from typing import Dict, List
from config import CATEGORIES

def format_post(product_name: str, category: str, specifications: Dict[str, str], 
                avito_link: str) -> str:
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
    
    emoji = category_emoji.get(category, "📦")
    category_name = CATEGORIES.get(category, "Техника")
    
    # Красивый заголовок с эмодзи и разделителями
    post = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    post += f"{emoji} <b>{product_name}</b> {emoji}\n"
    post += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
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
    
    # Ссылка на Авито с призывом к действию
    post += "🛒 <b>КУПИТЬ НА АВИТО:</b>\n"
    post += f"🔗 {avito_link}\n\n"
    
    # Разделитель и контакты
    post += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    post += "💬 <i>По вопросам обращайтесь в личные сообщения</i>\n"
    post += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    return post


