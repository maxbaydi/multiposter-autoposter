#!/bin/bash

# ===================================================================
# Background Check Script
# Проверка работы процессов в фоне
# ===================================================================

echo "🔍 Проверка фоновых процессов AutoPoster..."
echo "=================================="

# Проверка процессов autoposter
echo "📊 Процессы autoposter:"
ps aux | grep -v grep | grep autoposter || echo "❌ Процессы autoposter не найдены"
echo ""

# Проверка PID файлов
echo "📁 PID файлы:"
if [ -f "autoposter.pid" ]; then
    pid=$(cat autoposter.pid)
    echo "✅ PID файл найден: $pid"
    if kill -0 "$pid" 2>/dev/null; then
        echo "✅ Процесс с PID $pid активен"
    else
        echo "❌ Процесс с PID $pid не найден"
    fi
else
    echo "❌ PID файл не найден"
fi
echo ""

# Проверка health файла
echo "🏥 Health check:"
if [ -f "autoposter.health" ]; then
    echo "✅ Health файл найден"
    echo "Последнее обновление: $(stat -c %y autoposter.health)"
    echo "Содержимое:"
    cat autoposter.health
else
    echo "❌ Health файл не найден"
fi
echo ""

# Проверка cron задач
echo "⏰ Cron задачи:"
crontab -l | grep autoposter || echo "❌ Cron задачи не найдены"
echo ""

# Проверка логов
echo "📝 Последние записи в логах:"
if [ -f "logs/autoposter.log" ]; then
    echo "--- Последние 3 записи autoposter.log ---"
    tail -3 logs/autoposter.log
else
    echo "❌ Лог файл autoposter.log не найден"
fi
echo ""

if [ -f "logs/keepalive.log" ]; then
    echo "--- Последние 3 записи keepalive.log ---"
    tail -3 logs/keepalive.log
else
    echo "❌ Лог файл keepalive.log не найден"
fi
echo ""

# Тест независимости от сессии
echo "🔒 Проверка независимости от сессии:"
echo "Родительские процессы:"
ps -ef | grep -v grep | grep autoposter | awk '{print $3}' | while read ppid; do
    if [ "$ppid" = "1" ]; then
        echo "✅ Процесс работает под init (PID 1) - независим от сессии"
    else
        echo "⚠️ Процесс имеет родителя PID $ppid"
        ps -p $ppid -o pid,ppid,cmd --no-headers
    fi
done

echo ""
echo "🚀 Инструкции для проверки после выхода:"
echo "1. Выйдите из SSH сессии"
echo "2. Подождите 2-3 минуты" 
echo "3. Войдите снова и запустите:"
echo "   ./check_background.sh"
echo "   или"
echo "   ./keepalive.sh status" 