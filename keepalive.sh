#!/bin/bash

# ===================================================================
# AutoPoster KeepAlive Script
# Автоматический мониторинг и перезапуск autoposter
# ===================================================================

# Настройки
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTOPOSTER_SCRIPT="$SCRIPT_DIR/autoposter.py"
HEALTH_FILE="$SCRIPT_DIR/autoposter.health"
PID_FILE="$SCRIPT_DIR/autoposter.pid"
LOG_FILE="$SCRIPT_DIR/logs/keepalive.log"
PYTHON_CMD="/opt/python/python-3.8.8/bin/python"

# Интервалы проверки (в секундах)
CHECK_INTERVAL=30          # Проверка каждые 30 секунд
HEALTH_TIMEOUT=600         # Таймаут health check (10 минут)
MAX_RESTART_ATTEMPTS=5     # Максимум попыток перезапуска
RESTART_DELAY=60           # Задержка между перезапусками

# Счетчики
RESTART_COUNT=0
LAST_RESTART_TIME=0

# Функции логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

# Проверка существования autoposter.py
check_script_exists() {
    if [[ ! -f "$AUTOPOSTER_SCRIPT" ]]; then
        error "Autoposter script не найден: $AUTOPOSTER_SCRIPT"
        exit 1
    fi
}

# Проверка установки Python
check_python() {
    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        error "Python не найден. Проверьте установку."
        exit 1
    fi
}

# Создание директории логов
ensure_log_dir() {
    local log_dir=$(dirname "$LOG_FILE")
    if [[ ! -d "$log_dir" ]]; then
        mkdir -p "$log_dir"
    fi
}

# Получение PID процесса autoposter
get_autoposter_pid() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE" 2>/dev/null)
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return 0
        else
            # PID файл существует, но процесс не запущен
            rm -f "$PID_FILE"
        fi
    fi
    
    # Поиск процесса по имени
    pgrep -f "python.*autoposter.py"
}

# Проверка здоровья autoposter через health file
check_health() {
    if [[ ! -f "$HEALTH_FILE" ]]; then
        return 1  # Health file не найден
    fi
    
    # Проверяем время последнего обновления
    local health_timestamp=$(stat -c %Y "$HEALTH_FILE" 2>/dev/null)
    local current_time=$(date +%s)
    local time_diff=$((current_time - health_timestamp))
    
    if [[ $time_diff -gt $HEALTH_TIMEOUT ]]; then
        return 1  # Health file слишком старый
    fi
    
    # Проверяем содержимое health file
    if command -v jq &> /dev/null; then
        local status=$(jq -r '.status // "unknown"' "$HEALTH_FILE" 2>/dev/null)
        if [[ "$status" == "running" ]]; then
            return 0  # Все хорошо
        fi
    else
        # Если jq не установлен, проверяем просто наличие "running"
        if grep -q '"status": "running"' "$HEALTH_FILE" 2>/dev/null; then
            return 0
        fi
    fi
    
    return 1  # Проблемы с health check
}

# Запуск autoposter
start_autoposter() {
    log "🚀 Запуск autoposter..."
    
    cd "$SCRIPT_DIR"
    nohup "$PYTHON_CMD" "$AUTOPOSTER_SCRIPT" start > /dev/null 2>&1 &
    local pid=$!
    
    # Сохраняем PID
    echo "$pid" > "$PID_FILE"
    
    # Ждем немного и проверяем, что процесс действительно запустился
    sleep 5
    if kill -0 "$pid" 2>/dev/null; then
        log "✅ Autoposter запущен с PID: $pid"
        RESTART_COUNT=$((RESTART_COUNT + 1))
        LAST_RESTART_TIME=$(date +%s)
        return 0
    else
        error "❌ Не удалось запустить autoposter"
        rm -f "$PID_FILE"
        return 1
    fi
}

# Остановка autoposter
stop_autoposter() {
    local pid=$(get_autoposter_pid)
    if [[ -n "$pid" ]]; then
        log "🛑 Остановка autoposter (PID: $pid)..."
        
        # Сначала пробуем graceful shutdown
        kill -TERM "$pid" 2>/dev/null
        
        # Ждем до 30 секунд для graceful shutdown
        local count=0
        while [[ $count -lt 30 ]] && kill -0 "$pid" 2>/dev/null; do
            sleep 1
            ((count++))
        done
        
        # Если процесс все еще работает, принудительно завершаем
        if kill -0 "$pid" 2>/dev/null; then
            log "⚡ Принудительное завершение autoposter..."
            kill -KILL "$pid" 2>/dev/null
            sleep 2
        fi
        
        rm -f "$PID_FILE"
        log "✅ Autoposter остановлен"
    else
        log "ℹ️ Autoposter не запущен"
    fi
}

# Перезапуск autoposter
restart_autoposter() {
    log "🔄 Перезапуск autoposter..."
    stop_autoposter
    sleep 3
    start_autoposter
}

# Проверка ограничений на перезапуски
check_restart_limits() {
    local current_time=$(date +%s)
    local time_since_last_restart=$((current_time - LAST_RESTART_TIME))
    
    # Если прошло больше часа с последнего перезапуска, сбрасываем счетчик
    if [[ $time_since_last_restart -gt 3600 ]]; then
        RESTART_COUNT=0
    fi
    
    if [[ $RESTART_COUNT -ge $MAX_RESTART_ATTEMPTS ]]; then
        error "❌ Достигнут лимит перезапусков ($MAX_RESTART_ATTEMPTS). Остановка keepalive."
        return 1
    fi
    
    return 0
}

# Основной цикл мониторинга
main_loop() {
    log "🔧 Запуск KeepAlive для autoposter"
    log "📁 Директория: $SCRIPT_DIR"
    log "🐍 Python: $PYTHON_CMD"
    log "⏱️ Интервал проверки: ${CHECK_INTERVAL}s"
    log "🕒 Таймаут health check: ${HEALTH_TIMEOUT}s"
    
    while true; do
        local pid=$(get_autoposter_pid)
        local health_ok=false
        
        # Проверяем процесс
        if [[ -n "$pid" ]]; then
            # Процесс запущен, проверяем health
            if check_health; then
                health_ok=true
                log "✅ Autoposter работает нормально (PID: $pid)"
            else
                log "⚠️ Autoposter запущен, но health check неудачен (PID: $pid)"
            fi
        else
            log "❌ Autoposter не запущен"
        fi
        
        # Принимаем решение о перезапуске
        if [[ -z "$pid" ]] || [[ "$health_ok" == false ]]; then
            if check_restart_limits; then
                log "🔄 Инициируется перезапуск... (попытка $((RESTART_COUNT + 1))/$MAX_RESTART_ATTEMPTS)"
                restart_autoposter
                
                if [[ $? -eq 0 ]]; then
                    log "✅ Перезапуск успешен"
                else
                    error "❌ Перезапуск неудачен"
                    sleep $RESTART_DELAY
                fi
            else
                break
            fi
        fi
        
        # Ожидание до следующей проверки
        sleep $CHECK_INTERVAL
    done
}

# Обработка сигналов
cleanup() {
    log "🛑 Получен сигнал завершения KeepAlive"
    stop_autoposter
    exit 0
}

trap cleanup SIGTERM SIGINT

# Обработка аргументов командной строки
case "${1:-start}" in
    start)
        ensure_log_dir
        check_script_exists
        check_python
        main_loop
        ;;
    stop)
        stop_autoposter
        ;;
    restart)
        restart_autoposter
        ;;
    status)
        pid=$(get_autoposter_pid)
        if [[ -n "$pid" ]]; then
            echo "✅ Autoposter запущен (PID: $pid)"
            if check_health; then
                echo "✅ Health check: OK"
            else
                echo "⚠️ Health check: FAILED"
            fi
            exit 0
        else
            echo "❌ Autoposter не запущен"
            exit 1
        fi
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status}"
        echo ""
        echo "start   - Запуск мониторинга autoposter"
        echo "stop    - Остановка autoposter"
        echo "restart - Перезапуск autoposter"
        echo "status  - Проверка статуса autoposter"
        exit 1
        ;;
esac 