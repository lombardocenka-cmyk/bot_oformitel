from typing import Dict, List, Optional
from config import CATEGORIES

def format_post(product_name: str, category: str, specifications: Dict[str, str], 
                avito_link: str, price: Optional[str] = None, product_id: Optional[str] = None,
                shop_address: Optional[str] = None, shop_profile_link: Optional[str] = None) -> str:
    """
    Форматирование поста в красивый вид (как в примере)
    """
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
    
    # НЕ добавляем ссылку на Авито в текст - она будет только в кнопке
    # НЕ добавляем категорию - убрана по требованию
    
    return post

