# Настройки конфигурации AutoPoster

## Обзор
Все настройки системы хранятся в файле `config.json`. Этот документ описывает все доступные параметры конфигурации.

## Структура конфигурации

### WordPress (`wordpress`)
Настройки для публикации в WordPress.

```json
{
  "wordpress": {
    "url": "https://your-wordpress-site.com",
    "user": "your-wordpress-username", 
    "password": "your-wordpress-app-password",
    "category_id": 50,
    "timeout": 30
  }
}
```

**Параметры:**
- `url` (строка) - URL вашего WordPress сайта
- `user` (строка) - имя пользователя WordPress
- `password` (строка) - пароль приложения WordPress (НЕ обычный пароль!)
- `category_id` (число) - ID категории для публикации постов (по умолчанию: 50)
- `timeout` (число) - таймаут для WordPress API в секундах (по умолчанию: 30)

### Telegram (`telegram`)
Настройки для публикации в Telegram.

```json
{
  "telegram": {
    "token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
    "chat_id": "-1001234567890",
    "timeout": 30,
    "image_timeout": 60,
    "format": {
      "max_length": 800,
      "prefix": "🌐 Your Brand ",
      "suffix": "• More at your-site.com •",
      "default_url": "https://your-site.com/",
      "emoji_styles": ["🔹", "📌", "⚡️", "✅", "💡", "🔥"],
      "add_emoji_to_headings": true,
      "use_explicit_line_breaks": true,
      "add_double_breaks_after_headings": true,
      "bullet_symbol": "•"
    }
  }
}
```

**Основные параметры:**
- `token` (строка) - токен Telegram бота
- `chat_id` (строка) - ID чата или канала для публикации
- `timeout` (число) - таймаут для текстовых сообщений в секундах (по умолчанию: 30)
- `image_timeout` (число) - таймаут для отправки изображений в секундах (по умолчанию: 60)

**Параметры форматирования (`format`):**
- `max_length` (число) - максимальная длина сообщения
- `prefix` (строка) - префикс добавляемый к сообщениям
- `suffix` (строка) - суффикс добавляемый к сообщениям
- `default_url` (строка) - URL по умолчанию
- `emoji_styles` (массив) - список эмодзи для заголовков
- `add_emoji_to_headings` (булево) - добавлять ли эмодзи к заголовкам
- `use_explicit_line_breaks` (булево) - использовать явные переносы строк
- `add_double_breaks_after_headings` (булево) - добавлять двойные переносы после заголовков
- `bullet_symbol` (строка) - символ для маркированных списков

### GPT (`gpt`)
Настройки для генерации контента.

```json
{
  "gpt": {
    "api_key": "sk-your-api-key-here",
    "url": "https://api.vsegpt.ru/v1"
  }
}
```

**Параметры:**
- `api_key` (строка) - API ключ для сервиса генерации
- `url` (строка) - URL API сервиса

### Публикация (`publishing`)
Настройки расписания и интервалов публикации.

```json
{
  "publishing": {
    "posts_per_day": 3,
    "publish_window": [8, 20],
    "interval_min": 1800,
    "interval_max": 10800,
    "post_delay": 60,
    "cycle_restart_delay": 60
  }
}
```

**Параметры:**
- `posts_per_day` (число) - количество постов в день (по умолчанию: 3)
- `publish_window` (массив) - окно публикации в часах [начало, конец] (по умолчанию: [8, 20])
- `interval_min` (число) - минимальный интервал между публикациями в секундах (по умолчанию: 1800 = 30 мин)
- `interval_max` (число) - максимальный интервал между публикациями в секундах (по умолчанию: 10800 = 3 часа)
- `post_delay` (число) - задержка после успешной публикации в секундах (по умолчанию: 60)
- `cycle_restart_delay` (число) - задержка перед перезапуском цикла при ошибке в секундах (по умолчанию: 60)

### Логирование (`logging`)
Настройки системы логирования.

```json
{
  "logging": {
    "max_file_size": 10485760,
    "backup_count": 5,
    "encoding": "utf-8"
  }
}
```

**Параметры:**
- `max_file_size` (число) - максимальный размер лог файла в байтах (по умолчанию: 10485760 = 10MB)
- `backup_count` (число) - количество резервных лог файлов (по умолчанию: 5)
- `encoding` (строка) - кодировка лог файлов (по умолчанию: "utf-8")

### Система (`system`)
Общие системные настройки.

```json
{
  "system": {
    "check_interval": 60,
    "image_base_path": "./img"
  }
}
```

**Параметры:**
- `check_interval` (число) - интервал проверки команд управления в секундах (по умолчанию: 60)
- `image_base_path` (строка) - путь к папке с изображениями (по умолчанию: "./img")

## Обратная совместимость

Все новые параметры конфигурации имеют значения по умолчанию. Если параметр отсутствует в `config.json`, будет использовано дефолтное значение. Это обеспечивает обратную совместимость с существующими конфигурациями.

## Примеры настройки

### Быстрая публикация (тестирование)
```json
{
  "publishing": {
    "posts_per_day": 12,
    "publish_window": [0, 23],
    "interval_min": 300,
    "interval_max": 900,
    "post_delay": 10,
    "cycle_restart_delay": 10
  }
}
```

### Консервативная публикация
```json
{
  "publishing": {
    "posts_per_day": 1,
    "publish_window": [9, 17],
    "interval_min": 3600,
    "interval_max": 7200,
    "post_delay": 120,
    "cycle_restart_delay": 300
  }
}
```

### Отладка с подробным логированием
```json
{
  "logging": {
    "max_file_size": 52428800,
    "backup_count": 10,
    "encoding": "utf-8"
  },
  "system": {
    "check_interval": 30
  }
}
``` 