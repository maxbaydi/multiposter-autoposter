#!/bin/bash

# ===================================================================
# AutoPoster Advanced Monitor Script
# Расширенный мониторинг с диагностикой и отчетами
# ===================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTOPOSTER_SCRIPT="$SCRIPT_DIR/autoposter.py"
HEALTH_FILE="$SCRIPT_DIR/autoposter.health"
LOG_FILE="$SCRIPT_DIR/logs/autoposter.log"
MONITOR_LOG="$SCRIPT_DIR/logs/monitor.log"
SHUTDOWN_INFO="$SCRIPT_DIR/last_shutdown.info"
PYTHON_CMD="/opt/python/python-3.8.8/bin/python"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$MONITOR_LOG"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$MONITOR_LOG" >&2
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$MONITOR_LOG"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}" | tee -a "$MONITOR_LOG"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a "$MONITOR_LOG"
}

# Проверка статуса autoposter
check_autoposter_status() {
    local pid=$(pgrep -f "python.*autoposter.py")
    if [[ -n "$pid" ]]; then
        echo "running"
        return 0
    else
        echo "stopped"
        return 1
    fi
}

# Анализ health file
analyze_health() {
    if [[ ! -f "$HEALTH_FILE" ]]; then
        error "Health file не найден: $HEALTH_FILE"
        return 1
    fi
    
    if command -v jq &> /dev/null; then
        local status=$(jq -r '.status // "unknown"' "$HEALTH_FILE" 2>/dev/null)
        local published_today=$(jq -r '.publishing.published_today // 0' "$HEALTH_FILE" 2>/dev/null)
        local posts_per_day=$(jq -r '.publishing.posts_per_day // 3' "$HEALTH_FILE" 2>/dev/null)
        local wp_failures=$(jq -r '.circuit_breaker.wordpress.failures // 0' "$HEALTH_FILE" 2>/dev/null)
        local tg_failures=$(jq -r '.circuit_breaker.telegram.failures // 0' "$HEALTH_FILE" 2>/dev/null)
        local missed_slots=$(jq -r '[.publishing.slots[]? | select(.status == "missed")] | length' "$HEALTH_FILE" 2>/dev/null)
        
        info "Статус: $status"
        info "Опубликовано сегодня: $published_today/$posts_per_day"
        info "WordPress ошибки: $wp_failures"
        info "Telegram ошибки: $tg_failures"
        
        if [[ "$missed_slots" != "null" && "$missed_slots" -gt 0 ]]; then
            warning "Пропущено слотов: $missed_slots"
        fi
        
        # Проверяем старость health file
        local health_timestamp=$(jq -r '.timestamp' "$HEALTH_FILE" 2>/dev/null)
        if [[ "$health_timestamp" != "null" ]]; then
            local health_age=$(( $(date +%s) - $(date -d "$health_timestamp" +%s 2>/dev/null || echo 0) ))
            if [[ $health_age -gt 600 ]]; then
                warning "Health check устарел на $((health_age / 60)) минут"
            fi
        fi
    else
        warning "jq не установлен, ограниченный анализ health file"
        grep -o '"status": *"[^"]*"' "$HEALTH_FILE" 2>/dev/null || echo "Не удалось прочитать статус"
    fi
}

# Анализ последнего завершения
analyze_last_shutdown() {
    if [[ -f "$SHUTDOWN_INFO" ]]; then
        info "Информация о последнем завершении:"
        if command -v jq &> /dev/null; then
            local timestamp=$(jq -r '.timestamp // "unknown"' "$SHUTDOWN_INFO" 2>/dev/null)
            local signal=$(jq -r '.signal // "unknown"' "$SHUTDOWN_INFO" 2>/dev/null)
            local reason=$(jq -r '.reason // "unknown"' "$SHUTDOWN_INFO" 2>/dev/null)
            local graceful=$(jq -r '.graceful // false' "$SHUTDOWN_INFO" 2>/dev/null)
            
            info "  Время: $timestamp"
            info "  Сигнал: $signal"
            info "  Причина: $reason"
            info "  Graceful: $graceful"
        else
            cat "$SHUTDOWN_INFO"
        fi
    else
        info "Информация о последнем завершении недоступна"
    fi
}

# Анализ логов
analyze_logs() {
    if [[ ! -f "$LOG_FILE" ]]; then
        error "Лог файл не найден: $LOG_FILE"
        return 1
    fi
    
    info "Анализ логов за последние 24 часа:"
    
    # Количество ошибок
    local errors_24h=$(grep -c "ERROR" "$LOG_FILE" | head -n 1)
    local warnings_24h=$(grep -c "WARNING" "$LOG_FILE" | head -n 1)
    
    info "Ошибки: $errors_24h"
    info "Предупреждения: $warnings_24h"
    
    # Последние ошибки
    if [[ $errors_24h -gt 0 ]]; then
        warning "Последние ошибки:"
        tail -n 100 "$LOG_FILE" | grep "ERROR" | tail -n 3
    fi
    
    # Статистика публикаций
    local publications_today=$(grep "$(date +%Y-%m-%d)" "$LOG_FILE" | grep -c "опубликовано" || echo 0)
    info "Публикаций сегодня: $publications_today"
}

# Проверка ресурсов системы
check_system_resources() {
    info "Проверка системных ресурсов:"
    
    # Место на диске
    local disk_usage=$(df "$SCRIPT_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 90 ]]; then
        error "Мало места на диске: ${disk_usage}%"
    elif [[ $disk_usage -gt 80 ]]; then
        warning "Заканчивается место на диске: ${disk_usage}%"
    else
        info "Место на диске: ${disk_usage}%"
    fi
    
    # Размер лог файлов
    if [[ -f "$LOG_FILE" ]]; then
        local log_size=$(du -h "$LOG_FILE" | cut -f1)
        info "Размер лог файла: $log_size"
    fi
    
    # Проверка Python
    if command -v "$PYTHON_CMD" &> /dev/null; then
        local python_version=$("$PYTHON_CMD" --version 2>&1)
        info "Python: $python_version"
    else
        error "Python не найден: $PYTHON_CMD"
    fi
}

# Генерация отчета
generate_report() {
    local report_file="$SCRIPT_DIR/logs/autoposter_report_$(date +%Y%m%d_%H%M).txt"
    
    echo "=== AutoPoster Diagnostic Report ===" > "$report_file"
    echo "Generated: $(date)" >> "$report_file"
    echo "" >> "$report_file"
    
    echo "--- System Status ---" >> "$report_file"
    echo "AutoPoster Status: $(check_autoposter_status)" >> "$report_file"
    echo "" >> "$report_file"
    
    echo "--- Health Analysis ---" >> "$report_file"
    analyze_health >> "$report_file" 2>&1
    echo "" >> "$report_file"
    
    echo "--- Last Shutdown ---" >> "$report_file"
    analyze_last_shutdown >> "$report_file" 2>&1
    echo "" >> "$report_file"
    
    echo "--- System Resources ---" >> "$report_file"
    check_system_resources >> "$report_file" 2>&1
    echo "" >> "$report_file"
    
    echo "--- Recent Logs ---" >> "$report_file"
    if [[ -f "$LOG_FILE" ]]; then
        echo "Last 20 lines:" >> "$report_file"
        tail -n 20 "$LOG_FILE" >> "$report_file"
    fi
    
    info "Отчет сохранен: $report_file"
}

# Главная функция
case "${1:-status}" in
    "status")
        info "=== AutoPoster Monitor Status ==="
        echo "AutoPoster: $(check_autoposter_status)"
        analyze_health
        ;;
    "health")
        info "=== Health Analysis ==="
        analyze_health
        ;;
    "logs")
        info "=== Log Analysis ==="
        analyze_logs
        ;;
    "shutdown")
        info "=== Last Shutdown Analysis ==="
        analyze_last_shutdown
        ;;
    "system")
        info "=== System Resources ==="
        check_system_resources
        ;;
    "report")
        info "=== Generating Diagnostic Report ==="
        generate_report
        ;;
    "full")
        info "=== Full Diagnostic ==="
        echo "AutoPoster: $(check_autoposter_status)"
        echo ""
        analyze_health
        echo ""
        analyze_last_shutdown
        echo ""
        analyze_logs
        echo ""
        check_system_resources
        ;;
    *)
        echo "Использование: $0 {status|health|logs|shutdown|system|report|full}"
        echo ""
        echo "  status   - краткий статус"
        echo "  health   - анализ health check"
        echo "  logs     - анализ логов"
        echo "  shutdown - анализ последнего завершения"
        echo "  system   - проверка ресурсов"
        echo "  report   - генерация полного отчета"
        echo "  full     - полная диагностика"
        ;;
esac 