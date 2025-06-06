# 🚀 Быстрый деплой AutoPoster на сервер

## 📋 Минимальная инструкция для nohup

### 1. **Запуск бота:**

```bash
# Перейти в директорию проекта
cd autoposter

# Запуск с логированием
nohup python autoposter.py start > nohup.out 2>&1 &

# Сохранить PID для управления
echo $! > autoposter.pid
```

### 2. **Просмотр логов:**

```bash
# Логи nohup (дублируют основные логи)
tail -f nohup.out

# Основные логи (более детальные)
tail -f logs/autoposter.log

# Только ошибки
grep -E "(ERROR|❌)" logs/autoposter.log
```

### 3. **Управление ботом:**

```bash
# Проверить статус
ps aux | grep autoposter.py

# Остановить бота (мягко)
python autoposter.py stop

# Принудительная остановка
kill $(cat autoposter.pid)

# Или через pkill
pkill -f "autoposter.py"
```

### 4. **Команды управления на ходу:**

```bash
# Принудительная публикация
touch autoposter.publish_now

# Запрос статуса
touch autoposter.status

# Сброс счетчика за день
touch autoposter.reset_today

# Остановка
touch autoposter.stop
```

## 📊 Где искать логи:

1. **`nohup.out`** - вывод nohup (дублирует консоль)
2. **`logs/autoposter.log`** - основные логи с ротацией
3. **`logs/autoposter.log.1`** - архивные логи

## 🔍 Полезные команды для мониторинга:

```bash
# Мониторинг активности
tail -f logs/autoposter.log | grep "опубликован"

# Статистика за сегодня
grep "$(date '+%Y-%m-%d')" logs/autoposter.log | grep -c "Автоматически опубликовано"

# Ошибки за последний час
grep "$(date '+%Y-%m-%d %H')" logs/autoposter.log | grep ERROR

# Размер логов
du -h logs/ nohup.out

# Проверка процесса
ps -o pid,ppid,cmd,%mem,%cpu -p $(pgrep -f autoposter.py)
```

## ⚡ Автозапуск через cron:

```bash
# Добавить в crontab
crontab -e

# Запуск при загрузке системы (обновите путь к проекту)
@reboot cd /path/to/your/project/autoposter && nohup python autoposter.py start > nohup.out 2>&1 &

# Проверка каждые 5 минут
*/5 * * * * pgrep -f autoposter.py || (cd /path/to/your/project/autoposter && nohup python autoposter.py start > nohup.out 2>&1 &)
```

## 🆘 Troubleshooting:

```bash
# Если бот не запускается - тест конфигурации
python autoposter.py once

# Проверка синтаксиса Python
python -m py_compile autoposter.py

# Если логи не создаются
mkdir -p logs && chmod 755 logs

# Если процесс завис
pkill -9 -f autoposter.py

# Полная диагностика
echo "Процесс: $(pgrep -f autoposter.py || echo 'НЕ ЗАПУЩЕН')"
echo "Логи: $(ls -la logs/)"
echo "Последняя активность: $(tail -n 1 logs/autoposter.log 2>/dev/null || echo 'НЕТ ЛОГОВ')"
```

## 💡 Советы по деплою:

### 🐍 **Проверка версии Python:**
```bash
# Узнать доступные версии Python
which python
which python3
python --version
python3 --version
```

### 📁 **Права доступа:**
```bash
# Убедиться в правах на запись
chmod +x autoposter.py
chmod 755 logs/
```

### 🔗 **Проверка зависимостей:**
```bash
# Установка зависимостей если нужно
pip3 install -r requirements.txt
# или
pip install -r requirements.txt
```

---

💡 **Совет:** Используйте `tail -f logs/autoposter.log` для мониторинга работы в реальном времени! 