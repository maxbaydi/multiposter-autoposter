# AutoPoster - Автоматическая система публикации контента

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/maxbaydi/multiposter-autoposter)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

Система автоматической генерации и публикации статей с изображениями в WordPress и Telegram с использованием AI для создания контента.

## ✨ Возможности

- 🤖 **AI-генерация контента** - Автоматическое создание статей с помощью GPT
- 📝 **Публикация в WordPress** - Автоматическая публикация статей с изображениями
- 📱 **Отправка в Telegram** - Публикация в Telegram каналы и чаты
- 🖼️ **Обработка изображений** - Автоматическое добавление водяных знаков
- ⏰ **Планировщик** - Автоматическая публикация по расписанию
- 📊 **Логирование** - Подробные логи всех операций
- 🔄 **Система очередей** - Управление очередью публикаций

## 🚀 Быстрый старт

### Установка зависимостей

```bash
# Клонирование репозитория
git clone https://github.com/maxbaydi/multiposter-autoposter.git
cd multiposter-autoposter

# Основные зависимости
pip install -r requirements.txt

# Для разработки (включает инструменты тестирования и анализа)
pip install -r requirements-dev.txt
```

### Конфигурация

1. Скопируйте `config.json.example` в `config.json`
2. Заполните необходимые настройки:

```json
{
    "wordpress": {
        "url": "https://your-site.com",
        "user": "your_username",
        "password": "your_app_password",
        "category_id": 50,
        "timeout": 30
    },
    "telegram": {
        "token": "your_bot_token",
        "chat_id": "your_chat_id",
        "timeout": 30,
        "image_timeout": 60,
        "format": {
            "max_length": 800,
            "prefix": "🌐 GVN ",
            "suffix": "• More at GVN.biz •"
        }
    },
    "gpt": {
        "api_key": "your_api_key",
        "url": "https://api.vsegpt.ru/v1"
    },
    "publishing": {
        "posts_per_day": 3,
        "publish_window": [8, 20],
        "interval_min": 1800,
        "interval_max": 10800,
        "post_delay": 60,
        "skip_weekends": false
    },
    "watermark": {
        "image_path": "watermark_gvnbiz_2.png",
        "position": "bottom_right",
        "opacity": 0.7,
        "margin": 20
    },
    "image_processing": {
        "min_size": [800, 600],
        "max_size": [1920, 1080],
        "quality": 85,
        "format": "JPEG"
    }
}
```

### Запуск

```bash
# Проверка конфигурации
python check_db.py

# Запуск в режиме демона
python autoposter.py --daemon

# Запуск с логированием
python autoposter.py --verbose

# Запуск одного цикла публикации
python autoposter.py --once
```

## 📋 Системные требования

- Python 3.8+
- Библиотеки из requirements.txt
- Доступ к интернету для API вызовов
- Права на запись в директорию для логов и базы данных

## 🛠️ Архитектура

- `autoposter.py` - Основной модуль с логикой публикации
- `wordpress_client.py` - Клиент для работы с WordPress API
- `telegram_client.py` - Клиент для работы с Telegram Bot API
- `vsegpt_client.py` - Клиент для работы с GPT API
- `watermark.py` - Модуль обработки изображений и водяных знаков
- `db_manager.py` - Менеджер базы данных SQLite
- `utils.py` - Вспомогательные функции

## 🔧 Управление

### Systemd Service (Linux)

```bash
# Копирование service файла
sudo cp autoposter.service /etc/systemd/system/

# Включение автозапуска
sudo systemctl enable autoposter
sudo systemctl start autoposter

# Проверка статуса
sudo systemctl status autoposter
```

### Скрипты мониторинга

- `monitor_autoposter.sh` - Скрипт мониторинга и автозапуска
- `manage_logs.sh` - Управление лог-файлами
- `keepalive.sh` - Скрипт поддержания работоспособности

## 📖 Документация

- [CONFIGURATION.md](CONFIGURATION.md) - Детальная настройка
- [DEPLOYMENT.md](DEPLOYMENT.md) - Инструкции по развертыванию
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Решение проблем
- [TESTING.md](TESTING.md) - Тестирование системы

## 🐛 Устранение неполадок

### Общие проблемы

1. **Ошибки API**: Проверьте правильность токенов и ключей в config.json
2. **Проблемы с изображениями**: Убедитесь в наличии файла водяного знака
3. **Ошибки базы данных**: Проверьте права на запись в директории
4. **Проблемы с сетью**: Проверьте соединение с интернетом и доступность API

### Логи

Логи сохраняются в `logs/autoposter.log`. Для детального анализа используйте:

```bash
# Просмотр последних записей
tail -f logs/autoposter.log

# Поиск ошибок
grep ERROR logs/autoposter.log

# Анализ производительности
grep "Processing time" logs/autoposter.log
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения и добавьте тесты
4. Отправьте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

## 🔗 Полезные ссылки

- [WordPress REST API](https://developer.wordpress.org/rest-api/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [VseGPT API](https://api.vsegpt.ru/)

## 📞 Поддержка

Если у вас есть вопросы или проблемы, создайте [Issue](https://github.com/maxbaydi/multiposter-autoposter/issues) в GitHub.