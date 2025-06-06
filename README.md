# AutoPoster - Автоматическая система публикации контента

Система автоматической генерации и публикации статей с изображениями в WordPress и Telegram.

## 🚀 Быстрый старт

### Установка зависимостей

```bash
# Основные зависимости
pip install -r requirements.txt

# Для разработки (включает инструменты тестирования и анализа)
pip install -r requirements-dev.txt
```

### Конфигурация

1. Скопируйте `config.json.example` в `config.json`
2. Заполните необходимые настройки:

```json
{
    "wordpress": {
        "url": "https://your-site.com",
        "user": "your_username",
        "password": "your_app_password",
        "category_id": 50,
        "timeout": 30
    },
    "telegram": {
        "token": "your_bot_token",
        "chat_id": "your_chat_id",
        "timeout": 30,
        "image_timeout": 60,
        "format": {
            "max_length": 800,
            "prefix": "🌐 GVN ",
            "suffix": "• More at GVN.biz •"
        }
    },
    "gpt": {
        "api_key": "your_api_key",
        "url": "https://api.vsegpt.ru/v1"
    },
    "publishing": {
        "posts_per_day": 3,
        "publish_window": [8, 20],
        "interval_min": 1800,
        "interval_max": 10800,
        "post_delay": 60,
        "cycle_restart_delay": 60
    },
    "logging": {
        "max_file_size": 10485760,
        "backup_count": 5,
        "encoding": "utf-8"
    },
    "system": {
        "check_interval": 60,
        "image_base_path": "./img"
    }
}
```

**📋 Полное описание всех параметров конфигурации:** см. [CONFIGURATION.md](CONFIGURATION.md)

## 📖 Использование

### Команды

```bash
# Опубликовать одну статью
python autoposter.py once

# Запустить в режиме демона (по расписанию)
python autoposter.py start

# Остановить демон
python autoposter.py stop

# Посмотреть статистику за сегодня
python autoposter.py status

# Сбросить историю публикаций за сегодня
python autoposter.py reset_today

# Показать справку
python autoposter.py help
```

## 🛠️ Настройка публикации

Все параметры публикации теперь настраиваются в `config.json`:

- **posts_per_day** - количество постов в день
- **publish_window** - временное окно публикации (в часах)  
- **interval_min/max** - интервалы между публикациями
- **post_delay** - задержка после публикации
- **check_interval** - интервал проверки команд

Система обеспечивает обратную совместимость - если параметры отсутствуют, используются разумные значения по умолчанию.

## 🖼️ Работа с изображениями

Система автоматически:
- Ищет изображения товаров по артикулам в папке `img/`
- Добавляет водяные знаки
- Загружает на WordPress как Featured Image
- Отправляет в Telegram

## 📁 Структура проекта

```
autoposter/
├── autoposter.py          # Основной скрипт
├── utils.py              # Утилиты и основная логика
├── config.json           # Конфигурация (создать вручную)
├── config.json.example   # Пример конфигурации
├── CONFIGURATION.md      # Подробное описание всех настроек
├── theme_host.json       # Темы для статей
├── requirements.txt      # Основные зависимости
├── requirements-dev.txt  # Зависимости для разработки
├── img/                  # Изображения товаров по брендам
│   ├── ABB/
│   ├── Siemens/
│   └── ...
├── wordpress_client.py   # Клиент WordPress API
├── vsegpt_client.py     # Клиент GPT API
└── db_manager.py        # Управление базой данных
```

## 🔧 Системные требования

- Python 3.8+
- Свободное место: ~100MB (для базы данных и изображений)
- Доступ к интернету для API запросов

## 🌐 Развертывание на хостинге

См. подробные инструкции в разделе deployment документации.

## 📝 Лицензия

MIT License - см. файл LICENSE для деталей. 