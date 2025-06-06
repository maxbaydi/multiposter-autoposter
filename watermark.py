#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для добавления водяных знаков на изображения
"""

import os
from PIL import Image, ImageDraw, ImageFont
import shutil

def add_image_watermark(input_image_path, output_image_path, watermark_path=None, 
                       position=(10, 10), opacity=180, watermark_scale=0.25):
    """
    Добавляет водяной знак на изображение
    
    Args:
        input_image_path: путь к исходному изображению
        output_image_path: путь для сохранения результата
        watermark_path: путь к файлу водяного знака (если None, ищет watermark_gvnbiz_2.png в текущей папке)
        position: позиция водяного знака (x, y)
        opacity: прозрачность (0-255)
        watermark_scale: масштаб водяного знака относительно изображения
    
    Returns:
        путь к файлу с водяным знаком
    """
    try:
        # Если путь к водяному знаку не указан, ищем стандартный файл
        if watermark_path is None:
            # Получаем путь к текущей директории (где находится watermark.py)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            watermark_path = os.path.join(current_dir, 'watermark_gvnbiz_2.png')
            print(f"Ищем водяной знак: {watermark_path}")
        
        # Если водяного знака нет, просто копируем файл
        if not os.path.exists(watermark_path):
            print(f"Водяной знак не найден: {watermark_path}")
            print("Файл будет скопирован без водяного знака")
            shutil.copy2(input_image_path, output_image_path)
            return output_image_path
        
        print(f"Используем водяной знак: {os.path.basename(watermark_path)}")
        
        # Открываем основное изображение
        with Image.open(input_image_path) as base_image:
            # Конвертируем в RGBA для работы с прозрачностью
            if base_image.mode != 'RGBA':
                base_image = base_image.convert('RGBA')
            
            # Открываем водяной знак
            with Image.open(watermark_path) as watermark:
                # Конвертируем водяной знак в RGBA
                if watermark.mode != 'RGBA':
                    watermark = watermark.convert('RGBA')
                
                # Вычисляем размер водяного знака
                base_width, base_height = base_image.size
                watermark_width = int(base_width * watermark_scale)
                watermark_height = int(watermark_width * watermark.size[1] / watermark.size[0])
                
                print(f"Размер изображения: {base_width}x{base_height}")
                print(f"Размер водяного знака: {watermark_width}x{watermark_height}")
                
                # Изменяем размер водяного знака
                watermark = watermark.resize((watermark_width, watermark_height), Image.Resampling.LANCZOS)
                
                # Создаем слой для водяного знака с прозрачностью
                transparent = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
                transparent.paste(watermark, position, watermark)
                
                # Применяем прозрачность
                alpha = transparent.split()[-1]
                alpha = alpha.point(lambda p: int(p * opacity / 255.0))
                transparent.putalpha(alpha)
                
                # Накладываем водяной знак на основное изображение
                result = Image.alpha_composite(base_image, transparent)
                
                # Конвертируем обратно в RGB если нужно
                if input_image_path.lower().endswith(('.jpg', '.jpeg')):
                    result = result.convert('RGB')
                
                # Сохраняем результат
                result.save(output_image_path, quality=95)
                
        print(f"✅ Водяной знак добавлен: {os.path.basename(output_image_path)}")
        return output_image_path
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении водяного знака: {e}")
        # В случае ошибки копируем оригинал
        try:
            shutil.copy2(input_image_path, output_image_path)
            print(f"📄 Файл скопирован без водяного знака: {os.path.basename(output_image_path)}")
        except Exception as copy_error:
            print(f"❌ Ошибка при копировании файла: {copy_error}")
        return output_image_path

def create_text_watermark(input_image_path, output_image_path, text="GVN.biz", 
                         position=None, font_size=None, opacity=128):
    """
    Добавляет текстовый водяной знак на изображение
    
    Args:
        input_image_path: путь к исходному изображению
        output_image_path: путь для сохранения результата
        text: текст водяного знака
        position: позиция текста (x, y), если None - правый нижний угол
        font_size: размер шрифта, если None - автоматически
        opacity: прозрачность (0-255)
    
    Returns:
        путь к файлу с водяным знаком
    """
    try:
        with Image.open(input_image_path) as base_image:
            # Конвертируем в RGBA
            if base_image.mode != 'RGBA':
                base_image = base_image.convert('RGBA')
            
            # Создаем слой для текста
            txt_layer = Image.new('RGBA', base_image.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(txt_layer)
            
            # Определяем размер шрифта
            if font_size is None:
                font_size = max(20, base_image.size[0] // 40)
            
            try:
                # Пытаемся загрузить системный шрифт
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                except:
                    # Используем шрифт по умолчанию
                    font = ImageFont.load_default()
            
            # Получаем размеры текста
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Определяем позицию
            if position is None:
                # Правый нижний угол с отступом
                x = base_image.size[0] - text_width - 20
                y = base_image.size[1] - text_height - 20
                position = (x, y)
            
            # Рисуем текст с тенью для лучшей видимости
            shadow_offset = 2
            draw.text((position[0] + shadow_offset, position[1] + shadow_offset), 
                     text, font=font, fill=(0, 0, 0, opacity // 2))
            draw.text(position, text, font=font, fill=(255, 255, 255, opacity))
            
            # Накладываем текстовый слой
            result = Image.alpha_composite(base_image, txt_layer)
            
            # Конвертируем обратно в RGB если нужно
            if input_image_path.lower().endswith(('.jpg', '.jpeg')):
                result = result.convert('RGB')
            
            # Сохраняем результат
            result.save(output_image_path, quality=95)
        
        print(f"✅ Текстовый водяной знак добавлен: {os.path.basename(output_image_path)}")
        return output_image_path
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении текстового водяного знака: {e}")
        # В случае ошибки копируем оригинал
        shutil.copy2(input_image_path, output_image_path)
        return output_image_path

def find_watermark_file():
    """
    Ищет файл водяного знака в различных местах
    
    Returns:
        путь к файлу водяного знака или None
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Возможные местоположения водяного знака
    possible_paths = [
        os.path.join(current_dir, 'watermark_gvnbiz_2.png'),
        os.path.join(current_dir, '..', 'images', 'watermarks', 'watermark_gvnbiz_2.png'),
        os.path.join(current_dir, 'watermarks', 'watermark_gvnbiz_2.png'),
        os.path.join(current_dir, 'img', 'watermark_gvnbiz_2.png')
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"🎯 Найден водяной знак: {path}")
            return path
    
    print("⚠️ Водяной знак не найден в стандартных местах")
    return None

if __name__ == "__main__":
    print("🌊 Модуль watermark загружен успешно")
    print("📁 Поиск водяного знака...")
    watermark_file = find_watermark_file()
    
    print("\n🛠️ Доступные функции:")
    print("- add_image_watermark(): добавляет изображение-водяной знак")
    print("- create_text_watermark(): добавляет текстовый водяной знак")
    print("- find_watermark_file(): находит файл водяного знака")
    
    if watermark_file:
        print(f"\n✅ Готов к работе с водяным знаком: {os.path.basename(watermark_file)}")
    else:
        print(f"\n⚠️ Поместите файл 'watermark_gvnbiz_2.png' в папку autoposter для использования водяных знаков") 