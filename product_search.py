import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Optional
import re
import globals as globals_module
from config import CHANNEL_ID

async def search_product_specs(product_name: str, category: str) -> Dict[str, str]:
    """
    Поиск характеристик товара в Telegram канале
    Если не находит или не подключен к каналу, возвращает пустые поля
    """
    specs = {}
    
    # Сначала пытаемся найти в Telegram канале
    if CHANNEL_ID and globals_module.bot:
        try:
            # Получаем категорию из БД для поиска category_id
            categories = await globals_module.db.get_categories()
            category_id = None
            
            # Маппинг ключей категорий
            category_key_map = {
                "android": "android",
                "apple": "apple",
                "laptop": "laptop", 
                "pc": "pc",
                "other": "other"
            }
            
            # Ищем по ключу категории
            for cat_id, cat_name, cat_emoji in categories:
                cat_key = category_key_map.get(category)
                if cat_key and (cat_key in cat_name.lower() or category in cat_name.lower()):
                    category_id = cat_id
                    break
            
            # Если не нашли, ищем по названию
            if not category_id:
                for cat_id, cat_name, cat_emoji in categories:
                    if category in cat_name.lower() or cat_name.lower() in category:
                        category_id = cat_id
                        break
            
            # Получаем характеристики для категории из БД
            if category_id:
                category_specs = await globals_module.db.get_category_specs(category_id)
                spec_names = [spec[1] for spec in category_specs]
            else:
                spec_names = []
            
            # Ищем в опубликованных постах в БД с похожим названием товара
            try:
                # Получаем все посты со статусом published из БД
                all_posts = []
                import aiosqlite
                import json
                async with aiosqlite.connect(globals_module.db.db_path) as db:
                    async with db.execute("""
                        SELECT post_text, specifications
                        FROM posts
                        WHERE status = 'published' AND category = ?
                        ORDER BY created_at DESC
                        LIMIT 50
                    """, (category,)) as cursor:
                        rows = await cursor.fetchall()
                        for row in rows:
                            try:
                                specs_json = json.loads(row[1]) if row[1] else {}
                            except:
                                specs_json = {}
                            all_posts.append({"text": row[0] or "", "specs": specs_json})
                
                # Ищем посты с похожим названием
                messages_text = ""
                for post in all_posts:
                    if post["text"] and product_name.lower() in post["text"].lower():
                        messages_text += post["text"] + "\n"
                        # Также пытаемся извлечь из specifications
                        if post["specs"]:
                            for spec_name, spec_value in post["specs"].items():
                                # Пропускаем служебные поля (начинающиеся с _)
                                if not spec_name.startswith("_") and spec_name not in specs and spec_value and spec_value != "Не указано" and spec_value.strip():
                                    specs[spec_name] = spec_value
                
                # Если нашли сообщения, пытаемся извлечь характеристики
                if messages_text:
                    # Извлекаем характеристики в зависимости от категории
                    if category in ["android", "apple"]:
                        found_specs = extract_phone_specs(messages_text, product_name)
                    elif category == "laptop":
                        found_specs = extract_laptop_specs(messages_text, product_name)
                    elif category == "pc":
                        found_specs = extract_pc_specs(messages_text, product_name)
                    else:
                        found_specs = extract_general_specs(messages_text, product_name)
                    
                    # Объединяем найденные характеристики
                    for key, value in found_specs.items():
                        if key not in specs or not specs[key]:
                            specs[key] = value
                    
                    # Заполняем пустые характеристики из списка категории
                    for spec_name in spec_names:
                        if spec_name not in specs:
                            specs[spec_name] = ""
            
            except Exception as e:
                # Если не удалось получить доступ к БД, просто продолжаем
                print(f"Не удалось получить доступ к БД: {e}")
        
        except Exception as e:
            print(f"Ошибка при поиске в канале: {e}")
    
    # Если не нашли характеристики, возвращаем базовые поля (пустые)
    if not specs:
        specs = get_default_specs(category)
    else:
        # Дополняем найденные характеристики пустыми полями из категории
        categories = await globals_module.db.get_categories()
        category_id = None
        for cat_id, cat_name, cat_emoji in categories:
            if category in cat_name.lower() or cat_name.lower() in category:
                category_id = cat_id
                break
        
        if category_id:
            category_specs = await globals_module.db.get_category_specs(category_id)
            for spec_id, spec_name in category_specs:
                if spec_name not in specs:
                    specs[spec_name] = ""
    
    return specs

def extract_phone_specs(text: str, product_name: str) -> Dict[str, str]:
    """Извлечение характеристик смартфона"""
    specs = {}
    
    # Паттерны для поиска характеристик
    patterns = {
        "Память": r"(?:Память|Storage|ROM)[:\s]+(\d+\s*GB|\d+\s*ТБ)",
        "Оперативная память": r"(?:ОЗУ|RAM|Оперативная память)[:\s]+(\d+\s*GB)",
        "Процессор": r"(?:Процессор|CPU|Chipset)[:\s]+([A-Za-z0-9\s]+)",
        "Экран": r"(?:Экран|Display|Screen)[:\s]+([\d.]+[\"']?\s*дюйм|[\d.]+[\"']?\s*inch)",
        "Камера": r"(?:Камера|Camera)[:\s]+(\d+\s*МП|\d+\s*MP)",
        "Батарея": r"(?:Батарея|Battery)[:\s]+(\d+\s*мАч|\d+\s*mAh)",
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            specs[key] = match.group(1).strip()
    
    return specs

def extract_laptop_specs(text: str, product_name: str) -> Dict[str, str]:
    """Извлечение характеристик ноутбука"""
    specs = {}
    
    patterns = {
        "Процессор": r"(?:Процессор|CPU|Processor)[:\s]+([A-Za-z0-9\s]+)",
        "Оперативная память": r"(?:ОЗУ|RAM|Оперативная память)[:\s]+(\d+\s*GB)",
        "Накопитель": r"(?:SSD|HDD|Накопитель|Storage)[:\s]+(\d+\s*GB|\d+\s*ТБ)",
        "Экран": r"(?:Экран|Display|Screen)[:\s]+([\d.]+[\"']?\s*дюйм|[\d.]+[\"']?\s*inch)",
        "Видеокарта": r"(?:Видеокарта|GPU|Graphics)[:\s]+([A-Za-z0-9\s]+)",
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            specs[key] = match.group(1).strip()
    
    return specs

def extract_pc_specs(text: str, product_name: str) -> Dict[str, str]:
    """Извлечение характеристик ПК"""
    specs = {}
    
    patterns = {
        "Процессор": r"(?:Процессор|CPU|Processor)[:\s]+([A-Za-z0-9\s]+)",
        "Оперативная память": r"(?:ОЗУ|RAM|Оперативная память)[:\s]+(\d+\s*GB)",
        "Накопитель": r"(?:SSD|HDD|Накопитель|Storage)[:\s]+(\d+\s*GB|\d+\s*ТБ)",
        "Видеокарта": r"(?:Видеокарта|GPU|Graphics)[:\s]+([A-Za-z0-9\s]+)",
        "Материнская плата": r"(?:Материнская плата|Motherboard|MB)[:\s]+([A-Za-z0-9\s]+)",
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            specs[key] = match.group(1).strip()
    
    return specs

def extract_general_specs(text: str, product_name: str) -> Dict[str, str]:
    """Извлечение общих характеристик"""
    specs = {}
    
    # Базовые характеристики для любой техники
    patterns = {
        "Процессор": r"(?:Процессор|CPU|Processor)[:\s]+([A-Za-z0-9\s]+)",
        "Память": r"(?:Память|Storage|ROM)[:\s]+(\d+\s*GB|\d+\s*ТБ)",
        "Оперативная память": r"(?:ОЗУ|RAM|Оперативная память)[:\s]+(\d+\s*GB)",
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            specs[key] = match.group(1).strip()
    
    return specs

def get_default_specs(category: str) -> Dict[str, str]:
    """Возвращает базовые поля характеристик для категории"""
    defaults = {
        "android": {
            "Память": "",
            "Оперативная память": "",
            "Процессор": "",
            "Экран": "",
            "Камера": "",
            "Батарея": ""
        },
        "apple": {
            "Память": "",
            "Оперативная память": "",
            "Процессор": "",
            "Экран": "",
            "Камера": "",
            "Батарея": ""
        },
        "laptop": {
            "Процессор": "",
            "Оперативная память": "",
            "Накопитель": "",
            "Экран": "",
            "Видеокарта": ""
        },
        "pc": {
            "Процессор": "",
            "Оперативная память": "",
            "Накопитель": "",
            "Видеокарта": "",
            "Материнская плата": ""
        },
        "other": {
            "Процессор": "",
            "Память": "",
            "Оперативная память": ""
        }
    }
    
    return defaults.get(category, {"Характеристики": ""})


