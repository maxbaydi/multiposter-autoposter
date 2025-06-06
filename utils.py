# -*- coding: utf-8 -*-
import random
import requests
from datetime import datetime
from db_manager import DBManager
from wordpress_client import WordPressClient
from vsegpt_client import VseGPTClient
import re
import json
import os
import html
import glob
import sys
from watermark import add_image_watermark

def find_product_image(brand, text, img_base_path=None):
    """
    Ищет изображение товара по артикулу в тексте темы/сабтемы
    
    Args:
        brand: название бренда
        text: текст темы или сабтемы где ищем артикул
        img_base_path: базовый путь к папке с изображениями
    
    Returns:
        Путь к найденному изображению или None
    """
    if img_base_path is None:
        # Используем путь относительно корня проекта (BASE_DIR)
        img_base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'img'))
    
    # Нормализуем название бренда для поиска папки
    brand_variations = {
        'Allen Bradley': 'Allen-Bradley',
        'Pepperl+Fuchs': 'PEPPERL+FUCHS',
        'Honeywell': 'honeywell'
    }
    
    folder_brand = brand_variations.get(brand, brand)
    brand_folder = os.path.join(img_base_path, folder_brand)
    
    if not os.path.exists(brand_folder):
        print("Папка бренда не найдена: " + str(brand_folder) + "")
        return None
    
    # Извлекаем возможные артикулы из текста
    # Ищем различные форматы артикулов
    article_patterns = [
        r'[0-9][A-Z]{2,}[0-9]{6,}[A-Z][0-9]{4}',  # Формат ABB: 1SCA138208R1001
        r'[A-Z]{2}[0-9]{3}[A-Z][0-9]{2}[A-Z]',  # Формат: OT160G03K
        r'[0-9][A-Z]{3}[0-9]{8}[A-Z][0-9]{3,4}',  # Расширенный формат ABB
        r'[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+',  # Формат с дефисами: ABC-123-XYZ
        r'[A-Z]{2,4}[0-9]{4,8}[A-Z]{1,3}[0-9]{1,4}',  # Общий формат для промышленных артикулов
        r'[0-9]{4,}[A-Z]{2,}[0-9]{2,}',  # Формат: 1234AB56
        r'[A-Z]{3,}[0-9]{5,}',  # Формат: ABC12345
        r'[A-Z]{2,4}[0-9]{2,4}[A-Z]{1,3}',  # Формат RXG22BD: буквы+цифры+буквы
        r'[A-Z0-9]{5,}'  # Общий формат артикулов от 5 символов
    ]
    
    found_articles = []
    for pattern in article_patterns:
        matches = re.findall(pattern, text.upper())
        found_articles.extend(matches)
    
    # Убираем дубликаты и сортируем по длине (длинные артикулы более точные)
    found_articles = list(set(found_articles))
    found_articles.sort(key=len, reverse=True)
    
    # Фильтруем слишком общие слова и короткие артикулы
    filtered_articles = []
    common_words = ['EVERYTHING', 'FEATURES', 'BENEFITS', 'THROUGH', 'SWITCH', 'ABOUT', 'NEED', 'KNOW', 'ELECTRIC', 'SCHNEIDER']
    for article in found_articles:
        if article not in common_words and len(article) >= 5:  # Минимальная длина артикула уменьшена до 5
            filtered_articles.append(article)
    
    print("Найденные артикулы: " + str(filtered_articles) + "")
    
    # Ищем изображения для каждого найденного артикула
    for article in filtered_articles:
        # Поддерживаемые форматы изображений (в разных регистрах)
        image_extensions = [
            '.jpg', '.JPG', '.jpeg', '.JPEG',  # JPEG форматы
            '.png', '.PNG',                    # PNG формат
            '.webp', '.WEBP',                 # WebP формат
            '.gif', '.GIF',                   # GIF формат
            '.bmp', '.BMP',                   # BMP формат
            '.tiff', '.TIFF', '.tif', '.TIF', # TIFF форматы
            '.svg', '.SVG',                   # SVG векторный формат
            '.avif', '.AVIF',                 # AVIF формат
            '.heic', '.HEIC', '.heif', '.HEIF' # HEIC/HEIF форматы (Apple)
        ]
        
        # Ищем точное совпадение в разных форматах
        for extension in image_extensions:
            image_pattern = os.path.join(brand_folder, str(article) + "-itexport" + extension)
            if os.path.exists(image_pattern):
                print("✅ Найдено изображение: " + str(os.path.basename(image_pattern)) + "")
                return image_pattern
        
        # Ищем частичное совпадение в разных форматах
        for extension in image_extensions:
            search_pattern = os.path.join(brand_folder, "*" + str(article) + "*-itexport" + extension)
            matches = glob.glob(search_pattern)
            if matches:
                print("✅ Найдено изображение (частичное): " + str(os.path.basename(matches[0])) + "")
                return matches[0]
        
        # Ищем совпадение без дефисов в разных форматах
        article_no_dash = article.replace('-', '')
        for extension in image_extensions:
            search_pattern = os.path.join(brand_folder, "*" + str(article_no_dash) + "*-itexport" + extension)
            matches = glob.glob(search_pattern)
            if matches:
                print("✅ Найдено изображение (без дефисов): " + str(os.path.basename(matches[0])) + "")
                return matches[0]
    
    print("Изображение для бренда " + str(brand) + " не найдено")
    return None

def extract_article_from_topic(topic):
    """
    Извлекает артикул из темы статьи
    """
    # Ищем артикулы в различных форматах
    patterns = [
        r'([A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+)',
        r'([0-9]{2}[A-Z][0-9]{3}[A-Z][0-9]{2}[A-Z])',
        r'([A-Z]{2,}[0-9]{5,}[A-Z]{1,}[0-9]{1,})',
        r'([0-9]{1,}[A-Z]{1,}[A-Z0-9]{5,})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, topic.upper())
        if match:
            return match.group(1)
    
    return None

def generate_telegram_hashtags(brand, topic, tags=None):
    """
    Генерирует хештеги для Telegram постов
    
    Args:
        brand: название бренда
        topic: тема статьи
        tags: строка тегов от GPT (через запятую)
    
    Returns:
        Строка с хештегами для Telegram
    """
    hashtags = []
    
    # 1. Первый тег: #бренд
    if brand:
        # Нормализуем название бренда для хештега
        brand_normalized = brand.replace(' ', '_').replace('&', 'and').replace('+', 'plus')
        hashtags.append("#" + str(brand_normalized) + "")
    
    # 2. Второй тег: #вид_товара
    product_type = None
    
    # Определяем вид товара из темы или тегов
    product_keywords = {
        'frequency_converters': ['frequency converter', 'drive', 'vfd', 'variable frequency', 'ACS', 'frequency drive'],
        'sensors': ['sensor', 'proximity', 'photoelectric', 'ultrasonic', 'laser', 'detection'],
        'safety_systems': ['safety', 'emergency stop', 'light curtain', 'safety relay', 'protective', 'safety systems'],
        'switches': ['switch', 'selector', 'button', 'emergency', 'limit switch', 'safety switch'],
        'controllers': ['controller', 'plc', 'programmable', 'logic controller', 'control system'],
        'communication': ['ethernet', 'profibus', 'profinet', 'modbus', 'communication', 'network'],
        'instrumentation': ['transmitter', 'measurement', 'pressure', 'temperature', 'level', 'flow'],
        'robotics': ['robot', 'robotic', 'automation', 'collaborative', 'industrial robot'],
        'power_supplies': ['power supply', 'ups', 'uninterruptible', 'power', 'electrical'],
        'valves': ['valve', 'pneumatic', 'hydraulic', 'actuator', 'control valve']
    }
    
    # Объединяем тему и теги для поиска ключевых слов
    search_text = (topic + ' ' + (tags or '')).lower()
    
    for category, keywords in product_keywords.items():
        if any(keyword.lower() in search_text for keyword in keywords):
            product_type = category
            break
    
    # Если не нашли специфичный тип, используем общий
    if not product_type:
        if any(word in search_text for word in ['automation', 'industrial', 'control']):
            product_type = 'automation_equipment'
        else:
            product_type = 'industrial_equipment'
    
    hashtags.append("#" + str(product_type) + "")
    
    # 3. Третий тег: #категория_товара
    category_keywords = {
        'process_automation': ['process', 'manufacturing', 'production', 'chemical', 'petrochemical', 'sensor', 'detection', 'proximity'],
        'factory_automation': ['factory', 'assembly', 'packaging', 'conveyor', 'manufacturing', 'plc', 'programmable', 'controller'],
        'building_automation': ['building', 'hvac', 'facility', 'smart building', 'energy management'],
        'motion_control': ['motion', 'servo', 'stepper', 'positioning', 'movement'],
        'safety_solutions': ['safety', 'protection', 'emergency', 'hazard', 'risk'],
        'energy_efficiency': ['energy', 'efficiency', 'consumption', 'saving', 'green'],
        'connectivity': ['communication', 'network', 'iot', 'digital', 'remote'],
        'maintenance': ['maintenance', 'diagnostic', 'monitoring', 'predictive', 'condition']
    }
    
    category = None
    for cat, keywords in category_keywords.items():
        if any(keyword.lower() in search_text for keyword in keywords):
            category = cat
            break
    
    # Если не нашли специфичную категорию, используем общую
    if not category:
        category = 'industrial_solutions'
    
    hashtags.append("#" + str(category) + "")
    
    # Возвращаем хештеги через пробел
    return ' '.join(hashtags)

def remove_duplicate_title_from_content(content, title):
    """
    Удаляет дублирующиеся заголовки из контента статьи
    
    Args:
        content: HTML контент статьи
        title: заголовок поста
    
    Returns:
        Очищенный от дублирующихся заголовков контент
    
    Примечание:
        Для хранения очищенного контента используется переменная content_cleaned (НЕ cleaned_content).
    """
    if not content or not title:
        return content
    
    # Нормализуем заголовок для сравнения (убираем лишние пробелы, приводим к нижнему регистру)
    title_normalized = ' '.join(title.split()).lower()
    
    # Паттерны для поиска заголовков в HTML
    header_patterns = [
        r'<h1[^>]*>(.*?)</h1>',  # <h1> теги
        r'<h2[^>]*>(.*?)</h2>',  # <h2> теги (на случай если ИИ использует h2 вместо h1)
    ]
    
    content_cleaned = content
    
    for pattern in header_patterns:
        # Находим все совпадения для текущего паттерна
        while True:
            match = re.search(pattern, content_cleaned, re.IGNORECASE | re.DOTALL)
            if not match:
                break
                
            header_content = match.group(1).strip()
            # Удаляем HTML теги из содержимого заголовка для сравнения
            header_text = re.sub(r'<[^>]+>', '', header_content).strip()
            header_text_normalized = ' '.join(header_text.split()).lower()
            
            # Проверяем различные варианты совпадения
            is_duplicate = (
                header_text_normalized == title_normalized or  # Точное совпадение
                header_text_normalized in title_normalized or  # Заголовок содержится в title
                title_normalized in header_text_normalized or  # Title содержится в заголовке
                # Проверяем совпадение без знаков препинания
                re.sub(r'[^\w\s]', '', header_text_normalized) == re.sub(r'[^\w\s]', '', title_normalized)
            )
            
            if is_duplicate:
                print("🔍 Найден дублирующийся заголовок: '" + str(header_text) + "' ≈ '{title}'")
                # Удаляем весь тег заголовка
                content_cleaned = content_cleaned.replace(match.group(0), '', 1)  # Удаляем только первое совпадение
                print("✅ Дублирующийся заголовок удален")
            else:
                # Если заголовок не дублирующийся, прерываем цикл для этого паттерна
                break
    
    # Удаляем лишние переносы строк и пробелы в начале
    content_cleaned = re.sub(r'^\s*(<br\s*/?>\s*)*', '', content_cleaned.strip())
    content_cleaned = re.sub(r'^(\s*<p>\s*</p>\s*)*', '', content_cleaned)
    
    if content_cleaned != content:
        print("📝 Контент очищен от дублирующихся заголовков")
    
    return content_cleaned

def load_themes(theme_file='theme_host.json'):
    with open(theme_file, 'r', encoding='utf-8') as f:
        # Исправляем возможные ошибки структуры (например, отсутствие фигурных скобок)
        text = f.read().strip()
        if not text.startswith('{'):
            text = '{' + text
        if not text.endswith('}'):  # если нет закрывающей скобки
            text = text + '}'
        return json.loads(text)

def load_tg_settings(settings_file='settings.json'):
    with open(settings_file, 'r', encoding='utf-8') as f:
        return json.load(f).get('telegram_settings', {})

def build_gpt_prompt(topic, image_urls=None, subtopics=None):
    images = ''
    if image_urls:
        images = '\n'.join(image_urls)
    subtopics_str = ''
    if subtopics:
        subtopics_str = '\nSubtopics to cover as sections in the article:\n' + '\n'.join('- ' + s for s in subtopics)
    return '''
You are an expert SEO copywriter.
Generate a full, SEO-optimized article in English for the topic: "''' + topic + '''".
Requirements:
- The article must be interesting, useful, and human-like, but first and foremost optimized for search engine ranking and SEO.
- Title: Create a compelling and SEO-friendly title (this will be used as the main page title, do NOT include it as <h1> in the body)
- Main body: HTML formatted content starting with <h2> subheadings, lists, etc. (NO <h1> tags in body content)
- Generate 5-7 relevant SEO tags that are:
  * Highly relevant to the content and topic
  * Mix of branded terms (company names) and technical/industry terms
  * Include main keywords from the article
  * Suitable for industrial automation/equipment audience
  * Format as comma-separated string (e.g., "automation, industrial control, ABB, process control, manufacturing")
- The article must be at least 800 words, but not more than 1200 words
- At the very end of the article, place the WordPress shortcode [wpforms id="8325"] right below it (the shortcode must be visible in the HTML).
- Write a short, catchy, creative Telegram summary with its own unique title that's different from the article title. The summary must be engaging, suitable for Telegram format, and fully formatted using HTML with explicit line breaks. Important:
  * Create a short, unique title specifically for the Telegram summary (don't reuse the article title)
  * The title should be concise and attention-grabbing, max 50 chars
  * Use ONLY these HTML tags supported by Telegram: <b>, <i>, <u>, <s>, <a>, <code>, <pre>
  * DO NOT use <ul>, <li>, <br>, <p> tags - Telegram doesn't support them
  * Add explicit line breaks using "\\n" character, not <br> tags
  * Use emoji icons at the beginning of important points
  * Format important points as bullet lists using "•" symbol with proper indentation
  * Use <b>bold</b> for headings and important terms
  * Use <i>italic</i> for emphasis
  * Structure the text with clear sections and spaces between them
  * Maximum 500 characters
  * Example format for Telegram:
    <b>Short Catchy Title</b>\\n\\n📌 <b>Key Point 1:</b>\\n• Feature one\\n• Feature two\\n\\n⚡️ <b>Key Point 2:</b>\\n• Another important detail

- Output strictly in the following JSON format:
{{
  "title": "...",
  "body": "...",
  "tags": "tag1, tag2, tag3, tag4, tag5",
  "telegram_summary": "...",
  "telegram_title": "..." 
}}
''' + subtopics_str

def format_telegram_summary(summary, tg_config, title=None, url=None, hashtags=None):
    """
    Форматирует сообщение для Telegram с учетом настроек форматирования
    
    Args:
        summary: Текст сообщения
        tg_config: Конфигурация Telegram из config.json
        title: Заголовок сообщения (если не указан, используется из summary)
        url: URL для ссылки (если не указан, используется из конфигурации)
        hashtags: Строка с хештегами для добавления в конец сообщения
    
    Returns:
        Отформатированный текст для публикации в Telegram
    """
    # Извлекаем настройки форматирования
    format_config = tg_config.get('format', {})
    prefix = format_config.get('prefix', '🌐 GVN ')
    suffix = format_config.get('suffix', '• More at GVN.biz •')
    default_url = format_config.get('default_url', 'https://gvn.biz/')
    emoji_styles = format_config.get('emoji_styles', ['🔹', '📌', '⚡️', '✅', '💡'])
    add_emoji_to_headings = format_config.get('add_emoji_to_headings', True)
    use_explicit_line_breaks = format_config.get('use_explicit_line_breaks', True)
    add_double_breaks = format_config.get('add_double_breaks_after_headings', True)
    bullet_symbol = format_config.get('bullet_symbol', '•')
    
    if url is None:
        url = default_url
    
    # Очищаем от некорректных HTML-тегов и сущностей
    text = summary.strip()
    
    # Проверяем, есть ли уже заголовок в тексте от ИИ
    title_match = re.search(r'<b>(.*?)</b>', text)
    has_ai_title = bool(title_match)
    
    # Заменяем HTML-сущности на символы
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    
    # Заменяем неподдерживаемые Telegram теги на поддерживаемые или удаляем их
    text = re.sub(r'<ul>|</ul>', '', text)  # Удаляем теги списков
    text = re.sub(r'<li>(.*?)</li>', bullet_symbol + ' \\1', text)  # Заменяем элементы списка на символы
    text = re.sub(r'<h[1-6]>(.*?)</h[1-6]>', '<b>\\1</b>', text)  # Заголовки на жирный текст
    
    # Обрабатываем теги параграфов и переносов строк только если включена соответствующая опция
    if use_explicit_line_breaks:
        text = re.sub(r'<p>(.*?)</p>', '\\1\n', text)  # Параграфы на текст с переносом строки
        text = re.sub(r'<br>|<br/>', '\n', text)  # Заменяем <br> на реальные переносы строк
    
    # Обеспечиваем, чтобы после каждого маркера списка был один пробел
    text = re.sub(bullet_symbol + '\\s*', bullet_symbol + ' ', text)
    
    # Удаляем двойные переносы строк (более 2-х подряд)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Обеспечиваем, чтобы после каждого заголовка был двойной перенос строки если включена опция
    if add_double_breaks:
        text = re.sub(r'(</b>)(\s*?)(?!\n\n)', '\\1\n\n', text)
    
    # Обеспечиваем, чтобы перед каждым маркером списка был перенос строки
    text = re.sub(r'([^\n])(\s*?)(' + re.escape(bullet_symbol) + r'\s)', '\\1\n\\3', text)
    
    # Добавляем эмодзи для ключевых пунктов, если включена опция
    if add_emoji_to_headings and emoji_styles:
        # Проверяем, есть ли уже эмодзи в тексте
        emoji_pattern = '|'.join(re.escape(emoji) for emoji in emoji_styles)
        if not re.search(emoji_pattern, text):
            # Выбираем первый эмодзи из списка для заголовков
            default_emoji = emoji_styles[0] if emoji_styles else '🔹'
            # Добавляем эмодзи только к заголовкам без них
            emoji_check = '|'.join(re.escape(emoji) for emoji in emoji_styles)
            text = re.sub(r'<b>(?!(' + emoji_check + r'))(.*?)</b>', default_emoji + ' <b>\\2</b>', text)
    
    # Формируем заголовок сообщения
    header = ""
    if title and not has_ai_title:
        # Добавляем программный заголовок только если в тексте нет заголовка от ИИ
        header = prefix + "<b>" + title + "</b>\n\n"
    elif not has_ai_title:
        # Если нет ни программного заголовка, ни заголовка от ИИ, используем только префикс
        header = prefix + "\n\n"
    else:
        # Если есть заголовок от ИИ, добавляем только префикс
        header = prefix
    
    # Добавляем хештеги к суффиксу если они есть
    final_suffix = suffix
    if hashtags:
        final_suffix = suffix + "\n\n" + hashtags
    
    # Форматируем итоговое сообщение: заголовок, текст и суффикс с хештегами
    formatted_text = header + text + "\n\n" + final_suffix
    
    return formatted_text

def normalize_title_for_comparison(title):
    """
    Нормализует заголовок для корректного сравнения
    
    Args:
        title: исходный заголовок
    
    Returns:
        Нормализованный заголовок для сравнения
    """
    if not title:
        return ""
    
    # Приводим к нижнему регистру
    normalized = title.lower()
    
    # Удаляем специальные кавычки и заменяем на обычные
    normalized = normalized.replace('«', '"').replace('»', '"')
    
    # Удаляем знаки препинания СНАЧАЛА
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Удаляем лишние пробелы
    normalized = ' '.join(normalized.split())
    
    # Удаляем дублирование слов подряд (например "switch switch" -> "switch")
    words = normalized.split()
    cleaned_words = []
    prev_word = None
    for word in words:
        # Добавляем слово только если оно отличается от предыдущего
        if word != prev_word:
            cleaned_words.append(word)
        prev_word = word
    normalized = ' '.join(cleaned_words)
    
    return normalized.strip()

def get_next_theme(themes, published_today):
    # Возвращает случайную неиспользованную тему (brand, title, subtopics)
    
    # Создаем множество опубликованных тем (исходные названия из файла)
    published_themes = set()
    for brand, title in published_today:
        published_themes.add((brand.lower(), title.lower()))
    
    # Собираем все доступные темы
    available_themes = []
    for brand, items in themes.items():
        for item in items:
            theme_title = item['title']
            theme_key = (brand.lower(), theme_title.lower())
            
            if theme_key not in published_themes:
                available_themes.append((brand, theme_title, item.get('subtopics', [])))
    
    if not available_themes:
        print("❌ Все темы уже опубликованы")
        return None, None, None
    
    # Выбираем случайную тему из доступных
    selected_theme = random.choice(available_themes)
    brand, title, subtopics = selected_theme
    
    print("🎲 Случайно выбрана тема: " + str(brand) + " - {title}")
    return brand, title, subtopics

def generate_post_from_theme(themes, published_today, gpt_config, tg_config, img_base_path=None):
    brand, topic, subtopics = get_next_theme(themes, published_today)
    if not brand or not topic:
        return None
    
    # Сохраняем исходное название темы из файла
    original_topic = topic
    
    # Ищем изображение для товара
    print("Ищем изображение для бренда: " + str(brand) + ", тема: {topic}")
    
    # Сначала ищем в теме статьи
    image_path = find_product_image(brand, topic, img_base_path=img_base_path)
    
    # Если не нашли в теме, ищем в сабтемах
    if not image_path and subtopics:
        for subtopic in subtopics:
            image_path = find_product_image(brand, subtopic, img_base_path=img_base_path)
            if image_path:
                break
    
    # Создаем копию с водяным знаком если изображение найдено
    watermarked_image_path = None
    if image_path:
        watermarked_image_path = create_watermarked_image(image_path)
        if watermarked_image_path:
            # Используем изображение с водяным знаком
            image_path = watermarked_image_path
        # Если не удалось создать водяной знак, используем оригинал
    
    gpt = VseGPTClient(gpt_config['api_key'], gpt_config['url'])
    prompt = build_gpt_prompt(topic, image_urls=None, subtopics=subtopics)
    gpt_resp = gpt.generate_article(topic, prompt=prompt)
    content = gpt_resp['choices'][0]['message']['content']
    
    # Обработка возможного маркера кода JSON
    if '```json' in content:
        # Извлекаем JSON между маркерами ```json и ```
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if json_match:
            json_str = json_match.group(1).strip()
            try:
                article = json.loads(json_str)
                # Используем специальный заголовок для телеграм, если есть
                telegram_title = article.get('telegram_title', '')
                summary = article.get('telegram_summary', '')
                
                # Если нет специального заголовка, ищем в summary
                if not telegram_title:
                    title_match = re.search(r'<b>(.*?)</b>', summary)
                    if title_match:
                        telegram_title = title_match.group(1)
                        # Не удаляем заголовок из summary - format_telegram_summary сам обработает дублирование
                    else:
                        telegram_title = "ABB Switch Insights"  # Дефолтный заголовок
                
                # Генерируем хештеги для Telegram
                hashtags = generate_telegram_hashtags(brand, topic, article.get('tags', ''))
                print("🏷️ Сгенерированы хештеги для Telegram: " + str(hashtags) + "")
                
                # Форматируем контент для телеграм с отдельным заголовком и хештегами
                tg_summary = format_telegram_summary(article.get('telegram_summary', ''), tg_config, title=telegram_title, hashtags=hashtags)
                return {
                    'brand': brand,
                    'original_topic': original_topic,  # Исходное название темы из файла
                    'title': article['title'],  # Сгенерированный GPT заголовок
                    'content': article['body'],
                    'tags': article.get('tags', ''),  # Добавляем теги из GPT ответа
                    'telegram_summary': tg_summary,
                    'telegram_title': telegram_title,  # Сохраняем заголовок отдельно
                    'image_path': image_path  # Добавляем путь к изображению
                }
            except json.JSONDecodeError:
                print('Ошибка при разборе JSON внутри маркеров кода')
    
    # Если не нашли JSON внутри маркеров, используем обычный поиск фигурных скобок
    json_start = content.find('{')
    json_end = content.rfind('}')
    if json_start != -1 and json_end != -1 and json_end > json_start:
        json_str = content[json_start:json_end+1]
        try:
            article = json.loads(json_str)
            # Используем специальный заголовок для телеграм, если есть
            telegram_title = article.get('telegram_title', '')
            summary = article.get('telegram_summary', '')
            
            # Если нет специального заголовка, ищем в summary
            if not telegram_title:
                title_match = re.search(r'<b>(.*?)</b>', summary)
                if title_match:
                    telegram_title = title_match.group(1)
                    # Не удаляем заголовок из summary - format_telegram_summary сам обработает дублирование
                else:
                    telegram_title = "ABB Switch Insights"  # Дефолтный заголовок
            
            # Генерируем хештеги для Telegram
            hashtags = generate_telegram_hashtags(brand, topic, article.get('tags', ''))
            print("🏷️ Сгенерированы хештеги для Telegram: " + str(hashtags) + "")
            
            # Форматируем контент для телеграм с отдельным заголовком и хештегами
            tg_summary = format_telegram_summary(article.get('telegram_summary', ''), tg_config, title=telegram_title, hashtags=hashtags)
            return {
                'brand': brand,
                'original_topic': original_topic,  # Исходное название темы из файла
                'title': article['title'],  # Сгенерированный GPT заголовок
                'content': article['body'],
                'tags': article.get('tags', ''),  # Добавляем теги из GPT ответа
                'telegram_summary': tg_summary,
                'telegram_title': telegram_title,  # Сохраняем заголовок отдельно
                'image_path': image_path  # Добавляем путь к изображению
            }
        except json.JSONDecodeError:
            print('Ошибка при разборе JSON между фигурными скобками')
    
    # Если не удалось найти корректный JSON
    print('GPT ответ:', content)
    raise Exception('Ошибка: не найден корректный JSON в ответе GPT')

def publish_to_wordpress(post, wp_config):
    try:
        # Создаем клиент WordPress с правильными параметрами
        client = WordPressClient(
            url=wp_config['url'],
            username=wp_config['user'],
            app_password=wp_config['password']
        )
        
        # Загружаем изображение если оно есть
        featured_media_id = None
        if post.get('image_path'):
            try:
                print("📤 Загружаем изображение: " + str(post['image_path']) + "")
                media_id, media_url = client.upload_media(post['image_path'], optimize=True)
                featured_media_id = media_id
                print("✅ Изображение загружено успешно. Media ID: " + str(media_id) + "")
            except Exception as e:
                print("❌ Ошибка при загрузке изображения: " + str(str(e)) + "")
                # Проверяем, связана ли ошибка с размером файла
                if "503" in str(e) or "Service Unavailable" in str(e):
                    print("🔄 Попробуем загрузить без оптимизации...")
                    try:
                        media_id, media_url = client.upload_media(post['image_path'], optimize=False)
                        featured_media_id = media_id
                        print("✅ Изображение загружено без оптимизации. Media ID: " + str(media_id) + "")
                    except Exception as e2:
                        print("❌ Повторная ошибка загрузки: " + str(str(e2)) + "")
                        print("📝 Продолжаем публикацию без изображения")
        
        # Определяем категорию (по умолчанию ID 50 для Industrial Brands)
        category_id = wp_config.get('category_id', 50)  # ID категории из конфигурации
        
        # Извлекаем теги из поста (теги могут быть в поле 'tags' или сгенерированы GPT)
        tags = post.get('tags', [])
        print("🔍 Исходные теги из поста: " + str(repr(tags)) + " (тип: {type(tags)})")
        
        if isinstance(tags, str):
            # Если теги - строка, разделяем по запятым
            tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
            print("🔍 Теги после разделения строки: " + str(tags) + "")
        
        # Если нет тегов, создаем базовые теги на основе бренда
        if not tags:
            brand = post.get('brand', '')
            tags = [
                brand,
                "" + str(brand) + " automation",
                "industrial equipment",
                "automation solutions",
                "industrial controls"
            ]
            tags = [tag for tag in tags if tag]  # Убираем пустые теги
            print("🔍 Использованы fallback теги: " + str(tags) + "")
        
        print("🏷️ Финальные теги для публикации: " + str(tags) + "")
        
        # Очищаем контент от дублирующихся заголовков
        cleaned_content = remove_duplicate_title_from_content(post['content'], post['title'])
        if cleaned_content != post['content']:
            print("📝 Контент очищен от дублирующихся заголовков")
        
        # Используем клиент для создания поста
        result = client.create_post(
            title=post['title'],
            content=cleaned_content,  # Используем очищенный контент
            status='publish',
            tags=tags,
            media_ids=featured_media_id,
            category_id=category_id
        )
        
        print("✅ Пост опубликован в WordPress: ID " + str(result['id']) + "")
        print("📂 Категория: " + str(category_id) + "")
        print("🏷️ Теги: " + str(len(tags)) + " шт.")
        if featured_media_id:
            print("🖼️ С изображением: ID " + str(featured_media_id) + "")
        
        return result
        
    except Exception as e:
        # Перехватываем и логируем ошибку, затем пробрасываем дальше
        print("❌ Ошибка при публикации в WordPress: " + str(str(e)) + "")
        # Детальная диагностика для ошибки 503
        if "503" in str(e) or "Service Unavailable" in str(e):
            print("🔍 Диагностика ошибки 503:")
            print("   • Сервер временно недоступен")
            print("   • Возможно превышены лимиты хостинга")
            print("   • Попробуйте позже или оптимизируйте изображения")
        raise

def publish_to_telegram(post, tg_config):
    # Получаем настройки таймаутов из конфигурации
    timeout = tg_config.get('timeout', 30)
    image_timeout = tg_config.get('image_timeout', 60)
    
    # Если есть изображение, используем sendPhoto, иначе sendMessage
    if post.get('image_path'):
        url = 'https://api.telegram.org/bot' + tg_config["token"] + '/sendPhoto'
    else:
        url = 'https://api.telegram.org/bot' + tg_config["token"] + '/sendMessage'
    
    # Получаем настройки форматирования из конфига
    format_config = tg_config.get('format', {})
    use_explicit_line_breaks = format_config.get('use_explicit_line_breaks', True)
    add_double_breaks = format_config.get('add_double_breaks_after_headings', True)
    bullet_symbol = format_config.get('bullet_symbol', '•')
    
    # Проверяем, есть ли готовый summary для Telegram
    if post.get('telegram_summary'):
        # Используем готовый summary без дополнительной обработки
        text = post.get('telegram_summary')
        parse_mode = 'HTML'  # Используем HTML-форматирование
    else:
        # Формируем базовое сообщение из заголовка и контента
        # Получаем сохраненный заголовок для Telegram
        telegram_title = post.get('telegram_title')
        if not telegram_title and post.get('title'):
            telegram_title = post.get('title')
            
        # Удаляем HTML-теги из текста
        content = re.sub(r'<.*?>', '', post.get('content', ''))
        
        # Генерируем хештеги для Telegram
        brand = post.get('brand', '')
        topic = post.get('title', '')
        tags = post.get('tags', '')
        hashtags = generate_telegram_hashtags(brand, topic, tags)
        print("🏷️ Сгенерированы хештеги для Telegram: " + str(hashtags) + "")
        
        # Форматируем текст с заголовком, контентом и хештегами
        text = format_telegram_summary(content, tg_config, title=telegram_title, hashtags=hashtags)
        parse_mode = 'HTML'
    
    # Заменяем HTML-сущности на символы
    text = html.unescape(text)
    
    # Очищаем текст от возможного дублирования суффикса
    # Получаем суффикс из конфигурации
    suffix = format_config.get('suffix', '• More at GVN.biz •')
    
    # Удаляем различные варианты суффикса (с точками и без)
    suffix_variants = [
        suffix,  # "• More at GVN.biz •"
        suffix.rstrip(' •'),  # "• More at GVN.biz"
        suffix.strip('• '),  # "More at GVN.biz"
        "More at GVN.biz",
        "• More at GVN.biz",
        "More at GVN.biz •"
    ]
    
    for variant in suffix_variants:
        text = text.replace(variant, '').strip()
    
    # Удаляем маркеры списка в конце текста
    text = re.sub(r'\n' + re.escape(bullet_symbol) + r'\s*$', '', text)
    
    # Удаляем лишние переносы строк в конце
    text = text.rstrip('\n ')
    
    # Добавляем суффикс в конце
    text = text + '\n\n' + suffix
    
    # Проверяем, что используются только поддерживаемые Telegram теги
    # Telegram поддерживает только <b>, <i>, <u>, <s>, <a>, <code>, <pre>
    # НЕ повторяем эту обработку, если уже был готовый summary
    if not post.get('telegram_summary'):
        # Заменяем неподдерживаемые теги
        text = re.sub(r'<ul>|</ul>', '', text)  # Удаляем теги списков
        text = re.sub(r'<li>(.*?)</li>', bullet_symbol + ' \\1', text)  # Заменяем элементы списка на символы
        text = re.sub(r'<h[1-6]>(.*?)</h[1-6]>', '<b>\\1</b>', text)  # Заголовки на жирный текст
        
        # Обрабатываем теги параграфов и переносов строк
        if use_explicit_line_breaks:
            text = re.sub(r'<br>|<br/>', '\n', text)  # Заменяем <br> на реальные переносы строк
            text = re.sub(r'<p>(.*?)</p>', '\\1\n', text)  # Параграфы на текст с переносом строки
        
        # Удаляем двойные переносы строк (более 2-х подряд)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Обеспечиваем, чтобы после каждого заголовка был двойной перенос строки
        if add_double_breaks:
            text = re.sub(r'(</b>)(\s*?)(?!\n\n)', '\\1\n\n', text)
        
        # Обеспечиваем, чтобы перед каждым маркером списка был перенос строки
        text = re.sub(r'([^\n])(\s*?)(' + re.escape(bullet_symbol) + r'\s)', '\\1\n\\3', text)
    
    # Исправляем незакрытые HTML теги
    text = fix_html_tags(text)
    
    # Подготавливаем данные для запроса
    if post.get('image_path'):
        # Отправляем фото с caption
        try:
            print("📤 Отправляем изображение в Telegram: " + str(os.path.basename(post['image_path'])) + "")
            print("📝 Длина текста: " + str(len(text)) + " символов")
            
            with open(post['image_path'], 'rb') as image_file:
                files = {'photo': image_file}
                data = {
                    'chat_id': tg_config['chat_id'],
                    'caption': text,
                    'parse_mode': parse_mode
                }
                response = requests.post(url, data=data, files=files, timeout=image_timeout)  # Используем image_timeout из конфига
                
                if response.status_code != 200:
                    print("❌ Ошибка Telegram API: " + str(response.status_code) + "")
                    print("Ответ: " + str(response.text) + "")
                    
                    # Специфичная обработка ошибок для изображений
                    try:
                        error_data = response.json()
                        error_description = error_data.get('description', 'Неизвестная ошибка')
                        print("📋 Описание ошибки: " + error_description)
                        
                        if 'file size' in error_description.lower():
                            print("⚠️ Размер файла превышает лимиты Telegram (макс. 50MB для фото)")
                        elif 'wrong file identifier' in error_description.lower():
                            print("⚠️ Неверный формат файла")
                        elif 'bad request' in error_description.lower():
                            print("⚠️ Некорректный запрос. Проверьте формат изображения")
                            
                    except (ValueError, KeyError):
                        pass
                
                response.raise_for_status()
                print("✅ Изображение отправлено в Telegram")
                return response.json()
        except requests.exceptions.Timeout:
            print("❌ Таймаут при отправке изображения в Telegram (превышено " + str(image_timeout) + " секунд)")
            print("🔄 Пробуем отправить как обычное текстовое сообщение...")
        except requests.exceptions.ConnectionError:
            print("❌ Ошибка соединения при отправке изображения в Telegram")
            print("🔄 Пробуем отправить как обычное текстовое сообщение...")
        except Exception as e:
            print("❌ Ошибка при отправке изображения в Telegram: " + str(e) + "")
            # Если не удалось отправить с изображением, отправляем как обычное сообщение
            print("🔄 Пробуем отправить как обычное текстовое сообщение...")
        
        # Fallback: отправляем как обычное текстовое сообщение
        url = 'https://api.telegram.org/bot' + tg_config["token"] + '/sendMessage'
        data = {
            'chat_id': tg_config['chat_id'],
            'text': text,
            'parse_mode': parse_mode
        }
    else:
        # Отправляем обычное текстовое сообщение
        print("📝 Отправляем текст в Telegram: " + str(len(text)) + " символов")
        data = {
            'chat_id': tg_config['chat_id'],
            'text': text,
            'parse_mode': parse_mode
        }
    
    try:
        response = requests.post(url, data=data, timeout=timeout)  # Используем timeout из конфига
        
        # Детальная проверка ответа
        if response.status_code != 200:
            print("❌ Ошибка Telegram API: " + str(response.status_code) + "")
            print("Ответ: " + str(response.text) + "")
            
            # Специфичная обработка ошибок Telegram API
            try:
                error_data = response.json()
                error_description = error_data.get('description', 'Неизвестная ошибка')
                print("📋 Описание ошибки: " + error_description)
                
                # Специальная обработка для разных типов ошибок
                if 'message is too long' in error_description.lower():
                    print("⚠️ Сообщение слишком длинное. Попробуйте сократить контент.")
                elif 'chat not found' in error_description.lower():
                    print("⚠️ Чат не найден. Проверьте chat_id в конфигурации.")
                elif 'bot was blocked' in error_description.lower():
                    print("⚠️ Бот заблокирован пользователем.")
                elif 'forbidden' in error_description.lower():
                    print("⚠️ Недостаточно прав. Проверьте токен бота.")
                    
            except (ValueError, KeyError):
                # Если не удалось разобрать JSON ответ
                pass
        
        response.raise_for_status()
        print("✅ Сообщение отправлено в Telegram")
        return response.json()
    except requests.exceptions.Timeout:
        print("❌ Таймаут при отправке в Telegram (превышено " + str(timeout) + " секунд)")
        raise Exception("Telegram API timeout")
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка соединения с Telegram API")
        raise Exception("Telegram API connection error")
    except Exception as e:
        print("❌ Ошибка при публикации в Telegram: " + str(e) + "")
        # Если ошибка связана с HTML-форматированием, пробуем отправить без форматирования
        if "can't parse entities" in str(e).lower() or "bad request" in str(e).lower():
            try:
                print("🔄 Пробуем отправить без HTML-форматирования...")
                # Удаляем все HTML-теги и пробуем отправить обычный текст
                clean_text = re.sub(r'<.*?>', '', text)
                data = {
                    'chat_id': tg_config['chat_id'],
                    'text': clean_text
                    # Убираем parse_mode для отправки обычного текста
                }
                response = requests.post(url, data=data, timeout=timeout)
                response.raise_for_status()
                print("✅ Сообщение отправлено без HTML-форматирования")
                return response.json()
            except Exception as e2:
                print("❌ Повторная ошибка при публикации в Telegram: " + str(e2) + "")
                raise e2
        raise

def add_publication_history(db_path, brand, topic, platform, status):
    db = DBManager(db_path)
    db.add_publication_history(brand, topic, platform, status)

def create_watermarked_image(image_path, watermark_path=None):
    """
    Создает копию изображения с водяным знаком
    
    Args:
        image_path: путь к оригинальному изображению
        watermark_path: путь к файлу водяного знака (если None, используется автопоиск)
    
    Returns:
        Путь к изображению с водяным знаком или None при ошибке
    """
    try:
        # Создаем путь для изображения с водяным знаком
        base_name = os.path.splitext(image_path)[0]
        extension = os.path.splitext(image_path)[1]
        watermarked_path = base_name + "_wm" + extension
        
        # Добавляем водяной знак (watermark_path=None означает автопоиск)
        result_path = add_image_watermark(
            input_image_path=image_path,
            output_image_path=watermarked_path,
            watermark_path=watermark_path,  # None для автопоиска
            position=(10, 10),  # Левый верхний угол
            opacity=180,  # Умеренная прозрачность
            watermark_scale=0.25  # 25% от ширины изображения
        )
        
        print("✅ Водяной знак добавлен: " + str(os.path.basename(watermarked_path)) + "")
        return result_path
        
    except Exception as e:
        print("❌ Ошибка при создании водяного знака: " + str(str(e)) + "")
        return None

def fix_html_tags(text):
    """
    Исправляет незакрытые HTML теги в тексте
    """
    # Стек для отслеживания открытых тегов
    open_tags = []
    
    # Находим все теги в тексте
    tag_pattern = r'<(/?)([a-zA-Z]+)(?:\s[^>]*)?>|<(/?)([a-zA-Z]+)>'
    matches = list(re.finditer(tag_pattern, text))
    
    for match in matches:
        is_closing1, tag_name1, is_closing2, tag_name2 = match.groups()
        is_closing = is_closing1 or is_closing2
        tag_name = tag_name1 or tag_name2
        
        if is_closing:
            # Закрывающий тег
            if open_tags and open_tags[-1] == tag_name:
                open_tags.pop()
        else:
            # Открывающий тег
            if tag_name in ['b', 'i', 'u', 's', 'code', 'pre']:  # Поддерживаемые Telegram теги
                open_tags.append(tag_name)
    
    # Закрываем все незакрытые теги
    for tag in reversed(open_tags):
        text += '</' + tag + '>'
    
    return text 