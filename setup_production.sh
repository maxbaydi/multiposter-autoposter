#!/bin/bash

# ===================================================================
# AutoPoster Production Setup Script
# Настройка продуктивной среды с автоматическим перезапуском
# ===================================================================

set -e  # Остановка при ошибке

# Настройки
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="autoposter"
KEEPALIVE_SCRIPT="$SCRIPT_DIR/keepalive.sh"
PYTHON_CMD="/opt/python/python-3.8.8/bin/python"
PIP_CMD="/opt/python/python-3.8.8/bin/pip3"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции вывода
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка прав доступа
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        warning "Скрипт запущен от root. Это может потребоваться для системных настроек."
    fi
}

# Проверка зависимостей
check_dependencies() {
    info "Проверка зависимостей..."
    
    # Проверка Python
    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        error "Python не найден по пути: $PYTHON_CMD"
        exit 1
    fi
    
    # Проверка pip
    if ! command -v "$PIP_CMD" &> /dev/null; then 
        error "pip не найден по пути: $PIP_CMD"
        exit 1
    fi
    
    success "Все зависимости найдены"
}

# Установка Python зависимостей
install_python_deps() {
    info "Установка Python зависимостей..."
    
    if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
        "$PIP_CMD" install -r "$SCRIPT_DIR/requirements.txt"
        success "Python зависимости установлены"
    else
        warning "requirements.txt не найден"
    fi
}

# Создание необходимых директорий
create_directories() {
    info "Создание необходимых директорий..."
    
    mkdir -p "$SCRIPT_DIR/logs"
    mkdir -p "$SCRIPT_DIR/img"
    
    # Устанавливаем права доступа
    chmod 755 "$SCRIPT_DIR"
    chmod 755 "$SCRIPT_DIR/logs"
    chmod 755 "$SCRIPT_DIR/img"
    
    success "Директории созданы"
}

# Настройка keepalive скрипта
setup_keepalive() {
    info "Настройка keepalive скрипта..."
    
    if [[ -f "$KEEPALIVE_SCRIPT" ]]; then
        chmod +x "$KEEPALIVE_SCRIPT"
        success "Keepalive скрипт настроен"
    else
        error "Keepalive скрипт не найден: $KEEPALIVE_SCRIPT"
        exit 1
    fi
}

# Настройка systemd сервиса (если возможно)
setup_systemd_service() {
    if command -v systemctl &> /dev/null && [[ $EUID -eq 0 ]]; then
        info "Настройка systemd сервиса..."
        
        # Обновляем пути в сервис файле
        sed -i "s|/var/www/u2946491/data/autoposter|$SCRIPT_DIR|g" "$SCRIPT_DIR/autoposter.service"
        
        # Копируем сервис файл
        cp "$SCRIPT_DIR/autoposter.service" "/etc/systemd/system/${SERVICE_NAME}.service"
        
        # Перезагружаем systemd
        systemctl daemon-reload
        systemctl enable "$SERVICE_NAME"
        
        success "Systemd сервис настроен и включен"
        info "Используйте команды:"
        info "  systemctl start $SERVICE_NAME    # Запуск"
        info "  systemctl stop $SERVICE_NAME     # Остановка"
        info "  systemctl status $SERVICE_NAME   # Статус"
        info "  systemctl restart $SERVICE_NAME  # Перезапуск"
    else
        warning "Systemd недоступен или нет прав root. Используйте keepalive скрипт напрямую."
    fi
}

# Создание cron задачи (альтернатива systemd)
setup_cron() {
    if ! command -v systemctl &> /dev/null || [[ $EUID -ne 0 ]]; then
        info "Настройка cron задачи..."
        
        # Создаем cron задачу для проверки keepalive каждые 5 минут
        CRON_CMD="*/5 * * * * $KEEPALIVE_SCRIPT status > /dev/null || $KEEPALIVE_SCRIPT start"
        
        # Добавляем в crontab если еще нет
        (crontab -l 2>/dev/null | grep -v "$KEEPALIVE_SCRIPT"; echo "$CRON_CMD") | crontab -
        
        success "Cron задача настроена (проверка каждые 5 минут)"
        info "Для просмотра cron задач: crontab -l"
        info "Для удаления: crontab -e"
    fi
}

# Проверка конфигурации
check_config() {
    info "Проверка конфигурации..."
    
    if [[ ! -f "$SCRIPT_DIR/config.json" ]]; then
        error "config.json не найден. Создайте его на основе config.json.example"
        exit 1
    fi
    
    if [[ ! -f "$SCRIPT_DIR/theme_host.json" ]]; then
        error "theme_host.json не найден"
        exit 1
    fi
    
    success "Конфигурация найдена"
}

# Тестовый запуск
test_run() {
    info "Тестовый запуск autoposter..."
    
    cd "$SCRIPT_DIR"
    
    # Тестируем разовую публикацию
    if "$PYTHON_CMD" autoposter.py status; then
        success "Autoposter работает корректно"
    else
        warning "Возможны проблемы с autoposter. Проверьте конфигурацию."
    fi
}

# Основная функция установки
main() {
    echo "=========================================="
    echo "  AutoPoster Production Setup"
    echo "=========================================="
    echo ""
    
    check_permissions
    check_dependencies
    install_python_deps
    create_directories
    setup_keepalive
    check_config
    
    # Настройка автозапуска
    if [[ "${1:-}" == "--with-systemd" ]] && [[ $EUID -eq 0 ]]; then
        setup_systemd_service
    else
        setup_cron
    fi
    
    test_run
    
    echo ""
    echo "=========================================="
    success "Установка завершена!"
    echo "=========================================="
    echo ""
    info "Доступные команды:"
    echo "  $KEEPALIVE_SCRIPT start     # Запуск с мониторингом"
    echo "  $KEEPALIVE_SCRIPT stop      # Остановка"
    echo "  $KEEPALIVE_SCRIPT restart   # Перезапуск"
    echo "  $KEEPALIVE_SCRIPT status    # Проверка статуса"
    echo ""
    info "Логи:"
    echo "  tail -f $SCRIPT_DIR/logs/autoposter.log     # Логи autoposter"
    echo "  tail -f $SCRIPT_DIR/logs/keepalive.log      # Логи keepalive"
    echo ""
    info "Health check:"
    echo "  cat $SCRIPT_DIR/autoposter.health           # Текущий статус"
    echo ""
    
    if command -v systemctl &> /dev/null && [[ $EUID -eq 0 ]] && [[ "${1:-}" == "--with-systemd" ]]; then
        info "Systemd команды:"
        echo "  systemctl start $SERVICE_NAME"
        echo "  systemctl status $SERVICE_NAME"
        echo "  journalctl -u $SERVICE_NAME -f"
    fi
}

# Обработка аргументов
case "${1:-install}" in
    install|--with-systemd)
        main "$@"
        ;;
    uninstall)
        info "Удаление autoposter..."
        
        # Остановка всех процессов
        "$KEEPALIVE_SCRIPT" stop 2>/dev/null || true
        
        # Удаление systemd сервиса
        if [[ $EUID -eq 0 ]] && systemctl is-enabled "$SERVICE_NAME" &>/dev/null; then
            systemctl stop "$SERVICE_NAME"
            systemctl disable "$SERVICE_NAME"
            rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
            systemctl daemon-reload
        fi
        
        # Удаление cron задач
        crontab -l 2>/dev/null | grep -v "$KEEPALIVE_SCRIPT" | crontab - 2>/dev/null || true
        
        success "Autoposter удален"
        ;;
    *)
        echo "Использование: $0 [install|--with-systemd|uninstall]"
        echo ""
        echo "install          - Обычная установка с cron"
        echo "--with-systemd   - Установка с systemd (требует root)"
        echo "uninstall        - Удаление autoposter"
        exit 1
        ;;
esac 