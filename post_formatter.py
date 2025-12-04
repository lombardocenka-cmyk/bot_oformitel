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
        
        # Заменяем характеристики
        specs_text = ""
        for spec_name, spec_value in specifications.items():
            if spec_value and spec_value.strip() and spec_value != "Не указано":
                specs_text += f"│ <b>{spec_name}</b>: {spec_value}\n"
        
        if not specs_text:
            specs_text = "│ Характеристики не указаны\n"
        
        post = post.replace("{specifications}", specs_text)
        
        return post
    
    # Если шаблона нет, используем дефолтное форматирование
    emoji = category_emoji.get(category, "📦")
    category_name = CATEGORIES.get(category, "Техника")
    
    # Красивый заголовок с эмодзи и разделителями
    post = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    post += f"{emoji} <b>{product_name}</b> {emoji}\n"
    post += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Цена (если указана)
    if price:
        post += f"💰 <b>Цена:</b> {price} ₽\n\n"
    
    # ID товара (если указан)
    if product_id:
        post += f"🔢 <b>Артикул:</b> {product_id}\n\n"
    
    # Категория с иконкой
    post += f"📂 <b>Категория:</b> {category_name}\n\n"
    
    # Характеристики с красивым оформлением
    post += "⚙️ <b>📋 ХАРАКТЕРИСТИКИ:</b>\n"
    post += "┌─────────────────────────────┐\n"
    
    spec_count = 0
    for spec_name, spec_value in specifications.items():
        if spec_value and spec_value.strip() and spec_value != "Не указано":
            spec_count += 1
            # Красивое форматирование характеристики
            post += f"│ <b>{spec_name}</b>: {spec_value}\n"
    
    if spec_count == 0:
        post += "│ Характеристики не указаны\n"
    
    post += "└─────────────────────────────┘\n\n"
    
    # Адрес магазина (если указан)
    if shop_address:
        post += f"📍 <b>Адрес магазина:</b>\n"
        post += f"{shop_address}\n\n"
    
    # Разделитель
    post += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    # Контакты
    if shop_profile_link:
        post += f"💬 <b>Написать в магазин:</b>\n"
        post += f"{shop_profile_link}\n\n"
    
    post += "🛒 <b>Купить на Авито:</b>\n"
    post += f"{avito_link}\n\n"
    
    # Разделитель
    post += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    post += "💬 <i>По вопросам обращайтесь в личные сообщения</i>\n"
    post += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    return post


