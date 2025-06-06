# 🚀 Развертывание AutoPoster в продакшене

Руководство по настройке стабильной версии автопостера с автоматическим перезапуском и мониторингом.

## 🔧 Новые возможности

### ✅ Система стабильности:
- **Retry логика** - до 3 попыток публикации с экспоненциальной задержкой
- **Circuit Breaker** - защита от сбоев WordPress/Telegram API
- **Health Check** - мониторинг состояния каждые 5 минут
- **Graceful Shutdown** - корректное завершение процессов
- **Auto Restart** - автоматический перезапуск при сбоях

### 📊 Мониторинг:
- **KeepAlive скрипт** - следит за процессом autoposter 24/7
- **Health файл** - JSON со статусом и метриками
- **Детальное логирование** - полные traceback ошибок
- **Systemd сервис** - интеграция с системой управления

## 🛠️ Быстрая установка

### 1. Автоматическая установка:

```bash
# Обычная установка (с cron)
./setup_production.sh install

# Установка с systemd (требует root)
sudo ./setup_production.sh --with-systemd
```

### 2. Ручная установка:

```bash
# 1. Установка зависимостей
pip3 install -r requirements.txt

# 2. Создание директорий
mkdir -p logs img

# 3. Настройка keepalive
chmod +x keepalive.sh

# 4. Запуск с мониторингом
./keepalive.sh start
```

## 📋 Управление

### KeepAlive команды:
```bash
./keepalive.sh start     # Запуск с мониторингом
./keepalive.sh stop      # Остановка
./keepalive.sh restart   # Перезапуск
./keepalive.sh status    # Проверка статуса
```

### Autoposter команды:
```bash
python3 autoposter.py start         # Обычный запуск
python3 autoposter.py status        # Статус публикаций
python3 autoposter.py publish_now   # Принудительная публикация
python3 autoposter.py reset_today   # Сброс счетчика
```

### Systemd команды (если установлен):
```bash
systemctl start autoposter      # Запуск
systemctl stop autoposter       # Остановка
systemctl status autoposter     # Статус
systemctl restart autoposter    # Перезапуск
journalctl -u autoposter -f     # Просмотр логов
```

## 📊 Мониторинг

### Основные логи:
```bash
# Основные логи autoposter
tail -f logs/autoposter.log

# Логи keepalive скрипта
tail -f logs/keepalive.log

# Поиск ошибок
grep "ERROR\|❌" logs/autoposter.log

# Статистика публикаций
grep "опубликован" logs/autoposter.log | tail -10
```

### Health Check:
```bash
# Проверка статуса
cat autoposter.health

# Пример содержимого:
{
  "timestamp": "2025-01-06T10:30:45",
  "status": "running",
  "pid": 12345,
  "published_today": 2,
  "posts_per_day": 3,
  "wordpress_failures": 0,
  "telegram_failures": 0
}
```

### Метрики производительности:
```bash
# Процессы autoposter
ps aux | grep autoposter

# Использование памяти
free -h

# Место на диске
df -h

# Сетевые соединения
netstat -an | grep :443
```

## ⚙️ Конфигурация

### Новые настройки в config.json:

```json
{
  "publishing": {
    "max_retries": 3,          // Максимум попыток публикации
    "retry_delay": 300         // Базовая задержка между попытками (5 мин)
  },
  "system": {
    "health_check_interval": 300,        // Интервал health check (5 мин)
    "circuit_breaker_threshold": 5,      // Порог ошибок для circuit breaker
    "circuit_breaker_timeout": 1800      // Время блокировки сервиса (30 мин)
  }
}
```

### Настройка для хостинга:

1. **Увеличенные timeout'ы** - защита от медленных серверов
2. **Retry логика** - автоматические повторы при сбоях
3. **Circuit breaker** - защита от каскадных ошибок
4. **Health monitoring** - контроль состояния

## 🔍 Диагностика проблем

### Типичные проблемы и решения:

#### 1. Autoposter не запускается:
```bash
# Проверка конфигурации
python3 autoposter.py status

# Проверка зависимостей
pip3 list | grep -E "(requests|PIL|sqlite3)"

# Проверка прав доступа
ls -la autoposter.py keepalive.sh
```

#### 2. Публикации не работают:
```bash
# Проверка network доступа
curl -I https://www.gvn.biz/wp-json/wp/v2/
curl -I https://api.telegram.org/

# Проверка circuit breaker
grep "Circuit breaker" logs/autoposter.log

# Тест одиночной публикации
python3 autoposter.py once
```

#### 3. Высокая нагрузка:
```bash
# Проверка процессов
top -p $(pgrep -f autoposter)

# Анализ логов
grep "retry\|timeout\|error" logs/autoposter.log | tail -20

# Проверка health файла
watch -n 5 cat autoposter.health
```

### Экстренные команды:

```bash
# Полная остановка всех процессов
pkill -f autoposter
./keepalive.sh stop

# Сброс circuit breaker
python3 autoposter.py restart

# Принудительная очистка
rm -f autoposter.pid autoposter.health
rm -f autoposter.stop autoposter.restart
```

## 📈 Производительность

### Оптимизация для хостинга:

1. **Адаптивные интервалы** - автоматическая подстройка под нагрузку
2. **Эффективное использование ресурсов** - минимум памяти и CPU
3. **Сетевая оптимизация** - connection pooling и timeout management
4. **Disk I/O оптимизация** - ротация логов и cleanup

### Рекомендуемые настройки для VPS:

```json
{
  "publishing": {
    "posts_per_day": 3,
    "max_retries": 3,
    "retry_delay": 300
  },
  "system": {
    "check_interval": 60,
    "health_check_interval": 300,
    "circuit_breaker_threshold": 5
  }
}
```

## 🔒 Безопасность

### Настройки безопасности:

1. **Ограниченные права** - запуск от unprivileged пользователя
2. **Изолированная среда** - отдельная директория
3. **Защищенные конфиги** - ограниченный доступ к config.json
4. **Логирование действий** - полная аудитория операций

### Команды безопасности:

```bash
# Установка прав доступа
chmod 600 config.json
chmod 700 logs/
chmod 755 keepalive.sh autoposter.py

# Проверка процессов
ps aux | grep autoposter | grep -v grep
lsof -p $(pgrep -f autoposter)
```

## 📞 Поддержка

### Файлы для отправки при проблемах:

1. `logs/autoposter.log` (последние 100 строк)
2. `logs/keepalive.log` (последние 50 строк)
3. `autoposter.health` (current status)
4. `config.json` (без паролей!)

### Команды диагностики:

```bash
# Создание диагностического отчета
echo "=== AUTOPOSTER DIAGNOSTIC REPORT ===" > diagnostic.txt
echo "Date: $(date)" >> diagnostic.txt
echo "" >> diagnostic.txt

echo "=== PROCESS STATUS ===" >> diagnostic.txt
ps aux | grep autoposter >> diagnostic.txt
echo "" >> diagnostic.txt

echo "=== HEALTH CHECK ===" >> diagnostic.txt
cat autoposter.health >> diagnostic.txt
echo "" >> diagnostic.txt

echo "=== RECENT LOGS ===" >> diagnostic.txt
tail -50 logs/autoposter.log >> diagnostic.txt
echo "" >> diagnostic.txt

echo "=== RECENT ERRORS ===" >> diagnostic.txt
grep -i error logs/autoposter.log | tail -10 >> diagnostic.txt

echo "Diagnostic report created: diagnostic.txt"
```

---

**🎯 Результат**: Полностью автономный и стабильный autoposter, готовый к продуктивному использованию на любом хостинге! 