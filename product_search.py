import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Optional
import re

async def search_product_specs(product_name: str, category: str) -> Dict[str, str]:
    """
    Поиск характеристик товара в интернете
    Использует поиск Google для поиска информации о товаре
    """
    specs = {}
    
    # Формируем поисковый запрос
    search_query = f"{product_name} характеристики спецификация"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Используем Google поиск (можно заменить на другой источник)
            url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # Пытаемся найти характеристики в результатах поиска
                    # Это упрощенная версия, в реальности нужен более сложный парсинг
                    text_content = soup.get_text()
                    
                    # Извлекаем основные характеристики в зависимости от категории
                    if category in ["android", "apple"]:
                        specs = extract_phone_specs(text_content, product_name)
                    elif category == "laptop":
                        specs = extract_laptop_specs(text_content, product_name)
                    elif category == "pc":
                        specs = extract_pc_specs(text_content, product_name)
                    else:
                        specs = extract_general_specs(text_content, product_name)
    
    except Exception as e:
        print(f"Ошибка при поиске характеристик: {e}")
    
    # Если не нашли характеристики, возвращаем базовые поля
    if not specs:
        specs = get_default_specs(category)
    
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
            "Память": "Не указано",
            "Оперативная память": "Не указано",
            "Процессор": "Не указано",
            "Экран": "Не указано",
            "Камера": "Не указано",
            "Батарея": "Не указано"
        },
        "apple": {
            "Память": "Не указано",
            "Оперативная память": "Не указано",
            "Процессор": "Не указано",
            "Экран": "Не указано",
            "Камера": "Не указано",
            "Батарея": "Не указано"
        },
        "laptop": {
            "Процессор": "Не указано",
            "Оперативная память": "Не указано",
            "Накопитель": "Не указано",
            "Экран": "Не указано",
            "Видеокарта": "Не указано"
        },
        "pc": {
            "Процессор": "Не указано",
            "Оперативная память": "Не указано",
            "Накопитель": "Не указано",
            "Видеокарта": "Не указано",
            "Материнская плата": "Не указано"
        },
        "other": {
            "Процессор": "Не указано",
            "Память": "Не указано",
            "Оперативная память": "Не указано"
        }
    }
    
    return defaults.get(category, {"Характеристики": "Не указано"})


