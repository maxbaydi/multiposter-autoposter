# 🔧 Устранение проблем AutoPoster

## 🚨 Часто встречающиеся проблемы

### 1. Нестабильность работы и частые перезапуски

**Признаки:**
- Система неожиданно завершается и перезапускается
- В логах появляются сигналы завершения (SIGTERM, SIGINT)
- Keepalive часто перезапускает процесс

**Диагностика:**
```bash
# Проверяем информацию о последнем завершении
cat last_shutdown.info

# Анализируем health check
./monitor_autoposter.sh health

# Проверяем системные ресурсы
./monitor_autoposter.sh system
```

**Решения:**
1. **Проверьте ресурсы системы:**
   ```bash
   df -h  # Место на диске
   free -h  # Память
   ps aux | grep python  # Процессы Python
   ```

2. **Увеличьте интервалы в конфигурации:**
   ```json
   {
     "system": {
       "check_interval": 120,
       "health_check_interval": 600
     }
   }
   ```

3. **Проверьте логи хостинга:**
   ```bash
   tail -f /var/log/messages
   dmesg | tail
   ```

### 2. Проблемы с планированием публикаций

**Признаки:**
- "Догоняющие публикации" в логах
- Сообщения "выход за окно публикации" при наличии свободных слотов
- Неравномерное распределение постов

**Диагностика:**
```bash
# Анализируем health check на предмет пропущенных слотов
./monitor_autoposter.sh health

# Проверяем debug логи планировщика
grep "🔍" logs/autoposter.log | tail -20
```

**Решения:**
1. **Включите debug логирование:**
   ```python
   # В autoposter.py измените уровень логирования
   logger.setLevel(logging.DEBUG)
   ```

2. **Проверьте конфигурацию окна публикаций:**
   ```json
   {
     "publishing": {
       "posts_per_day": 3,
       "publish_window": [8, 20],
       "interval_min": 1800,
       "interval_max": 10800
     }
   }
   ```

3. **Сбросьте данные за день для тестирования:**
   ```bash
   python autoposter.py reset_today
   ```

### 3. Ошибки публикации в WordPress/Telegram

**Признаки:**
- Circuit breaker активирован
- Многочисленные retry попытки
- Ошибки соединения или аутентификации

**Диагностика:**
```bash
# Проверяем статус circuit breaker
./monitor_autoposter.sh health

# Анализируем ошибки в логах
grep "ERROR" logs/autoposter.log | tail -10
```

**Решения:**
1. **Проверьте настройки соединения:**
   ```bash
   # Тест WordPress API
   curl -X GET "https://your-site.com/wp-json/wp/v2/posts" \
        -u "username:app-password"
   
   # Тест Telegram API
   curl "https://api.telegram.org/bot<TOKEN>/getMe"
   ```

2. **Увеличьте таймауты:**
   ```json
   {
     "wordpress": {
       "timeout": 60
     },
     "telegram": {
       "timeout": 60,
       "image_timeout": 120
     }
   }
   ```

3. **Настройте retry логику:**
   ```json
   {
     "publishing": {
       "max_retries": 5,
       "retry_delay": 600
     }
   }
   ```

### 4. Проблемы с изображениями

**Признаки:**
- Ошибки загрузки изображений
- Пустые посты без картинок
- Таймауты при работе с Telegram

**Решения:**
1. **Проверьте права доступа:**
   ```bash
   ls -la img/
   chmod -R 755 img/
   ```

2. **Проверьте размер изображений:**
   ```bash
   find img/ -name "*.jpg" -o -name "*.png" | xargs du -h | sort -hr
   ```

3. **Оптимизируйте изображения:**
   ```bash
   # Установите ImageMagick если нужно
   find img/ -name "*.jpg" -exec convert {} -resize 1200x1200> {} \;
   ```

## 🔍 Инструменты диагностики

### Новый скрипт мониторинга
```bash
# Сделайте скрипт исполняемым
chmod +x monitor_autoposter.sh

# Различные виды диагностики
./monitor_autoposter.sh status    # Краткий статус
./monitor_autoposter.sh health    # Анализ health check
./monitor_autoposter.sh logs      # Анализ логов
./monitor_autoposter.sh shutdown  # Анализ последнего завершения
./monitor_autoposter.sh system    # Проверка ресурсов
./monitor_autoposter.sh report    # Полный отчет
./monitor_autoposter.sh full      # Полная диагностика
```

### Анализ health check файла
```bash
# Если установлен jq
jq . autoposter.health

# Проверка пропущенных слотов
jq '.publishing.slots[] | select(.status == "missed")' autoposter.health

# Статистика circuit breaker
jq '.circuit_breaker' autoposter.health
```

### Мониторинг в реальном времени
```bash
# Следите за логами
tail -f logs/autoposter.log

# Мониторинг health check
watch -n 30 './monitor_autoposter.sh status'

# Проверка процессов
watch -n 10 'ps aux | grep autoposter'
```

## 📊 Профилактические меры

### 1. Регулярное обслуживание
```bash
# Еженедельная очистка старых логов
find logs/ -name "*.log.*" -mtime +7 -delete

# Ежемесячная проверка базы данных
python check_db.py

# Генерация отчетов
./monitor_autoposter.sh report
```

### 2. Мониторинг производительности
```bash
# Настройте cron для регулярных проверок
echo "*/30 * * * * cd /path/to/autoposter && ./monitor_autoposter.sh status >> logs/monitor.log 2>&1" | crontab -
```

### 3. Резервное копирование
```bash
# Ежедневное резервное копирование конфигурации и базы
cp config.json config.json.backup.$(date +%Y%m%d)
cp autoposter.db autoposter.db.backup.$(date +%Y%m%d)
```

## 🆘 Экстренное восстановление

### При полном сбое
1. **Остановите все процессы:**
   ```bash
   ./keepalive.sh stop
   pkill -f autoposter
   ```

2. **Проверьте целостность файлов:**
   ```bash
   python check_db.py
   python -c "import json; json.load(open('config.json'))"
   ```

3. **Перезапустите с чистого листа:**
   ```bash
   python autoposter.py reset_today
   ./keepalive.sh start
   ```

### При проблемах с базой данных
```bash
# Создайте резервную копию
cp autoposter.db autoposter.db.backup

# Пересоздайте базу
rm autoposter.db
python autoposter.py status  # Автоматически создаст новую базу
```

## 📞 Получение помощи

При обращении за помощью приложите:
1. Вывод `./monitor_autoposter.sh full`
2. Последние 50 строк логов: `tail -50 logs/autoposter.log`
3. Содержимое `last_shutdown.info`
4. Конфигурацию (без паролей): `jq 'del(.wordpress.password, .telegram.token, .gpt.api_key)' config.json` 