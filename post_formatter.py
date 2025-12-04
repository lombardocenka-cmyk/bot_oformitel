from typing import Dict, List
from config import CATEGORIES

def format_post(product_name: str, category: str, specifications: Dict[str, str], 
                avito_link: str) -> str:
    """
    Форматирование поста в красивый вид
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
    
    # Заголовок
    post = f"{emoji} <b>{product_name}</b>\n"
    post += f"📂 Категория: {category_name}\n\n"
    
    # Характеристики
    post += "⚙️ <b>Характеристики:</b>\n"
    for spec_name, spec_value in specifications.items():
        if spec_value and spec_value != "Не указано":
            post += f"• {spec_name}: <b>{spec_value}</b>\n"
    
    post += "\n"
    post += "🔗 <b>Ссылка на объявление:</b>\n"
    post += f"{avito_link}\n\n"
    post += "━━━━━━━━━━━━━━━━━━━━\n"
    post += "💬 По вопросам обращайтесь в личные сообщения"
    
    return post


