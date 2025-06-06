# -*- coding: utf-8 -*-
import requests
from requests.auth import HTTPBasicAuth
import os
from PIL import Image

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1"
}

class WordPressClient:
    def __init__(self, url, username, app_password):
        self.url = url.rstrip('/')
        self.auth = HTTPBasicAuth(username, app_password)

    def test_connection(self):
        r = requests.get(f'{self.url}/wp-json/wp/v2/posts', auth=self.auth, headers=BROWSER_HEADERS)
        return r.status_code == 200

    def optimize_image_for_upload(self, file_path, max_width=1920, max_height=1080, quality=85):
        """
        Оптимизирует изображение для загрузки, уменьшая размер если необходимо
        
        Args:
            file_path: путь к исходному изображению
            max_width: максимальная ширина
            max_height: максимальная высота 
            quality: качество JPEG (1-100)
            
        Returns:
            путь к оптимизированному изображению
        """
        try:
            with Image.open(file_path) as img:
                # Получаем размеры изображения
                width, height = img.size
                print(f"🖼️ Исходное изображение: {width}x{height}")
                
                # Проверяем, нужно ли уменьшать
                if width <= max_width and height <= max_height:
                    print("✅ Изображение уже оптимального размера")
                    return file_path
                
                # Вычисляем новые размеры с сохранением пропорций
                ratio = min(max_width/width, max_height/height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                
                print(f"🔄 Изменяем размер до: {new_width}x{new_height}")
                
                # Создаем путь для оптимизированного изображения
                base_name = os.path.splitext(file_path)[0]
                extension = os.path.splitext(file_path)[1]
                optimized_path = f"{base_name}_optimized{extension}"
                
                # Изменяем размер изображения
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Сохраняем с оптимизацией
                if extension.lower() in ['.jpg', '.jpeg']:
                    resized_img = resized_img.convert('RGB')
                    resized_img.save(optimized_path, 'JPEG', quality=quality, optimize=True)
                else:
                    resized_img.save(optimized_path, optimize=True)
                
                # Проверяем размер файла
                original_size = os.path.getsize(file_path)
                optimized_size = os.path.getsize(optimized_path)
                print(f"📊 Размер файла: {original_size/1024/1024:.1f}MB → {optimized_size/1024/1024:.1f}MB")
                
                return optimized_path
                
        except Exception as e:
            print(f"⚠️ Ошибка оптимизации изображения: {e}")
            return file_path

    def upload_media(self, file_path, optimize=True):
        """
        Загружает медиафайл в WordPress
        
        Args:
            file_path: путь к файлу
            optimize: оптимизировать изображение перед загрузкой
            
        Returns:
            tuple: (media_id, media_url)
        """
        upload_path = file_path
        
        # Оптимизируем изображение если включена оптимизация
        if optimize and file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            print("🔧 Оптимизируем изображение для загрузки...")
            upload_path = self.optimize_image_for_upload(file_path)
        
        try:
            with open(upload_path, 'rb') as f:
                filename = os.path.basename(upload_path)
                headers = BROWSER_HEADERS.copy()
                headers['Content-Disposition'] = f'attachment; filename={filename}'
                
                print(f"📤 Загружаем: {filename} ({os.path.getsize(upload_path)/1024/1024:.1f}MB)")
                
                r = requests.post(
                    f'{self.url}/wp-json/wp/v2/media',
                    headers=headers,
                    files={'file': (filename, f)},
                    auth=self.auth,
                    timeout=60  # Увеличиваем таймаут для больших файлов
                )
                
            if r.status_code in (200, 201):
                result = r.json()
                print(f"✅ Медиафайл загружен: ID {result['id']}")
                return result['id'], result['source_url']
            else:
                raise Exception(f'Upload failed: {r.status_code} - {r.text}')
                
        except requests.exceptions.Timeout:
            raise Exception('Upload timeout - файл слишком большой или медленное соединение')
        except requests.exceptions.RequestException as e:
            raise Exception(f'Network error during upload: {str(e)}')
        finally:
            # Удаляем оптимизированный файл если он был создан
            if upload_path != file_path and os.path.exists(upload_path):
                try:
                    os.remove(upload_path)
                    print("🗑️ Временный оптимизированный файл удален")
                except:
                    pass

    def create_or_get_tags(self, tag_names):
        """
        Создает теги или получает существующие
        
        Args:
            tag_names: список названий тегов
            
        Returns:
            список ID тегов
        """
        if not tag_names:
            return []
        
        tag_ids = []
        
        for tag_name in tag_names:
            # Ищем существующий тег
            search_response = requests.get(
                f'{self.url}/wp-json/wp/v2/tags',
                params={'search': tag_name, 'per_page': 1},
                auth=self.auth,
                headers=BROWSER_HEADERS
            )
            
            if search_response.status_code == 200:
                existing_tags = search_response.json()
                if existing_tags and existing_tags[0]['name'].lower() == tag_name.lower():
                    tag_ids.append(existing_tags[0]['id'])
                    print(f"🏷️ Найден существующий тег: {tag_name} (ID: {existing_tags[0]['id']})")
                    continue
            
            # Создаем новый тег
            try:
                create_response = requests.post(
                    f'{self.url}/wp-json/wp/v2/tags',
                    json={'name': tag_name, 'slug': tag_name.lower().replace(' ', '-').replace('/', '-')},
                    auth=self.auth,
                    headers={**BROWSER_HEADERS, 'Content-Type': 'application/json'}
                )
                
                if create_response.status_code in (200, 201):
                    new_tag = create_response.json()
                    tag_ids.append(new_tag['id'])
                    print(f"🆕 Создан новый тег: {tag_name} (ID: {new_tag['id']})")
                elif create_response.status_code == 400:
                    # Проверяем, есть ли ошибка о существующем теге
                    try:
                        error_data = create_response.json()
                        if error_data.get('code') == 'term_exists':
                            # Тег уже существует, получаем его ID
                            existing_tag_id = error_data.get('data', {}).get('term_id') or error_data.get('additional_data', [None])[0]
                            if existing_tag_id:
                                tag_ids.append(existing_tag_id)
                                print(f"🏷️ Найден существующий тег: {tag_name} (ID: {existing_tag_id})")
                            else:
                                print(f"⚠️ Тег {tag_name} уже существует, но не удалось получить ID")
                        else:
                            print(f"⚠️ Не удалось создать тег {tag_name}: {create_response.text}")
                    except:
                        print(f"⚠️ Не удалось создать тег {tag_name}: {create_response.text}")
                else:
                    print(f"⚠️ Не удалось создать тег {tag_name}: {create_response.text}")
                    
            except Exception as e:
                print(f"⚠️ Ошибка при создании тега {tag_name}: {e}")
                
        return tag_ids

    def create_post(self, title, content, status='publish', tags=None, media_ids=None, category_id=None):
        """
        Создает пост в WordPress
        
        Args:
            title: заголовок поста
            content: содержимое поста
            status: статус поста ('publish', 'draft')
            tags: список тегов (строки)
            media_ids: ID медиафайла для featured image
            category_id: ID категории
            
        Returns:
            объект созданного поста
        """
        data = {
            'title': title,
            'content': content,
            'status': status,
        }
        
        # Добавляем категорию
        if category_id:
            data['categories'] = [category_id]
            print(f"📂 Публикуем в категорию ID: {category_id}")
        
        # Обрабатываем теги
        if tags:
            if isinstance(tags, str):
                # Если теги переданы как строка, разделяем их
                tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            else:
                tag_list = tags
                
            tag_ids = self.create_or_get_tags(tag_list)
            if tag_ids:
                data['tags'] = tag_ids
                print(f"🏷️ Добавлены теги: {len(tag_ids)} шт.")
        
        # Добавляем featured image
        if media_ids:
            featured_id = media_ids[0] if isinstance(media_ids, list) else media_ids
            data['featured_media'] = featured_id
            print(f"🖼️ Установлен featured image: ID {featured_id}")
        
        headers = BROWSER_HEADERS.copy()
        headers['Content-Type'] = 'application/json'
        
        try:
            r = requests.post(
                f'{self.url}/wp-json/wp/v2/posts',
                json=data,
                auth=self.auth,
                headers=headers,
                timeout=60
            )
            
            if r.status_code in (200, 201):
                result = r.json()
                print(f"✅ Пост создан: ID {result['id']}, статус: {result['status']}")
                return result
            else:
                raise Exception(f'Post creation failed: {r.status_code} - {r.text}')
                
        except requests.exceptions.Timeout:
            raise Exception('Post creation timeout')
        except requests.exceptions.RequestException as e:
            raise Exception(f'Network error during post creation: {str(e)}')

    def get_categories(self):
        headers = BROWSER_HEADERS.copy()
        r = requests.get(
            f'{self.url}/wp-json/wp/v2/categories?per_page=100',
            auth=self.auth,
            headers=headers
        )
        if r.status_code == 200:
            return r.json()
        else:
            raise Exception(f'Failed to fetch categories: {r.text}')
            
    def test_api(self):
        """Тестовая функция для проверки соединения с WordPress REST API"""
        print(f"Тестирование подключения к {self.url}")
        print(f"Полный URL: {self.url}/wp-json/wp/v2/posts")
        
        # Без аутентификации
        print("\n1. Запрос без аутентификации:")
        r1 = requests.get(f'{self.url}/wp-json/wp/v2/posts', headers=BROWSER_HEADERS)
        print(f"Статус: {r1.status_code}")
        print(f"Ответ: {r1.text[:300]}...")
        
        # С аутентификацией
        print("\n2. Запрос с аутентификацией:")
        r2 = requests.get(f'{self.url}/wp-json/wp/v2/posts', auth=self.auth, headers=BROWSER_HEADERS)
        print(f"Статус: {r2.status_code}")
        print(f"Ответ: {r2.text[:300]}...")
        
        # Проверка URL без https:// префикса
        if self.url.startswith('https://'):
            fixed_url = self.url
            print("\n3. Проверка корректности URL:")
            print(f"Текущий URL: {self.url}")
            print(f"В коде URL соединяется как: https://{self.url}/wp-json/wp/v2/posts")
            print("Это может вызывать ошибку из-за дублирования https://")
            
        return r2.status_code == 200 