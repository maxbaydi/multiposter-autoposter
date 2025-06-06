#!/bin/bash

# ===================================================================
# Fix Dependencies Script for AutoPoster
# Исправление проблем с urllib3 на старых серверах
# ===================================================================

PYTHON_CMD="/opt/python/python-3.8.8/bin/python"
PIP_CMD="/opt/python/python-3.8.8/bin/pip3"

echo "🔧 Исправление зависимостей для старых серверов..."

# Проверяем версию OpenSSL
echo "📋 Информация о системе:"
echo "OpenSSL version: $($PYTHON_CMD -c "import ssl; print(ssl.OPENSSL_VERSION)")"
echo "Python version: $($PYTHON_CMD --version)"

# Удаляем все проблемные пакеты
echo "🗑️ Удаление несовместимых пакетов..."
$PIP_CMD uninstall urllib3 requests certifi charset-normalizer idna -y

# Устанавливаем совместимые версии в правильном порядке
echo "📦 Установка совместимых версий пакетов..."

# Сначала устанавливаем базовые зависимости
$PIP_CMD install "certifi>=2023.0.0"
$PIP_CMD install "charset-normalizer>=3.0.0"
$PIP_CMD install "idna>=3.0"

# Устанавливаем urllib3 без зависимостей
$PIP_CMD install --no-deps "urllib3==1.26.20"

# Устанавливаем requests без автоматического обновления зависимостей
$PIP_CMD install --no-deps "requests>=2.31.0"

# Проверяем что всё работает
echo "✅ Тестирование импорта..."
if $PYTHON_CMD -c "import urllib3; print('urllib3 version:', urllib3.__version__)"; then
    echo "✅ urllib3 импортируется успешно"
else
    echo "❌ Проблемы с urllib3"
    exit 1
fi

if $PYTHON_CMD -c "import requests; print('requests version:', requests.__version__)"; then
    echo "✅ requests импортируется успешно"
else
    echo "❌ Проблемы с requests"
    exit 1
fi

if $PYTHON_CMD -c "import requests; import urllib3; print('✅ Все модули работают вместе')"; then
    echo "🎉 Проблема с зависимостями исправлена!"
else
    echo "❌ Всё ещё есть проблемы с совместимостью"
    exit 1
fi

# Показываем установленные версии
echo "📊 Установленные версии:"
$PIP_CMD list | grep -E "(urllib3|requests|certifi|charset-normalizer|idna)"

echo "🚀 Теперь можно запускать autoposter!" 