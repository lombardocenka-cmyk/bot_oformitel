import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ID администратора (для модерации постов)
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ID канала для публикации постов
CHANNEL_ID = os.getenv("CHANNEL_ID", "")

# URL веб-приложения (Mini App)
# Для локальной разработки можно использовать ngrok или другой туннель
WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:8000")

# Максимальное количество фотографий
MAX_PHOTOS = 12

# Категории товаров
CATEGORIES = {
    "android": "📱 Смартфон (Android)",
    "apple": "🍎 Смартфон (Apple)",
    "laptop": "💻 Ноутбук",
    "pc": "🖥️ ПК",
    "other": "🔧 Другая техника"
}

# База данных
DATABASE_PATH = "bot_database.db"


