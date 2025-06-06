# 🚀 Установка AutoPoster на хостинге

## Быстрая установка

### 1. Подготовка файлов

```bash
# Даем права на выполнение скриптов
chmod +x setup_production.sh
chmod +x keepalive.sh

# Проверяем права
ls -la *.sh
```

### 2. Установка зависимостей

```bash
# Устанавливаем Python пакеты (путь уже настроен в скрипте)
/opt/python/python-3.8.8/bin/pip3 install -r requirements.txt
```

### 2.1. Исправление проблем с urllib3 (для старых серверов)

Если возникает ошибка с urllib3 и OpenSSL:

```bash
# Даем права и запускаем скрипт исправления
chmod +x fix_dependencies.sh
./fix_dependencies.sh
```

Или ручное исправление:

```bash
# Удаляем несовместимую версию
/opt/python/python-3.8.8/bin/pip3 uninstall urllib3 -y

# Устанавливаем совместимую версию
/opt/python/python-3.8.8/bin/pip3 install "urllib3>=1.26.0,<2.0.0"

# Переустанавливаем requests
/opt/python/python-3.8.8/bin/pip3 install --force-reinstall requests
```

### 3. Автоматическая установка

```bash
# Запускаем установку
./setup_production.sh install
```

### 4. Альтернативная установка

Если автоматическая установка не работает:

```bash
# Ручная установка
mkdir -p logs img
chmod 755 logs img

# Запуск keepalive
./keepalive.sh start
```

## Управление

### Основные команды:
```bash
./keepalive.sh start     # Запуск с мониторингом
./keepalive.sh stop      # Остановка
./keepalive.sh status    # Проверка статуса
./keepalive.sh restart   # Перезапуск
```

### Прямые команды autoposter:
```bash
/opt/python/python-3.8.8/bin/python autoposter.py status
/opt/python/python-3.8.8/bin/python autoposter.py publish_now
/opt/python/python-3.8.8/bin/python autoposter.py once
```

## Проверка работы

```bash
# Проверка процессов
ps aux | grep autoposter

# Проверка логов
tail -f logs/autoposter.log
tail -f logs/keepalive.log

# Проверка health
cat autoposter.health
```

## Диагностика

### Если не запускается:
```bash
# Проверка Python
/opt/python/python-3.8.8/bin/python --version

# Проверка зависимостей
/opt/python/python-3.8.8/bin/pip3 list

# Тестовый запуск
/opt/python/python-3.8.8/bin/python autoposter.py status
```

### Проверка конфигурации:
```bash
# Должны существовать файлы:
ls -la config.json theme_host.json

# Проверка прав
ls -la *.py *.sh
```

---

**Важно**: Все скрипты уже настроены для использования пути `/opt/python/python-3.8.8/bin/python` 