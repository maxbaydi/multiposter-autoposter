# 🚀 Развертывание AutoPoster на хостинге reg.ru

## 📋 Предварительные требования

- Хостинг с поддержкой Python 3.8+
- SSH доступ к серверу
- ~100MB свободного места

## 🔧 Пошаговая установка

### 1. Подключение к серверу

```bash
# Подключаемся через SSH
ssh your_username@your_domain.ru

# Или используем SSH-клиент в панели управления reg.ru
```

### 2. Подготовка окружения

```bash
# Проверяем версию Python
python3 --version

# Если Python 3.8+ недоступен, устанавливаем:
# (для reg.ru shared hosting может потребоваться обращение в поддержку)

# Переходим в домашнюю директорию
cd ~

# Создаем директорию проекта
mkdir -p MultiPoster
cd MultiPoster
```

### 3. Загрузка файлов проекта

**Вариант A: Через FileManager в панели reg.ru**
1. Заархивируйте папку `autoposter` локально
2. Загрузите архив через веб-интерфейс reg.ru
3. Разархивируйте на сервере

**Вариант B: Через SCP**
```bash
# На локальном компьютере
scp -r autoposter your_username@your_domain.ru:~/MultiPoster/
```

**Вариант C: Ручное создание файлов**
```bash
# Создаем структуру
mkdir -p autoposter/img
cd autoposter

# Создаем основные файлы (копируем содержимое вручную)
nano autoposter.py
nano utils.py
nano config.json
# и т.д.
```

### 4. Установка зависимостей

```bash
cd ~/MultiPoster/autoposter

# Создаем виртуальное окружение
python3 -m venv venv

# Активируем окружение
source venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt
```

### 5. Настройка конфигурации

```bash
# Копируем пример конфигурации
cp config.json.example config.json

# Редактируем конфигурацию
nano config.json
```

Заполните настройки:
```json
{
    "wordpress": {
        "url": "https://www.gvn.biz",
        "user": "your_wp_user",
        "password": "your_wp_app_password"
    },
    "telegram": {
        "token": "your_bot_token",
        "chat_id": "your_chat_id",
        "format": {
            "max_length": 800,
            "prefix": "🌐 GVN ",
            "suffix": "• More at GVN.biz •"
        }
    },
    "gpt": {
        "api_key": "your_gpt_api_key",
        "url": "https://api.vsegpt.ru/v1"
    }
}
```

### 6. Загрузка изображений

```bash
# Создаем структуру для изображений
mkdir -p img/ABB img/Siemens img/Schneider\ Electric
# и т.д. для всех брендов

# Загружаем изображения товаров в соответствующие папки
# Структура: img/BRAND/ARTICLE-itexport.jpg
```

### 7. Настройка водяных знаков

```bash
# Создаем папку для водяных знаков
mkdir -p ../images/watermarks

# Загружаем файлы водяных знаков
# watermark_gvnbiz_2.png должен быть в ../images/watermarks/
```

### 8. Тестирование

```bash
# Активируем окружение
source venv/bin/activate

# Тестируем публикацию одного поста
python autoposter.py once

# Проверяем статус
python autoposter.py status
```

### 9. Настройка автозапуска

```bash
# Создаем скрипт запуска
cat > ~/MultiPoster/run_autoposter.sh << 'EOF'
#!/bin/bash
cd /home/your_username/MultiPoster/autoposter
source venv/bin/activate
python autoposter.py "$@"
EOF

# Делаем исполняемым
chmod +x ~/MultiPoster/run_autoposter.sh

# Настраиваем cron
crontab -e

# Добавляем задание (каждые 4 часа)
0 */4 * * * /home/your_username/MultiPoster/run_autoposter.sh once >> /home/your_username/autoposter.log 2>&1
```

### 10. Мониторинг

```bash
# Просмотр логов
tail -f ~/autoposter.log

# Проверка статуса
~/MultiPoster/run_autoposter.sh status

# Ручной запуск
~/MultiPoster/run_autoposter.sh once
```

## 🔧 Настройка прав доступа

```bash
# Права на исполнение
chmod +x ~/MultiPoster/autoposter/autoposter.py

# Права на папки
chmod -R 755 ~/MultiPoster/autoposter/img/
chmod -R 755 ~/MultiPoster/images/

# Права на базу данных
chmod 644 ~/MultiPoster/autoposter/autoposter.db
```

## ⚠️ Важные замечания для reg.ru

1. **Ограничения ресурсов**: На shared hosting ограничены CPU/Memory
2. **Время выполнения**: Скрипты могут быть завершены через 30-60 секунд
3. **Cron частота**: Не запускайте чаще чем раз в час
4. **Логи**: Следите за размером лог-файлов
5. **Python версия**: Убедитесь что доступен Python 3.8+

## 🐛 Решение проблем

### Ошибка "Python не найден"
```bash
# Попробуйте разные варианты
python --version
python3 --version
python3.8 --version
python3.9 --version
```

### Ошибка прав доступа
```bash
chmod -R 755 ~/MultiPoster/
chown -R your_username:your_username ~/MultiPoster/
```

### Проблемы с pip
```bash
# Обновите pip
python3 -m pip install --upgrade pip

# Установите зависимости с --user
pip install --user -r requirements.txt
```

### Ошибки с изображениями
```bash
# Проверьте права на папки
ls -la img/
chmod -R 755 img/
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `tail -50 ~/autoposter.log`
2. Запустите в режиме отладки: `python autoposter.py once`
3. Проверьте конфигурацию: `cat config.json`

## 🎯 Альтернатива - VPS

Для более стабильной работы рассмотрите VPS на reg.ru:
- Полный контроль над системой
- Возможность запуска как daemon
- Больше ресурсов
- Права root 