from typing import Dict, List, Optional
from config import CATEGORIES
import globals as globals_module

async def format_post(product_name: str, category: str, specifications: Dict[str, str], 
                avito_link: str, price: Optional[str] = None, product_id: Optional[str] = None,
                shop_address: Optional[str] = None, shop_profile_link: Optional[str] = None) -> str:
    """
    Форматирование поста в красивый и привлекательный вид
    """
    category_emoji = {
        "android": "📱",
        "apple": "🍎",
        "laptop": "💻",
        "pc": "🖥️",
        "other": "🔧"
    }
    
    # Пытаемся получить шаблон из БД
    template_text = None
    if globals_module.db:
        try:
            # Получаем category_id из названия категории
            categories = await globals_module.db.get_categories()
            category_id = None
            for cat_id, cat_name, cat_emoji in categories:
                if category in cat_name.lower() or cat_name.lower() in category:
                    category_id = cat_id
                    break
            
            if category_id:
                template = await globals_module.db.get_post_template(category_id)
                if template:
                    template_text = template[2]  # template_text
        except:
            pass
    
    # Если есть шаблон, используем его
    if template_text:
        # Заменяем переменные в шаблоне
        post = template_text
        post = post.replace("{product_name}", product_name)
        post = post.replace("{category}", CATEGORIES.get(category, "Техника"))
        post = post.replace("{price}", price or "Не указана")
        post = post.replace("{product_id}", product_id or "Не указан")
        post = post.replace("{shop_address}", shop_address or "Не указан")
        post = post.replace("{shop_profile_link}", shop_profile_link or "")
        post = post.replace("{avito_link}", avito_link)
        
        # Маппинг эмодзи для характеристик
        spec_emojis = {
            "состояние": "📱",
            "гарантия": "🛠️",
            "комплект": "📦",
            "память": "💾",
            "оперативная память": "⚡",
            "ram": "⚡",
            "процессор": "🔧",
            "cpu": "🔧",
            "экран": "📺",
            "дисплей": "📺",
            "камера": "📷",
            "батарея": "🔋",
            "аккумулятор": "🔋",
            "цвет": "🎨",
            "размер": "📏",
            "вес": "⚖️",
            "операционная система": "💻",
            "os": "💻",
        }
        
        # Заменяем характеристики (каждая с уникальным оформлением)
        specs_text = ""
        for spec_name, spec_value in specifications.items():
            # Пропускаем служебные поля
            if spec_name.startswith("_"):
                continue
                
            if spec_value and spec_value.strip() and spec_value != "Не указано":
                # Определяем эмодзи для характеристики
                spec_lower = spec_name.lower()
                emoji = "🔹"  # По умолчанию
                for key, emoji_value in spec_emojis.items():
                    if key in spec_lower:
                        emoji = emoji_value
                        break
                
                specs_text += f"{emoji} <b>{spec_name}:</b> {spec_value}\n"
        
        if not specs_text:
            specs_text = "Характеристики не указаны\n"
        
        post = post.replace("{specifications}", specs_text)
        
        return post
    
    # Маппинг эмодзи для характеристик (по умолчанию и специальные)
    spec_emojis = {
        "состояние": "📱",
        "гарантия": "🛠️",
        "комплект": "📦",
        "память": "💾",
        "оперативная память": "⚡",
        "ram": "⚡",
        "процессор": "🔧",
        "cpu": "🔧",
        "экран": "📺",
        "дисплей": "📺",
        "камера": "📷",
        "батарея": "🔋",
        "аккумулятор": "🔋",
        "цвет": "🎨",
        "размер": "📏",
        "вес": "⚖️",
        "операционная система": "💻",
        "os": "💻",
    }
    
    # Название и цена в одной строке (как в примере)
    if price:
        # Форматируем цену (убираем лишние пробелы, добавляем ₽ если нет)
        price_clean = price.strip()
        if not price_clean.endswith(('₽', 'Р', 'руб', 'рублей')):
            price_clean = f"{price_clean} ₽"
        post = f"🔥 <b>{product_name} - {price_clean}</b>\n\n"
    else:
        post = f"🔥 <b>{product_name}</b>\n\n"
    
    # Характеристики с уникальными эмодзи для каждой
    spec_count = 0
    for spec_name, spec_value in specifications.items():
        # Пропускаем служебные поля
        if spec_name.startswith("_"):
            continue
            
        if spec_value and spec_value.strip() and spec_value != "Не указано":
            spec_count += 1
            # Определяем эмодзи для характеристики
            spec_lower = spec_name.lower()
            emoji = "🔹"  # По умолчанию
            for key, emoji_value in spec_emojis.items():
                if key in spec_lower:
                    emoji = emoji_value
                    break
            
            # Форматируем характеристику
            post += f"{emoji} <b>{spec_name}:</b> {spec_value}\n"
    
    # Адрес магазина (если указан)
    if shop_address:
        post += f"\n📍 <b>Адрес:</b> {shop_address}\n"
    
    # ID товара (если указан) - в конце без эмодзи
    if product_id:
        post += f"\n<b>{product_id}</b>"
    
    return post


