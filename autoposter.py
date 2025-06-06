# -*- coding: utf-8 -*-
import time
import random
import json
import sys
import os
import logging
import signal
import traceback
from datetime import datetime, timedelta, time as dtime
from logging.handlers import RotatingFileHandler
from utils import (
    generate_post_from_theme, load_themes, add_publication_history,
    publish_to_wordpress, publish_to_telegram
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
DB_PATH = os.path.join(BASE_DIR, 'autoposter.db')
THEME_FILE = os.path.join(BASE_DIR, 'theme_host.json')
STOP_FILE = os.path.join(BASE_DIR, 'autoposter.stop')
RESTART_FILE = os.path.join(BASE_DIR, 'autoposter.restart')
HEALTH_FILE = os.path.join(BASE_DIR, 'autoposter.health')
# Файлы команд для управления ботом во время работы
PUBLISH_NOW_FILE = os.path.join(BASE_DIR, 'autoposter.publish_now')
STATUS_FILE = os.path.join(BASE_DIR, 'autoposter.status')
RESET_TODAY_FILE = os.path.join(BASE_DIR, 'autoposter.reset_today')

# Дефолтные значения (используются если нет в config.json)
DEFAULT_PUBLISHING_CONFIG = {
    "posts_per_day": 3,
    "publish_window": [8, 20],
    "interval_min": 1800,
    "interval_max": 10800,
    "post_delay": 60,
    "cycle_restart_delay": 60,
    "max_retries": 3,
    "retry_delay": 300
}

DEFAULT_LOGGING_CONFIG = {
    "max_file_size": 10485760,  # 10MB
    "backup_count": 5,
    "encoding": "utf-8"
}

DEFAULT_SYSTEM_CONFIG = {
    "check_interval": 60,
    "image_base_path": "./img",
    "health_check_interval": 300,
    "circuit_breaker_threshold": 5,
    "circuit_breaker_timeout": 1800
}

# Глобальные переменные для конфигурации (будут загружены из config.json)
POSTS_PER_DAY = DEFAULT_PUBLISHING_CONFIG["posts_per_day"]
PUBLISH_WINDOW = DEFAULT_PUBLISHING_CONFIG["publish_window"]
INTERVAL_MIN = DEFAULT_PUBLISHING_CONFIG["interval_min"]
INTERVAL_MAX = DEFAULT_PUBLISHING_CONFIG["interval_max"]
POST_DELAY = DEFAULT_PUBLISHING_CONFIG["post_delay"]
CYCLE_RESTART_DELAY = DEFAULT_PUBLISHING_CONFIG["cycle_restart_delay"]
MAX_RETRIES = DEFAULT_PUBLISHING_CONFIG["max_retries"]
RETRY_DELAY = DEFAULT_PUBLISHING_CONFIG["retry_delay"]
CHECK_INTERVAL = DEFAULT_SYSTEM_CONFIG["check_interval"]
HEALTH_CHECK_INTERVAL = DEFAULT_SYSTEM_CONFIG["health_check_interval"]
CIRCUIT_BREAKER_THRESHOLD = DEFAULT_SYSTEM_CONFIG["circuit_breaker_threshold"]
CIRCUIT_BREAKER_TIMEOUT = DEFAULT_SYSTEM_CONFIG["circuit_breaker_timeout"]

# IMG_BASE_PATH будет установлен в load_config_settings()
IMG_BASE_PATH = os.path.join(BASE_DIR, 'img')

# Глобальные переменные для circuit breaker
WORDPRESS_FAILURES = 0
WORDPRESS_CIRCUIT_OPEN_TIME = None
TELEGRAM_FAILURES = 0
TELEGRAM_CIRCUIT_OPEN_TIME = None

# Флаг для graceful shutdown
SHUTDOWN_REQUESTED = False

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    global SHUTDOWN_REQUESTED
    log_print("🛑 Получен сигнал завершения. Инициируется graceful shutdown...", 'warning')
    SHUTDOWN_REQUESTED = True

# Регистрируем обработчики сигналов
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def setup_logging():
    """
    Настраивает систему логирования для бота
    """
    # Создаем директорию для логов если её нет
    logs_dir = os.path.join(BASE_DIR, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Основной лог файл
    log_file = os.path.join(logs_dir, 'autoposter.log')
    
    # Пытаемся загрузить настройки логирования из конфига
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logging_config = config.get('logging', DEFAULT_LOGGING_CONFIG)
    except:
        logging_config = DEFAULT_LOGGING_CONFIG
    
    # Настраиваем ротацию логов с настройками из конфига
    handler = RotatingFileHandler(
        log_file, 
        maxBytes=logging_config.get("max_file_size", DEFAULT_LOGGING_CONFIG["max_file_size"]),
        backupCount=logging_config.get("backup_count", DEFAULT_LOGGING_CONFIG["backup_count"]),
        encoding=logging_config.get("encoding", DEFAULT_LOGGING_CONFIG["encoding"])
    )
    
    # Формат лога с временной меткой
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Настраиваем логгер
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    # Также выводим в консоль (для nohup.out)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def log_print(message, level='info'):
    """
    Функция для логирования и вывода сообщений
    
    Args:
        message: текст сообщения
        level: уровень логирования ('info', 'warning', 'error', 'debug')
    """
    # Обычный print для совместимости
    print(message)
    
    # Логирование в файл
    if hasattr(log_print, 'logger'):
        if level == 'error':
            log_print.logger.error(message)
        elif level == 'warning':
            log_print.logger.warning(message)
        elif level == 'debug':
            log_print.logger.debug(message)
        else:
            log_print.logger.info(message)

# Инициализируем логгер при загрузке модуля
try:
    log_print.logger = setup_logging()
    log_print("📊 Система логирования инициализирована")
    log_path = os.path.join(BASE_DIR, 'logs', 'autoposter.log')
    log_print("📁 Логи сохраняются в: " + log_path)
except Exception as e:
    print("❌ Ошибка инициализации логирования: " + str(e))
    # Создаем заглушку если логирование не работает
    log_print.logger = None

def check_files():
    """
    Проверяет наличие необходимых файлов и директорий, создает их при необходимости
    """
    # Проверяем и создаем необходимые директории
    required_dirs = [
        (os.path.join(BASE_DIR, 'logs'), "логов"),
        (IMG_BASE_PATH, "изображений")
    ]
    
    for dir_path, dir_desc in required_dirs:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                print("📁 Создана папка " + dir_desc + ": " + dir_path)
            except Exception as e:
                print("❌ Ошибка создания папки " + dir_desc + ": " + str(e))
                # Продолжаем работу, так как это не критично
    
    # Проверяем наличие обязательных файлов
    for path in [CONFIG_PATH, THEME_FILE]:
        if not os.path.exists(path):
            print("❌ Ошибка: отсутствует обязательный файл " + path)
            if path == CONFIG_PATH:
                print('💡 Создайте config.json на основе config.json.example')
            elif path == THEME_FILE:
                print('💡 Убедитесь, что файл theme_host.json находится в корневой папке проекта')
            sys.exit(1)

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_config_settings():
    """
    Загружает настройки из config.json и обновляет глобальные переменные
    
    Returns:
        dict: Полная конфигурация
    """
    global POSTS_PER_DAY, PUBLISH_WINDOW, INTERVAL_MIN, INTERVAL_MAX
    global POST_DELAY, CYCLE_RESTART_DELAY, CHECK_INTERVAL, IMG_BASE_PATH
    global MAX_RETRIES, RETRY_DELAY, HEALTH_CHECK_INTERVAL
    global CIRCUIT_BREAKER_THRESHOLD, CIRCUIT_BREAKER_TIMEOUT
    
    try:
        config = load_config()
        
        # Загружаем настройки публикации
        publishing_config = config.get('publishing', {})
        POSTS_PER_DAY = publishing_config.get('posts_per_day', DEFAULT_PUBLISHING_CONFIG['posts_per_day'])
        PUBLISH_WINDOW = tuple(publishing_config.get('publish_window', DEFAULT_PUBLISHING_CONFIG['publish_window']))
        INTERVAL_MIN = publishing_config.get('interval_min', DEFAULT_PUBLISHING_CONFIG['interval_min'])
        INTERVAL_MAX = publishing_config.get('interval_max', DEFAULT_PUBLISHING_CONFIG['interval_max'])
        POST_DELAY = publishing_config.get('post_delay', DEFAULT_PUBLISHING_CONFIG['post_delay'])
        CYCLE_RESTART_DELAY = publishing_config.get('cycle_restart_delay', DEFAULT_PUBLISHING_CONFIG['cycle_restart_delay'])
        MAX_RETRIES = publishing_config.get('max_retries', DEFAULT_PUBLISHING_CONFIG['max_retries'])
        RETRY_DELAY = publishing_config.get('retry_delay', DEFAULT_PUBLISHING_CONFIG['retry_delay'])
        
        # Загружаем системные настройки
        system_config = config.get('system', {})
        CHECK_INTERVAL = system_config.get('check_interval', DEFAULT_SYSTEM_CONFIG['check_interval'])
        HEALTH_CHECK_INTERVAL = system_config.get('health_check_interval', DEFAULT_SYSTEM_CONFIG['health_check_interval'])
        CIRCUIT_BREAKER_THRESHOLD = system_config.get('circuit_breaker_threshold', DEFAULT_SYSTEM_CONFIG['circuit_breaker_threshold'])
        CIRCUIT_BREAKER_TIMEOUT = system_config.get('circuit_breaker_timeout', DEFAULT_SYSTEM_CONFIG['circuit_breaker_timeout'])
        
        # Настройка пути к изображениям
        img_path = system_config.get('image_base_path', DEFAULT_SYSTEM_CONFIG['image_base_path'])
        if img_path.startswith('./'):
            IMG_BASE_PATH = os.path.join(BASE_DIR, img_path[2:])
        elif img_path.startswith('/'):
            IMG_BASE_PATH = img_path
        else:
            IMG_BASE_PATH = os.path.join(BASE_DIR, img_path)
        
        log_print("📝 Настройки загружены из config.json:")
        log_print("   • Постов в день: " + str(POSTS_PER_DAY))
        log_print("   • Окно публикации: " + str(PUBLISH_WINDOW[0]).zfill(2) + ":00 - " + str(PUBLISH_WINDOW[1]).zfill(2) + ":00")
        log_print("   • Интервал между постами: " + str(INTERVAL_MIN//60) + "-" + str(INTERVAL_MAX//60) + " мин")
        log_print("   • Задержка после поста: " + str(POST_DELAY) + " сек")
        log_print("   • Интервал проверки команд: " + str(CHECK_INTERVAL) + " сек")
        log_print("   • Максимум повторов: " + str(MAX_RETRIES))
        log_print("   • Интервал health check: " + str(HEALTH_CHECK_INTERVAL) + " сек")
        log_print("   • Путь к изображениям: " + IMG_BASE_PATH)
        
        return config
        
    except Exception as e:
        log_print("⚠️ Ошибка загрузки настроек из config.json: " + str(e), 'warning')
        log_print("🔄 Используются дефолтные значения", 'warning')
        return load_config()  # Возвращаем базовую конфигурацию

def get_published_today(db_path):
    from db_manager import DBManager
    db = DBManager(db_path)
    today = datetime.now().date().isoformat()
    recent = db.get_recent_publications(days=1)
    return set((row[0], row[1]) for row in recent if row[3][:10] == today)

def calculate_next_post_time():
    """
    Вычисляет время следующей публикации
    
    Returns:
        tuple: (next_post_datetime, description) - время следующего поста и описание
    """
    now = datetime.now()
    published_today = get_published_today(DB_PATH)
    posts_count_today = len(published_today)
    total_window_seconds = (PUBLISH_WINDOW[1] - PUBLISH_WINDOW[0]) * 3600
    if POSTS_PER_DAY > 1:
        interval_seconds = total_window_seconds // (POSTS_PER_DAY - 1)
    else:
        interval_seconds = total_window_seconds

    # Если достигнут лимит постов на сегодня
    if posts_count_today >= POSTS_PER_DAY:
        tomorrow = (now + timedelta(days=1)).replace(
            hour=PUBLISH_WINDOW[0], 
            minute=0, 
            second=0, 
            microsecond=0
        )
        return tomorrow, "завтра в " + str(PUBLISH_WINDOW[0]).zfill(2) + ":00 (лимит " + str(POSTS_PER_DAY) + " постов/день достигнут)"

    # Если сейчас время публикации
    if PUBLISH_WINDOW[0] <= now.hour < PUBLISH_WINDOW[1]:
        # Следующий пост в равномерном интервале
        first_post_time = now.replace(hour=PUBLISH_WINDOW[0], minute=0, second=0, microsecond=0)
        next_time = first_post_time + timedelta(seconds=interval_seconds * posts_count_today)
        if next_time <= now:
            next_time = now + timedelta(seconds=INTERVAL_MIN)
        # Проверяем, не выходит ли время за окно публикации
        if next_time.hour >= PUBLISH_WINDOW[1]:
            tomorrow = (now + timedelta(days=1)).replace(
                hour=PUBLISH_WINDOW[0], 
                minute=0, 
                second=0, 
                microsecond=0
            )
            return tomorrow, "завтра в " + str(PUBLISH_WINDOW[0]).zfill(2) + ":00 (выход за окно публикации)"
        # ИСПРАВЛЕНИЕ: Правильный расчёт разности времени
        time_diff = next_time - now
        total_seconds = time_diff.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        if hours > 0:
            time_desc = "через " + str(hours) + "ч " + str(minutes) + "мин"
        else:
            time_desc = "через " + str(minutes) + "мин"
        return next_time, time_desc

    # Если сейчас время вне окна публикации
    if now.hour < PUBLISH_WINDOW[0]:
        today_start = now.replace(
            hour=PUBLISH_WINDOW[0], 
            minute=0, 
            second=0, 
            microsecond=0
        )
        return today_start, "сегодня в " + str(PUBLISH_WINDOW[0]).zfill(2) + ":00"
    else:
        tomorrow = (now + timedelta(days=1)).replace(
            hour=PUBLISH_WINDOW[0], 
            minute=0, 
            second=0, 
            microsecond=0
        )
        return tomorrow, "завтра в " + str(PUBLISH_WINDOW[0]).zfill(2) + ":00"

def format_next_post_message():
    """
    Форматирует сообщение о времени следующей публикации
    
    Returns:
        str: Отформатированное сообщение
    """
    next_time, description = calculate_next_post_time()
    
    # Форматируем точное время
    time_str = next_time.strftime("%H:%M")
    date_str = next_time.strftime("%d.%m")
    
    published_today = get_published_today(DB_PATH)
    posts_count = len(published_today)
    
    return "⏰ Следующий пост: " + description + " (" + time_str + ", " + date_str + ") | Опубликовано сегодня: " + str(posts_count) + "/" + str(POSTS_PER_DAY)

def check_command_files():
    """
    Проверяет файлы команд и выполняет соответствующие действия
    
    Returns:
        bool: True если нужно остановить бота, False - продолжить
    """
    # Проверяем команду остановки
    if os.path.exists(STOP_FILE):
        print('🛑 Обнаружен файл остановки. Бот завершает работу.')
        os.remove(STOP_FILE)
        return True
    
    # Проверяем команду принудительной публикации
    if os.path.exists(PUBLISH_NOW_FILE):
        print('📢 Обнаружена команда принудительной публикации.')
        try:
            force_publish()
            print('✅ Принудительная публикация выполнена.')
        except Exception as e:
            print('❌ Ошибка при принудительной публикации: ' + str(e))
        finally:
            os.remove(PUBLISH_NOW_FILE)
    
    # Проверяем команду статуса
    if os.path.exists(STATUS_FILE):
        print('📊 Обнаружена команда статуса.')
        try:
            print_status()
        except Exception as e:
            print('❌ Ошибка при выводе статуса: ' + str(e))
        finally:
            os.remove(STATUS_FILE)
    
    # Проверяем команду сброса
    if os.path.exists(RESET_TODAY_FILE):
        print('🔄 Обнаружена команда сброса данных за сегодня.')
        try:
            reset_today()
            print('✅ История публикаций за сегодня сброшена.')
        except Exception as e:
            print('❌ Ошибка при сбросе: ' + str(e))
        finally:
            os.remove(RESET_TODAY_FILE)
    
    return False

def force_publish():
    """
    Принудительно публикует следующую статью, игнорируя временные ограничения
    """
    try:
        config = load_config_settings()  # Загружаем настройки в глобальные переменные
        themes = load_themes(THEME_FILE)
        published_today = get_published_today(DB_PATH)
        
        log_print("🔄 Принудительная публикация запущена...")
        
        post = generate_post_from_theme(themes, published_today, config['gpt'], config['telegram'], img_base_path=IMG_BASE_PATH)
        if post:
            log_print("📋 Генерируем принудительную публикацию: " + post['brand'] + " - " + post['title'][:50] + "...")
            
            # Публикация в WordPress
            try:
                publish_to_wordpress(post, config['wordpress'])
                add_publication_history(DB_PATH, post['brand'], post['original_topic'], 'wordpress', 'success')
                log_print('✅ WordPress: ' + post["brand"] + ' — ' + post["title"][:50] + "...")
            except Exception as e:
                error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
                log_print("❌ Ошибка публикации в WordPress: " + error_msg, 'error')
                add_publication_history(DB_PATH, post['brand'], post['original_topic'], 'wordpress', 'error: ' + str(e)[:200])
            
            # Публикация в Telegram
            try:
                publish_to_telegram(post, config['telegram'])
                add_publication_history(DB_PATH, post['brand'], post['original_topic'], 'telegram', 'success')
                log_print('✅ Telegram: опубликовано')
            except Exception as e:
                error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
                log_print("❌ Ошибка публикации в Telegram: " + error_msg, 'error')
                add_publication_history(DB_PATH, post['brand'], post['original_topic'], 'telegram', 'error: ' + str(e)[:200])
            
            log_print("📝 Принудительно опубликовано: " + post['brand'] + " — " + post['title'][:50] + "...")
            log_print(format_next_post_message())
        else:
            log_print("⚠️ Нет новых тем для публикации. Все темы из файла уже опубликованы сегодня.", 'warning')
    except Exception as e:
        log_print("❌ Критическая ошибка при принудительной публикации: " + str(e), 'error')
        raise

def publish_one():
    """
    Публикует одну статью и завершает работу
    """
    try:
        check_files()
        config = load_config_settings()  # Загружаем настройки в глобальные переменные
        themes = load_themes(THEME_FILE)
        
        log_print("📋 Разовая публикация запущена...")
        
        # Используем конфигурацию telegram непосредственно из config.json
        published_today = get_published_today(DB_PATH)
        post = generate_post_from_theme(themes, published_today, config['gpt'], config['telegram'], img_base_path=IMG_BASE_PATH)
        if post:
            log_print("📋 Генерируем разовую публикацию: " + post['brand'] + " - " + post['title'][:50] + "...")
            
            # Публикация в WordPress
            try:
                publish_to_wordpress(post, config['wordpress'])
                add_publication_history(DB_PATH, post['brand'], post['original_topic'], 'wordpress', 'success')
                log_print("✅ WordPress: опубликовано")
            except Exception as e:
                error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
                log_print("❌ Ошибка публикации в WordPress: " + error_msg, 'error')
                add_publication_history(DB_PATH, post['brand'], post['original_topic'], 'wordpress', 'error: ' + str(e)[:200])
            
            # Публикация в Telegram
            try:
                publish_to_telegram(post, config['telegram'])
                add_publication_history(DB_PATH, post['brand'], post['original_topic'], 'telegram', 'success')
                log_print("✅ Telegram: опубликовано")
            except Exception as e:
                error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
                log_print("❌ Ошибка публикации в Telegram: " + error_msg, 'error')
                add_publication_history(DB_PATH, post['brand'], post['original_topic'], 'telegram', 'error: ' + str(e)[:200])
            
            log_print("📝 Опубликовано: " + post['brand'] + " — " + post['title'][:50] + "...")
            log_print(format_next_post_message())
        else:
            log_print("⚠️ Нет новых тем для публикации. Все темы из файла уже опубликованы сегодня.", 'warning')
    except Exception as e:
        log_print("❌ Критическая ошибка при разовой публикации: " + str(e), 'error')
        raise

def print_status():
    published_today = get_published_today(DB_PATH)
    print("📊 Сегодня опубликовано: " + str(len(published_today)) + "/" + str(POSTS_PER_DAY))
    for brand, title in published_today:
        print("   • " + brand + ": " + title)
    print(format_next_post_message())

def reset_today():
    from db_manager import DBManager
    db = DBManager(DB_PATH)
    today = datetime.now().date().isoformat()
    c = db.conn.cursor()
    c.execute('DELETE FROM publication_history WHERE published_at LIKE ?', (today + '%',))
    db.conn.commit()
    print('🔄 История публикаций за сегодня сброшена.')
    print(format_next_post_message())

def get_today_slots():
    """
    Возвращает список времён публикаций (datetime.time) для текущего дня
    """
    slots = []
    start, end = PUBLISH_WINDOW
    total_seconds = (end - start) * 3600
    if POSTS_PER_DAY == 1:
        slots = [dtime(hour=start, minute=0)]
    else:
        interval = total_seconds // (POSTS_PER_DAY - 1)
        for i in range(POSTS_PER_DAY):
            slot_seconds = start * 3600 + interval * i
            slot_hour = slot_seconds // 3600
            slot_minute = (slot_seconds % 3600) // 60
            slots.append(dtime(hour=int(slot_hour), minute=int(slot_minute)))
    return slots

def main_loop():
    """
    Основной цикл работы автопостера с обработкой критических ошибок
    """
    global SHUTDOWN_REQUESTED
    last_health_check = 0
    
    try:
        check_files()
        config = load_config_settings()  # Загружаем настройки в глобальные переменные
        themes = load_themes(THEME_FILE)
        log_print('🤖 Бот запущен в режиме автопостинга.')
        log_print('📅 Окно публикации: ' + str(PUBLISH_WINDOW[0]).zfill(2) + ':00 - ' + str(PUBLISH_WINDOW[1]).zfill(2) + ':00')
        log_print('📊 Постов в день: ' + str(POSTS_PER_DAY))
        log_print('⏱️ Интервал: ' + str(INTERVAL_MIN//60) + '-' + str(INTERVAL_MAX//60) + ' минут')
        log_print('🔄 Retry логика: ' + str(MAX_RETRIES) + ' повторов с таймаутом ' + str(RETRY_DELAY) + 'с')
        log_print('⚡ Circuit breaker: ' + str(CIRCUIT_BREAKER_THRESHOLD) + ' ошибок за ' + str(CIRCUIT_BREAKER_TIMEOUT) + 'с')
        log_print('📁 Для управления используйте команды или создайте файлы:')
        log_print('   • autoposter.stop - остановить бота')
        log_print('   • autoposter.restart - перезапустить бота')
        log_print('   • autoposter.publish_now - принудительно опубликовать статью')
        log_print('   • autoposter.status - показать статус')
        log_print('   • autoposter.reset_today - сбросить счетчик за сегодня')
        log_print('---')
        log_print(format_next_post_message())
        log_print('---')
        
        # Первый health check
        write_health_check()
        
    except Exception as e:
        log_print("❌ Критическая ошибка при инициализации: " + str(e), 'error')
        log_print("🔍 Полный traceback:", 'error')
        log_print(traceback.format_exc(), 'error')
        log_print("🔍 Проверьте файлы config.json и theme_host.json", 'error')
        return

    while not SHUTDOWN_REQUESTED:
        try:
            # Проверяем команды управления
            if check_command_files():
                break
                
            # Проверяем запрос на restart
            if os.path.exists(RESTART_FILE):
                log_print("🔄 Обнаружен запрос на restart. Выходим для перезапуска...", 'warning')
                os.remove(RESTART_FILE)
                break
            
            # Health check
            current_time = time.time()
            if current_time - last_health_check > HEALTH_CHECK_INTERVAL:
                write_health_check()
                last_health_check = current_time
            
            now = datetime.now()
            today = now.date()
            slots = get_today_slots()
            published_today = get_published_today(DB_PATH)
            published_count = len(published_today)
            
            # 1. Догоняющие публикации
            for i, slot in enumerate(slots):
                if SHUTDOWN_REQUESTED:
                    break
                    
                slot_dt = now.replace(hour=slot.hour, minute=slot.minute, second=0, microsecond=0)
                if slot_dt < now and published_count <= i:
                    try:
                        post = generate_post_from_theme(themes, published_today, config['gpt'], config['telegram'], img_base_path=IMG_BASE_PATH)
                        if post:
                            log_print("📋 Генерируем догоняющую публикацию: " + post['brand'] + " - " + post['title'][:50] + "...")
                            
                            # Используем новую систему retry
                            results = publish_with_retry(post, config)
                            
                            if results['wordpress'] or results['telegram']:
                                log_print("📝 Догоняющая публикация завершена: " + post['brand'] + " — " + post['title'][:50] + "...")
                                log_print(format_next_post_message())
                                
                                # ИСПРАВЛЕНИЕ: Перезагружаем данные из базы после публикации
                                published_today = get_published_today(DB_PATH)
                                published_count = len(published_today)
                                
                                if not SHUTDOWN_REQUESTED:
                                    time.sleep(POST_DELAY)  # Используем конфигурируемую задержку
                            else:
                                log_print("❌ Догоняющая публикация полностью неудачна", 'error')
                        else:
                            log_print("⚠️ Нет новых тем для публикации. Все темы из файла уже опубликованы сегодня.", 'warning')
                    except Exception as e:
                        log_print("❌ Критическая ошибка при генерации поста: " + str(e), 'error')
                        log_print("🔍 Traceback: " + traceback.format_exc(), 'error')
                        # Продолжаем работу, пропускаем этот пост
                        continue
            
            if SHUTDOWN_REQUESTED:
                break
            
            # 2. Ждём до следующего слота
            now = datetime.now()
            # ИСПРАВЛЕНИЕ: Перезагружаем актуальные данные перед проверкой следующего слота
            published_today = get_published_today(DB_PATH)
            published_count = len(published_today)
            
            for i, slot in enumerate(slots):
                if SHUTDOWN_REQUESTED:
                    break
                    
                slot_dt = now.replace(hour=slot.hour, minute=slot.minute, second=0, microsecond=0)
                if slot_dt > now and published_count <= i:
                    sleep_time = (slot_dt - now).total_seconds()
                    hours = int(sleep_time // 3600)
                    minutes = int((sleep_time % 3600) // 60)
                    log_print("💤 Ожидание до следующей публикации: " + str(hours) + "ч " + str(minutes) + "мин (" + str(slot.hour).zfill(2) + ":" + str(slot.minute).zfill(2) + ")")
                    
                    # Ожидание с проверкой shutdown
                    total_slept = 0
                    while total_slept < sleep_time and not SHUTDOWN_REQUESTED:
                        if check_command_files():
                            return
                        
                        # Health check во время ожидания
                        current_time = time.time()
                        if current_time - last_health_check > HEALTH_CHECK_INTERVAL:
                            write_health_check()
                            last_health_check = current_time
                        
                        chunk_sleep = min(CHECK_INTERVAL, sleep_time - total_slept)  # Используем конфигурируемый интервал
                        time.sleep(chunk_sleep)
                        total_slept += chunk_sleep
                    
                    if SHUTDOWN_REQUESTED:
                        break
                    
                    try:
                        # ИСПРАВЛЕНИЕ: Перезагружаем данные перед генерацией поста
                        published_today = get_published_today(DB_PATH)
                        post = generate_post_from_theme(themes, published_today, config['gpt'], config['telegram'], img_base_path=IMG_BASE_PATH)
                        if post:
                            log_print("📋 Генерируем плановую публикацию: " + post['brand'] + " - " + post['title'][:50] + "...")
                            
                            # Используем новую систему retry
                            results = publish_with_retry(post, config)
                            
                            if results['wordpress'] or results['telegram']:
                                log_print("📝 Автоматически опубликовано: " + post['brand'] + " — " + post['title'][:50] + "...")
                                log_print(format_next_post_message())
                                
                                # ИСПРАВЛЕНИЕ: Перезагружаем данные из базы после публикации
                                published_today = get_published_today(DB_PATH)
                                published_count = len(published_today)
                            else:
                                log_print("❌ Плановая публикация полностью неудачна", 'error')
                        else:
                            log_print("⚠️ Нет новых тем для публикации. Все темы из файла уже опубликованы сегодня.", 'warning')
                    except Exception as e:
                        log_print("❌ Критическая ошибка при генерации планового поста: " + str(e), 'error')
                        log_print("🔍 Traceback: " + traceback.format_exc(), 'error')
                        # Продолжаем работу, пропускаем этот пост
                        continue
            
            if SHUTDOWN_REQUESTED:
                break
            
            # 3. Если все слоты прошли — ждём до первого слота завтра
            # ИСПРАВЛЕНИЕ: Финальная проверка - действительно ли все публикации выполнены
            published_today = get_published_today(DB_PATH)
            published_count = len(published_today)
            
            if published_count >= POSTS_PER_DAY:
                now = datetime.now()
                first_slot_tomorrow = (now + timedelta(days=1)).replace(hour=slots[0].hour, minute=slots[0].minute, second=0, microsecond=0)
                sleep_time = (first_slot_tomorrow - now).total_seconds()
                hours = int(sleep_time // 3600)
                minutes = int((sleep_time % 3600) // 60)
                log_print("💤 Все слоты на сегодня завершены. Ожидание до завтра: " + str(hours) + "ч " + str(minutes) + "мин (" + str(slots[0].hour).zfill(2) + ":" + str(slots[0].minute).zfill(2) + ")")
                
                # Ожидание с проверкой shutdown
                total_slept = 0
                while total_slept < sleep_time and not SHUTDOWN_REQUESTED:
                    if check_command_files():
                        return
                    
                    # Health check во время длительного ожидания
                    current_time = time.time()
                    if current_time - last_health_check > HEALTH_CHECK_INTERVAL:
                        write_health_check()
                        last_health_check = current_time
                    
                    chunk_sleep = min(CHECK_INTERVAL, sleep_time - total_slept)  # Используем конфигурируемый интервал
                    time.sleep(chunk_sleep)
                    total_slept += chunk_sleep
            else:
                # Если ещё есть неопубликованные слоты - продолжаем цикл
                log_print("🔄 Проверяем оставшиеся слоты для публикации...")
                if not SHUTDOWN_REQUESTED:
                    time.sleep(CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            log_print("🛑 Получен сигнал остановки (Ctrl+C). Завершение работы...", 'warning')
            SHUTDOWN_REQUESTED = True
            break
        except Exception as e:
            log_print("❌ Неожиданная ошибка в основном цикле: " + str(e), 'error')
            log_print("🔍 Полный traceback:", 'error')
            log_print(traceback.format_exc(), 'error')
            log_print("🔄 Пауза " + str(CYCLE_RESTART_DELAY) + " секунд перед перезапуском цикла...", 'warning')
            
            if not SHUTDOWN_REQUESTED:
                time.sleep(CYCLE_RESTART_DELAY)  # Используем конфигурируемую задержку
                continue
            else:
                break

    # Graceful shutdown
    log_print("🏁 Автопостер завершает работу...", 'info')
    try:
        # Обновляем health check со статусом остановки
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "status": "stopped",
            "pid": os.getpid(),
            "shutdown_reason": "graceful"
        }
        with open(HEALTH_FILE, 'w', encoding='utf-8') as f:
            json.dump(health_data, f, indent=2)
    except:
        pass
    
    log_print("🏁 Автопостер завершил работу")

def stop_bot():
    with open(STOP_FILE, 'w', encoding='utf-8') as f:
        f.write('stop')
    print('🛑 Файл остановки создан. Бот завершит работу в ближайшее время.')

def publish_now_command():
    """Создает файл команды для принудительной публикации"""
    with open(PUBLISH_NOW_FILE, 'w', encoding='utf-8') as f:
        f.write('publish_now')
    print('📢 Команда принудительной публикации отправлена боту.')

def status_command():
    """Создает файл команды для получения статуса"""
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        f.write('status')
    print('📊 Команда получения статуса отправлена боту.')

def reset_today_command():
    """Создает файл команды для сброса данных за сегодня"""
    with open(RESET_TODAY_FILE, 'w', encoding='utf-8') as f:
        f.write('reset_today')
    print('🔄 Команда сброса данных за сегодня отправлена боту.')

def help_message():
    print('''
🤖 Доступные команды AutoPoster:

Основные команды:
  start         — запустить бота в режиме публикации по расписанию
  stop          — остановить бота (создаёт файл autoposter.stop)
  once          — опубликовать одну статью и завершить работу
  next          — опубликовать следующую тему вручную (аналог once)
  status        — вывести статистику публикаций за сегодня
  reset_today   — сбросить историю публикаций за сегодня
  help          — показать это сообщение

Команды управления работающим ботом:
  publish_now   — принудительно опубликовать статью (игнорирует расписание)
  bot_status    — запросить статус у работающего бота
  bot_reset     — сбросить счетчик публикаций у работающего бота

📁 Альтернативный способ - создание файлов команд:
  • autoposter.stop - остановить бота
  • autoposter.publish_now - принудительно опубликовать
  • autoposter.status - показать статус
  • autoposter.reset_today - сбросить счетчик

Примеры использования:
  python autoposter.py start          # Запуск бота
  python autoposter.py publish_now    # Принудительная публикация
  python autoposter.py stop          # Остановка бота
''')

def write_health_check():
    """Записывает файл health check с текущим временем и статусом"""
    try:
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "status": "running",
            "pid": os.getpid(),
            "published_today": len(get_published_today(DB_PATH)),
            "posts_per_day": POSTS_PER_DAY,
            "wordpress_failures": WORDPRESS_FAILURES,
            "telegram_failures": TELEGRAM_FAILURES
        }
        with open(HEALTH_FILE, 'w', encoding='utf-8') as f:
            json.dump(health_data, f, indent=2)
    except Exception as e:
        log_print("⚠️ Ошибка записи health check: " + str(e), 'warning')

def is_circuit_breaker_open(service_name):
    """Проверяет, открыт ли circuit breaker для сервиса"""
    global WORDPRESS_FAILURES, WORDPRESS_CIRCUIT_OPEN_TIME
    global TELEGRAM_FAILURES, TELEGRAM_CIRCUIT_OPEN_TIME
    
    now = time.time()
    
    if service_name == 'wordpress':
        if WORDPRESS_FAILURES >= CIRCUIT_BREAKER_THRESHOLD:
            if WORDPRESS_CIRCUIT_OPEN_TIME is None:
                WORDPRESS_CIRCUIT_OPEN_TIME = now
                log_print("⚡ Circuit breaker ОТКРЫТ для WordPress", 'warning')
                return True
            elif now - WORDPRESS_CIRCUIT_OPEN_TIME < CIRCUIT_BREAKER_TIMEOUT:
                return True
            else:
                log_print("🔄 Circuit breaker сброшен для WordPress", 'info')
                WORDPRESS_FAILURES = 0
                WORDPRESS_CIRCUIT_OPEN_TIME = None
                return False
    elif service_name == 'telegram':
        if TELEGRAM_FAILURES >= CIRCUIT_BREAKER_THRESHOLD:
            if TELEGRAM_CIRCUIT_OPEN_TIME is None:
                TELEGRAM_CIRCUIT_OPEN_TIME = now
                log_print("⚡ Circuit breaker ОТКРЫТ для Telegram", 'warning')
                return True
            elif now - TELEGRAM_CIRCUIT_OPEN_TIME < CIRCUIT_BREAKER_TIMEOUT:
                return True
            else:
                log_print("🔄 Circuit breaker сброшен для Telegram", 'info')
                TELEGRAM_FAILURES = 0
                TELEGRAM_CIRCUIT_OPEN_TIME = None
                return False
    
    return False

def record_service_failure(service_name):
    """Записывает ошибку сервиса для circuit breaker"""
    global WORDPRESS_FAILURES, TELEGRAM_FAILURES
    
    if service_name == 'wordpress':
        WORDPRESS_FAILURES += 1
        log_print(f"📊 WordPress ошибки: {WORDPRESS_FAILURES}/{CIRCUIT_BREAKER_THRESHOLD}", 'warning')
    elif service_name == 'telegram':
        TELEGRAM_FAILURES += 1
        log_print(f"📊 Telegram ошибки: {TELEGRAM_FAILURES}/{CIRCUIT_BREAKER_THRESHOLD}", 'warning')

def record_service_success(service_name):
    """Записывает успешную операцию сервиса"""
    global WORDPRESS_FAILURES, TELEGRAM_FAILURES
    
    if service_name == 'wordpress':
        WORDPRESS_FAILURES = max(0, WORDPRESS_FAILURES - 1)
    elif service_name == 'telegram':
        TELEGRAM_FAILURES = max(0, TELEGRAM_FAILURES - 1)

def publish_with_retry(post, config, max_retries=None):
    """
    Публикует пост с retry логикой и circuit breaker
    
    Returns:
        dict: результат публикации {'wordpress': bool, 'telegram': bool}
    """
    if max_retries is None:
        max_retries = MAX_RETRIES
    
    results = {'wordpress': False, 'telegram': False}
    
    # Публикация в WordPress с retry
    if not is_circuit_breaker_open('wordpress'):
        for attempt in range(max_retries + 1):
            try:
                publish_to_wordpress(post, config['wordpress'])
                add_publication_history(DB_PATH, post['brand'], post['original_topic'], 'wordpress', 'success')
                log_print("✅ WordPress: " + post['title'][:50] + "...")
                record_service_success('wordpress')
                results['wordpress'] = True
                break
            except Exception as e:
                record_service_failure('wordpress')
                error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
                
                if attempt < max_retries:
                    retry_delay = RETRY_DELAY * (attempt + 1)  # Экспоненциальная задержка
                    log_print(f"❌ WordPress попытка {attempt + 1}/{max_retries + 1} неудачна: {error_msg}", 'error')
                    log_print(f"🔄 Повтор через {retry_delay} секунд...", 'warning')
                    time.sleep(retry_delay)
                else:
                    log_print(f"❌ WordPress окончательная ошибка: {error_msg}", 'error')
                    add_publication_history(DB_PATH, post['brand'], post['original_topic'], 'wordpress', 'error: ' + str(e)[:200])
    else:
        log_print("⚡ WordPress недоступен (circuit breaker открыт)", 'warning')
        add_publication_history(DB_PATH, post['brand'], post['original_topic'], 'wordpress', 'error: circuit breaker open')
    
    # Публикация в Telegram с retry
    if not is_circuit_breaker_open('telegram'):
        for attempt in range(max_retries + 1):
            try:
                publish_to_telegram(post, config['telegram'])
                add_publication_history(DB_PATH, post['brand'], post['original_topic'], 'telegram', 'success')
                log_print("✅ Telegram: опубликовано")
                record_service_success('telegram')
                results['telegram'] = True
                break
            except Exception as e:
                record_service_failure('telegram')
                error_msg = str(e)[:100] + "..." if len(str(e)) > 100 else str(e)
                
                if attempt < max_retries:
                    retry_delay = RETRY_DELAY * (attempt + 1)  # Экспоненциальная задержка
                    log_print(f"❌ Telegram попытка {attempt + 1}/{max_retries + 1} неудачна: {error_msg}", 'error')
                    log_print(f"🔄 Повтор через {retry_delay} секунд...", 'warning')
                    time.sleep(retry_delay)
                else:
                    log_print(f"❌ Telegram окончательная ошибка: {error_msg}", 'error')
                    add_publication_history(DB_PATH, post['brand'], post['original_topic'], 'telegram', 'error: ' + str(e)[:200])
    else:
        log_print("⚡ Telegram недоступен (circuit breaker открыт)", 'warning')
        add_publication_history(DB_PATH, post['brand'], post['original_topic'], 'telegram', 'error: circuit breaker open')
    
    return results

if __name__ == '__main__':
    if len(sys.argv) == 1 or sys.argv[1] == 'start':
        main_loop()
    elif sys.argv[1] == 'stop':
        stop_bot()
    elif sys.argv[1] == 'once' or sys.argv[1] == 'next':
        publish_one()
    elif sys.argv[1] == 'status':
        print_status()
    elif sys.argv[1] == 'reset_today':
        reset_today()
    elif sys.argv[1] == 'publish_now':
        publish_now_command()
    elif sys.argv[1] == 'bot_status':
        status_command()
    elif sys.argv[1] == 'bot_reset':
        reset_today_command()
    elif sys.argv[1] == 'help':
        help_message()
    else:
        print('❌ Неизвестная команда. Используйте help для списка команд.') 