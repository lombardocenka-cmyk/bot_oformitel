"""
Глобальные объекты для использования в обработчиках
"""
from database import Database
from config import DATABASE_PATH

# Глобальные объекты (инициализируются в main.py)
db: Database = None
bot = None

def init_globals(bot_instance, db_instance: Database):
    """Инициализация глобальных объектов"""
    global bot, db
    bot = bot_instance
    db = db_instance


