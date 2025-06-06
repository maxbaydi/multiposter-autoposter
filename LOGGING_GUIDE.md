# 📊 Руководство по логированию AutoPoster

## 🔧 Настройка логирования

AutoPoster теперь имеет продвинутую систему логирования с автоматической ротацией файлов.

### 📁 Структура логов

```
autoposter/
├── logs/                    # Директория логов (создается автоматически)
│   ├── autoposter.log      # Основной файл логов  
│   ├── autoposter.log.1    # Архивный файл #1
│   ├── autoposter.log.2    # Архивный файл #2
│   └── ...                 # До 5 архивных файлов
├── nohup.out              # Лог nohup (дублирует основные логи)
└── manage_logs.sh         # Скрипт управления логами
```

### ⚙️ Параметры логирования

- **Максимальный размер файла:** 10MB
- **Количество архивных файлов:** 5  
- **Общий объем логов:** до 50MB
- **Кодировка:** UTF-8
- **Автоматическая ротация:** включена

## 🚀 Запуск бота на сервере

### 1. **Базовый запуск через nohup:**

```bash
# Переход в директорию бота
cd /path/to/autoposter

# Запуск с перенаправлением в отдельный лог-файл
nohup python autoposter.py start > autoposter_nohup.log 2>&1 &

# Получить PID процесса
echo $! > autoposter.pid
```

### 2. **Рекомендуемый запуск:**

```bash
# Через управляющий скрипт (Linux/Mac)
./manage_logs.sh start

# Или вручную с правильным перенаправлением
nohup python autoposter.py start > nohup.out 2>&1 &
```

### 3. **Проверка статуса:**

```bash
# Проверка процесса
ps aux | grep autoposter.py

# Через скрипт управления
./manage_logs.sh status

# Последняя активность
tail -n 1 logs/autoposter.log
```

## 📖 Просмотр логов

### 🔍 Базовые команды

```bash
# Последние 50 строк логов
tail -n 50 logs/autoposter.log

# Мониторинг в реальном времени
tail -f logs/autoposter.log

# Логи за сегодня
grep "$(date '+%Y-%m-%d')" logs/autoposter.log

# Только ошибки
grep -E "(ERROR|❌|Ошибка)" logs/autoposter.log
```

### 📊 Поиск и фильтрация

```bash
# Поиск по бренду
grep "Schneider Electric" logs/autoposter.log

# Публикации WordPress
grep "опубликован в WordPress" logs/autoposter.log

# Публикации Telegram  
grep "отправлено в Telegram" logs/autoposter.log

# Статистика публикаций
grep -c "Автоматически опубликовано" logs/autoposter.log
```

### 🕐 Поиск по времени

```bash
# Логи за конкретную дату
grep "2024-06-02" logs/autoposter.log

# Логи за последний час
grep "$(date '+%Y-%m-%d %H')" logs/autoposter.log

# Активность в определенное время
grep "14:30" logs/autoposter.log
```

## 🛠️ Использование скрипта manage_logs.sh

### 📊 Просмотр логов

```bash
# Последние записи
./manage_logs.sh tail

# Мониторинг в реальном времени
./manage_logs.sh follow

# Логи за сегодня
./manage_logs.sh today

# Только ошибки
./manage_logs.sh errors

# Статистика публикаций
./manage_logs.sh stats
```

### 🔍 Поиск в логах

```bash
# Поиск по тексту
./manage_logs.sh search "Schneider Electric"

# Все публикации
./manage_logs.sh posts

# Публикации WordPress
./manage_logs.sh wordpress

# Публикации Telegram
./manage_logs.sh telegram
```

### 🤖 Управление ботом

```bash
# Запуск бота
./manage_logs.sh start

# Остановка бота
./manage_logs.sh stop

# Статус бота
./manage_logs.sh status

# Перезапуск бота
./manage_logs.sh restart
```

### 🧹 Управление логами

```bash
# Размер файлов логов
./manage_logs.sh size

# Очистка старых логов (>7 дней)
./manage_logs.sh clean

# Информация о ротации
./manage_logs.sh rotate
```

## 🐛 Мониторинг ошибок

### 🚨 Быстрая диагностика

```bash
# Последние ошибки
tail -n 100 logs/autoposter.log | grep -E "(ERROR|❌)"

# Ошибки за сегодня
grep "$(date '+%Y-%m-%d')" logs/autoposter.log | grep -E "(ERROR|❌)"

# Проблемы с публикацией
grep "Ошибка публикации" logs/autoposter.log

# Проблемы с подключением
grep -E "(ConnectionError|TimeoutError)" logs/autoposter.log
```

### 📈 Анализ производительности

```bash
# Количество публикаций за день
grep "$(date '+%Y-%m-%d')" logs/autoposter.log | grep -c "Автоматически опубликовано"

# Время публикаций
grep "Автоматически опубликовано" logs/autoposter.log | cut -d' ' -f1,2

# Ошибки по типам
grep "ERROR" logs/autoposter.log | cut -d']' -f2 | sort | uniq -c
```

## 🔄 Ротация и архивирование

### 📦 Автоматическая ротация

Система автоматически:
- Создает новый файл когда текущий достигает 10MB
- Архивирует старые файлы (autoposter.log.1, .2, и т.д.)
- Удаляет файлы старше 5-го архива
- Сохраняет до 50MB логов общим объемом

### 🗂️ Ручное архивирование

```bash
# Архивирование за месяц
tar -czf logs_$(date '+%Y-%m').tar.gz logs/

# Очистка логов старше недели
find logs/ -name "*.log*" -mtime +7 -delete

# Создание резервной копии
cp logs/autoposter.log backup_$(date '+%Y%m%d_%H%M%S').log
```

## 🔧 Системные команды

### 📱 Управление процессом

```bash
# Найти PID процесса
pgrep -f "python.*autoposter.py"

# Завершить процесс
pkill -f "python.*autoposter.py"

# Мягкая остановка через файл
touch autoposter.stop

# Принудительная публикация
touch autoposter.publish_now

# Запрос статуса
touch autoposter.status
```

### 📊 Мониторинг ресурсов

```bash
# Использование памяти
ps -o pid,ppid,cmd,%mem,%cpu -p $(pgrep -f autoposter.py)

# Размер файлов логов
du -h logs/

# Свободное место на диске
df -h .
```

## 🚀 Автозапуск через systemd

### 📝 Создание сервиса

```bash
# Создать файл сервиса
sudo nano /etc/systemd/system/autoposter.service
```

```ini
[Unit]
Description=AutoPoster Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/autoposter
ExecStart=/usr/bin/python3 autoposter.py start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### ⚡ Управление сервисом

```bash
# Активировать и запустить
sudo systemctl enable autoposter
sudo systemctl start autoposter

# Проверить статус
sudo systemctl status autoposter

# Просмотр логов systemd
sudo journalctl -u autoposter -f

# Остановка и перезапуск
sudo systemctl stop autoposter
sudo systemctl restart autoposter
```

## 📞 Troubleshooting

### ❌ Частые проблемы

1. **Бот не запускается:**
   ```bash
   # Проверить конфигурацию
   python autoposter.py once
   
   # Проверить ошибки в логах
   tail -n 50 logs/autoposter.log
   ```

2. **Логи не создаются:**
   ```bash
   # Проверить права доступа
   ls -la logs/
   
   # Создать директорию
   mkdir -p logs
   chmod 755 logs
   ```

3. **Большой размер логов:**
   ```bash
   # Принудительная очистка
   > logs/autoposter.log
   
   # Архивирование
   gzip logs/autoposter.log.1
   ```

4. **Процесс завис:**
   ```bash
   # Мягкая остановка
   touch autoposter.stop
   
   # Принудительная остановка
   pkill -9 -f autoposter.py
   ```

### 🔍 Диагностические команды

```bash
# Полная диагностика
echo "=== СТАТУС БОТА ==="
ps aux | grep autoposter.py

echo "=== РАЗМЕР ЛОГОВ ==="
du -h logs/ nohup.out 2>/dev/null

echo "=== ПОСЛЕДНИЕ ЛОГИ ==="
tail -n 5 logs/autoposter.log

echo "=== ОШИБКИ ЗА СЕГОДНЯ ==="
grep "$(date '+%Y-%m-%d')" logs/autoposter.log | grep -c ERROR
```

## 📋 Чек-лист для деплоя

- [ ] Проверить наличие всех конфигурационных файлов
- [ ] Создать директорию logs с правильными правами
- [ ] Протестировать запуск в фоне через nohup
- [ ] Настроить мониторинг логов
- [ ] Проверить автоматическую ротацию
- [ ] Настроить автозапуск (systemd/cron)
- [ ] Создать скрипты мониторинга
- [ ] Настроить оповещения об ошибках

---

**💡 Совет:** Всегда используйте `tail -f` для мониторинга логов в реальном времени при первом запуске на сервере! 