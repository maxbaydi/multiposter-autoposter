#!/bin/bash

# Скрипт для управления логами AutoPoster
# Использование: ./manage_logs.sh [команда]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
MAIN_LOG="$LOG_DIR/autoposter.log"
NOHUP_LOG="$SCRIPT_DIR/nohup.out"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция вывода с цветом
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Показать справку
show_help() {
    echo -e "${BLUE}=== УПРАВЛЕНИЕ ЛОГАМИ AUTOPOSTER ===${NC}"
    echo ""
    echo "Доступные команды:"
    echo ""
    echo "  📊 ПРОСМОТР ЛОГОВ:"
    echo "    tail      - последние 50 строк логов"
    echo "    follow    - мониторинг логов в реальном времени"
    echo "    today     - логи за сегодня"
    echo "    errors    - только ошибки"
    echo "    stats     - статистика публикаций"
    echo ""
    echo "  🔍 ПОИСК В ЛОГАХ:"
    echo "    search [текст]  - поиск по тексту"
    echo "    posts           - все публикации"
    echo "    wordpress       - публикации WordPress"
    echo "    telegram        - публикации Telegram"
    echo ""
    echo "  🧹 УПРАВЛЕНИЕ:"
    echo "    clean     - очистить старые логи (>7 дней)"
    echo "    size      - размер лог файлов"
    echo "    rotate    - принудительная ротация логов"
    echo ""
    echo "  🤖 УПРАВЛЕНИЕ БОТОМ:"
    echo "    start     - запустить бота через nohup"
    echo "    stop      - остановить бота"
    echo "    status    - статус бота"
    echo "    restart   - перезапустить бота"
    echo ""
    echo "Примеры:"
    echo "  ./manage_logs.sh follow"
    echo "  ./manage_logs.sh search 'Schneider Electric'"
    echo "  ./manage_logs.sh start"
}

# Проверить статус бота
check_bot_status() {
    if pgrep -f "python.*autoposter.py" > /dev/null; then
        local pid=$(pgrep -f "python.*autoposter.py")
        log_info "Бот запущен (PID: $pid)"
        return 0
    else
        log_warn "Бот не запущен"
        return 1
    fi
}

# Основная логика
case "${1:-help}" in
    # Просмотр логов
    "tail")
        if [[ -f "$MAIN_LOG" ]]; then
            log_info "Последние 50 строк из $MAIN_LOG:"
            tail -n 50 "$MAIN_LOG"
        else
            log_error "Файл логов не найден: $MAIN_LOG"
        fi
        ;;
    
    "follow")
        if [[ -f "$MAIN_LOG" ]]; then
            log_info "Мониторинг логов в реальном времени (Ctrl+C для выхода):"
            tail -f "$MAIN_LOG"
        else
            log_error "Файл логов не найден: $MAIN_LOG"
        fi
        ;;
    
    "today")
        if [[ -f "$MAIN_LOG" ]]; then
            local today=$(date '+%Y-%m-%d')
            log_info "Логи за сегодня ($today):"
            grep "$today" "$MAIN_LOG" || log_warn "Нет логов за сегодня"
        else
            log_error "Файл логов не найден: $MAIN_LOG"
        fi
        ;;
    
    "errors")
        if [[ -f "$MAIN_LOG" ]]; then
            log_info "Только ошибки:"
            grep -E "(ERROR|❌|Ошибка)" "$MAIN_LOG" || log_info "Ошибок не найдено"
        else
            log_error "Файл логов не найден: $MAIN_LOG"
        fi
        ;;
    
    "stats")
        if [[ -f "$MAIN_LOG" ]]; then
            log_info "Статистика публикаций:"
            echo "WordPress: $(grep -c 'опубликован в WordPress' "$MAIN_LOG")"
            echo "Telegram: $(grep -c 'отправлено в Telegram' "$MAIN_LOG")"
            echo "Ошибки: $(grep -c -E '(ERROR|❌)' "$MAIN_LOG")"
        else
            log_error "Файл логов не найден: $MAIN_LOG"
        fi
        ;;
    
    # Поиск
    "search")
        if [[ -z "$2" ]]; then
            log_error "Укажите текст для поиска: ./manage_logs.sh search 'текст'"
            exit 1
        fi
        if [[ -f "$MAIN_LOG" ]]; then
            log_info "Поиск '$2' в логах:"
            grep -i "$2" "$MAIN_LOG" || log_warn "Ничего не найдено"
        else
            log_error "Файл логов не найден: $MAIN_LOG"
        fi
        ;;
    
    "posts")
        if [[ -f "$MAIN_LOG" ]]; then
            log_info "Все публикации:"
            grep "опубликован" "$MAIN_LOG" || log_warn "Публикаций не найдено"
        else
            log_error "Файл логов не найден: $MAIN_LOG"
        fi
        ;;
    
    "wordpress")
        if [[ -f "$MAIN_LOG" ]]; then
            log_info "Публикации WordPress:"
            grep "WordPress" "$MAIN_LOG" || log_warn "Публикаций WordPress не найдено"
        else
            log_error "Файл логов не найден: $MAIN_LOG"
        fi
        ;;
    
    "telegram")
        if [[ -f "$MAIN_LOG" ]]; then
            log_info "Публикации Telegram:"
            grep "Telegram" "$MAIN_LOG" || log_warn "Публикаций Telegram не найдено"
        else
            log_error "Файл логов не найден: $MAIN_LOG"
        fi
        ;;
    
    # Управление логами
    "clean")
        log_info "Очистка старых логов (>7 дней)..."
        if [[ -d "$LOG_DIR" ]]; then
            find "$LOG_DIR" -name "*.log*" -mtime +7 -delete
            log_info "Старые логи удалены"
        else
            log_warn "Директория логов не найдена"
        fi
        ;;
    
    "size")
        if [[ -d "$LOG_DIR" ]]; then
            log_info "Размер лог файлов:"
            du -h "$LOG_DIR"/* 2>/dev/null || log_warn "Лог файлы не найдены"
        else
            log_warn "Директория логов не найдена"
        fi
        if [[ -f "$NOHUP_LOG" ]]; then
            echo "nohup.out: $(du -h "$NOHUP_LOG" | cut -f1)"
        fi
        ;;
    
    "rotate")
        log_info "Принудительная ротация логов не требуется - используется автоматическая ротация"
        log_info "Максимальный размер файла: 10MB, количество файлов: 5"
        ;;
    
    # Управление ботом
    "start")
        if check_bot_status; then
            log_warn "Бот уже запущен"
        else
            log_info "Запуск бота через nohup..."
            cd "$SCRIPT_DIR"
            nohup python autoposter.py start > nohup.out 2>&1 &
            sleep 2
            if check_bot_status; then
                log_info "Бот успешно запущен"
                log_info "Логи: tail -f nohup.out или ./manage_logs.sh follow"
            else
                log_error "Не удалось запустить бота"
            fi
        fi
        ;;
    
    "stop")
        if check_bot_status; then
            log_info "Остановка бота..."
            python autoposter.py stop
        else
            log_warn "Бот не запущен"
        fi
        ;;
    
    "status")
        check_bot_status
        if [[ -f "$MAIN_LOG" ]]; then
            local last_activity=$(tail -n 1 "$MAIN_LOG" | cut -d' ' -f1,2)
            log_info "Последняя активность: $last_activity"
        fi
        ;;
    
    "restart")
        log_info "Перезапуск бота..."
        if check_bot_status; then
            python autoposter.py stop
            sleep 3
        fi
        cd "$SCRIPT_DIR"
        nohup python autoposter.py start > nohup.out 2>&1 &
        sleep 2
        if check_bot_status; then
            log_info "Бот успешно перезапущен"
        else
            log_error "Не удалось перезапустить бота"
        fi
        ;;
    
    "help"|*)
        show_help
        ;;
esac 