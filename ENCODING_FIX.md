# ✅ Исправление проблем с кодировкой UTF-8

## Проблема
При запуске на сервере с Python 3.8 возникала ошибка кодировки:
```
SyntaxError: Non-ASCII character '\xd0' in file /var/www/u2946491/data/autoposter/utils.py on line 20, but no encoding declared; see http://www.python.org/peps/pep-0263.html for details
```

## Причина
В файлах Python использовались кириллические символы (русские комментарии), но не была объявлена кодировка UTF-8.

## Решение
Добавлено объявление кодировки UTF-8 во все Python файлы с кириллическими символами:

### Исправленные файлы:
```bash
# Добавлена строка: # -*- coding: utf-8 -*-

✅ utils.py              - основной модуль с кириллическими комментариями
✅ wordpress_client.py   - комментарии к функциям на русском
✅ check_db.py          - вывод сообщений на русском
✅ vsegpt_client.py     - комментарии на русском
✅ watermark.py         - уже была кодировка
✅ autoposter.py        - уже была кодировка
```

### Формат объявления кодировки:
```python
# -*- coding: utf-8 -*-
import module_name
# ... остальной код
```

## Проверка исправления:
```bash
# Проверка синтаксиса всех файлов
python -m py_compile utils.py
python -m py_compile wordpress_client.py  
python -m py_compile check_db.py
python -m py_compile vsegpt_client.py
python -m py_compile autoposter.py

# Тестовый запуск
python autoposter.py help
python autoposter.py status
```

## Соответствие стандартам:
- ✅ Соответствует PEP 263 (Defining Python Source Code Encodings)
- ✅ Совместимо с Python 3.6+ 
- ✅ Работает на Linux/Windows серверах
- ✅ Корректная обработка кириллических символов

## Команда для деплоя на сервере:
```bash
cd autoposter
nohup python autoposter.py start > nohup.out 2>&1 &
```

**Статус:** ✅ Проблемы с кодировкой полностью устранены 