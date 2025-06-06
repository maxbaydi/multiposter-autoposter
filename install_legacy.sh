#!/bin/bash

# ===================================================================
# Legacy Install Script for AutoPoster
# Установка совместимых зависимостей для старых серверов
# ===================================================================

PYTHON_CMD="/opt/python/python-3.8.8/bin/python"
PIP_CMD="/opt/python/python-3.8.8/bin/pip3"

echo "🔧 Установка зависимостей для legacy серверов..."

# Проверяем версию OpenSSL
echo "📋 Информация о системе:"
echo "OpenSSL version: $($PYTHON_CMD -c "import ssl; print(ssl.OPENSSL_VERSION)")"
echo "Python version: $($PYTHON_CMD --version)"

# Полная очистка
echo "🗑️ Полная очистка зависимостей..."
$PIP_CMD uninstall urllib3 requests certifi charset-normalizer idna Pillow python-dateutil -y 2>/dev/null || true

# Установка из legacy requirements
echo "📦 Установка legacy зависимостей..."
$PIP_CMD install -r requirements-legacy.txt --force-reinstall

# Проверяем что всё работает
echo "✅ Тестирование..."
if $PYTHON_CMD -c "
import sys
print('Python:', sys.version)

import ssl
print('OpenSSL:', ssl.OPENSSL_VERSION)

import urllib3
print('urllib3:', urllib3.__version__)

import requests
print('requests:', requests.__version__)

import certifi
print('certifi:', certifi.__version__)

print('✅ Все пакеты загружены успешно!')

# Тест HTTP запроса
try:
    import requests
    response = requests.get('https://httpbin.org/get', timeout=10)
    print('✅ HTTP запросы работают!')
except Exception as e:
    print('❌ Ошибка HTTP запроса:', e)
"; then
    echo "🎉 Legacy зависимости успешно установлены!"
else
    echo "❌ Ошибка при тестировании"
    exit 1
fi

# Показываем итоговые версии
echo "📊 Установленные версии:"
$PIP_CMD list | grep -E "(urllib3|requests|certifi|charset-normalizer|idna|Pillow)"

echo "🚀 Теперь можно запускать autoposter!"
echo "💡 Команда для тестирования: /opt/python/python-3.8.8/bin/python autoposter.py status" 