# 🤖 AutoPoster - Автоматическая система публикации контента

**AutoPoster** - это интеллектуальная система автоматической генерации и публикации технических статей с изображениями в WordPress и Telegram. Система специализируется на публикации контента о промышленной автоматизации и электронных компонентах.

## ✨ Основные возможности

- 🔄 **Автоматическая генерация контента** через GPT API
- 📝 **Публикация в WordPress** с автоматическим размещением изображений
- 📱 **Отправка в Telegram** с красивым форматированием
- 🖼️ **Автоматическое добавление водяных знаков** на изображения
- ⏰ **Гибкое планирование публикаций** по времени
- 📊 **Система мониторинга и логирования**
- 🔄 **Circuit Breaker** для обработки ошибок API
- 🎯 **Тематические публикации** на основе JSON-схем

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.8+
- Доступ к WordPress сайту с REST API
- Telegram бот и канал/чат
- API ключ от VseGPT или другого совместимого GPT сервиса

### Установка

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/your-username/autoposter.git
cd autoposter
```

2. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

3. **Настройте конфигурацию:**
```bash
cp config.json.example config.json
```

Отредактируйте `config.json` со своими данными:

```json
{
    "wordpress": {
        "url": "https://your-site.com",
        "user": "your_username", 
        "password": "your_app_password",
        "category_id": 50
    },
    "telegram": {
        "token": "your_bot_token",
        "chat_id": "your_chat_id"
    },
    "gpt": {
        "api_key": "your_api_key",
        "url": "https://api.vsegpt.ru/v1"
    }
}
```

### Использование

#### Разовая публикация
```bash
python autoposter.py once
```

#### Запуск в режиме демона
```bash
python autoposter.py start
```

#### Проверка статуса
```bash
python autoposter.py status
```

#### Остановка демона
```bash
python autoposter.py stop
```

## 📁 Структура проекта

```
autoposter/
├── 📄 autoposter.py          # Основной скрипт
├── 🔧 utils.py              # Утилиты и основная логика
├── ⚙️ config.json           # Конфигурация (создать вручную)
├── 📋 config.json.example   # Пример конфигурации
├── 🎨 theme_host.json       # Темы для статей
├── 📦 requirements.txt      # Зависимости
├── 🖼️ img/                  # Изображения товаров по брендам
│   ├── 🏭 ABB/
│   ├── ⚡ Siemens/
│   ├── 🤖 Mitsubishi/
│   └── 📊 ...
├── 🌐 wordpress_client.py   # Клиент WordPress API
├── 🧠 vsegpt_client.py     # Клиент GPT API
├── 💾 db_manager.py        # Управление базой данных
├── 💧 watermark.py         # Обработка водяных знаков
└── 📜 logs/                # Файлы логов
```

## ⚙️ Конфигурация

Полная документация по настройке доступна в [CONFIGURATION.md](CONFIGURATION.md).

### Основные параметры

- **posts_per_day**: Количество постов в день (по умолчанию: 3)
- **publish_window**: Временное окно публикации в часах [8, 20]  
- **interval_min/max**: Интервалы между публикациями в секундах
- **post_delay**: Задержка после публикации
- **check_interval**: Интервал проверки команд

### Настройка изображений

Система автоматически ищет изображения в папке `img/` по структуре:
```
img/
├── Бренд1/
│   ├── артикул1.jpg
│   └── артикул2.png
└── Бренд2/
    └── артикул3.gif
```

## 🎯 Генерация контента

Система использует тематические схемы из `theme_host.json` для генерации разнообразного контента:

- Технические статьи о промышленном оборудовании
- Описания электронных компонентов
- Обзоры автоматизации и IoT решений
- Новости индустрии

## 📊 Мониторинг и логирование

- **Rotating logs** с автоматической ротацией файлов
- **Health checks** для проверки состояния системы
- **Circuit breaker** для graceful handling API ошибок
- **Детальная статистика** публикаций

## 🔧 Расширенные возможности

### Circuit Breaker
Защита от перегрузки API с автоматическим восстановлением:
- Отслеживание ошибок WordPress и Telegram
- Временное отключение при превышении лимита ошибок
- Автоматическое восстановление через настраиваемые интервалы

### Graceful Shutdown
Корректная остановка демона с сохранением состояния:
- Обработка SIGTERM/SIGINT сигналов
- Завершение текущих операций
- Сохранение progress в базе данных

## 🚀 Развертывание

### Локальное развертывание
```bash
# Запуск в фоне
nohup python autoposter.py start > /dev/null 2>&1 &
```

### Systemd сервис (Linux)
```bash
sudo cp autoposter.service /etc/systemd/system/
sudo systemctl enable autoposter
sudo systemctl start autoposter
```

### Docker (опционально)
```dockerfile
FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "autoposter.py", "start"]
```

## 🤝 Развитие проекта

Мы приветствуем вклад в развитие проекта! Вы можете:

1. 🐛 Сообщать об ошибках через Issues
2. 💡 Предлагать новые функции
3. 🔄 Создавать Pull Requests
4. 📖 Улучшать документацию

### Требования для контрибьютеров

- Следовать PEP 8 стандартам
- Покрывать новый код тестами
- Обновлять документацию
- Использовать осмысленные commit сообщения

## 📋 TODO

- [ ] Веб-интерфейс для управления
- [ ] Поддержка дополнительных социальных сетей
- [ ] Улучшенная система тегирования
- [ ] API для внешних интеграций
- [ ] Поддержка мультиязычности
- [ ] Система шаблонов для контента

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. Подробности в файле [LICENSE](LICENSE).

## 🆘 Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте [Issues](https://github.com/your-username/autoposter/issues)
2. Просмотрите документацию в папке проекта
3. Создайте новый Issue с детальным описанием

## 🏆 Благодарности

- VseGPT за API генерации контента
- WordPress за REST API
- Telegram за Bot API
- Всем контрибьютерам проекта

---

**AutoPoster** - делаем автоматизацию контента простой и эффективной! 🚀 