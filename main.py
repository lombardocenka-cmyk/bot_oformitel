import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, DATABASE_PATH
from database import Database
from handlers import router as handlers_router
from moderation import router as moderation_router
from admin_panel import router as admin_panel_router
from scheduler import PostScheduler
from globals import init_globals

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрация роутеров
dp.include_router(handlers_router)
dp.include_router(moderation_router)
dp.include_router(admin_panel_router)

# Инициализация базы данных
db = Database(DATABASE_PATH)

# Инициализация глобальных объектов
init_globals(bot, db)

# Планировщик постов
scheduler = PostScheduler(db)

async def on_startup():
    """Действия при запуске бота"""
    logger.info("Инициализация базы данных...")
    await db.init_db()
    logger.info("База данных инициализирована")
    
    logger.info("Запуск планировщика постов...")
    await scheduler.start()
    logger.info("Планировщик запущен")
    
    logger.info("Бот запущен и готов к работе!")

async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("Остановка планировщика...")
    scheduler.stop()
    logger.info("Бот остановлен")

async def main():
    """Главная функция"""
    try:
        # Регистрируем обработчики запуска и остановки
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        # Запускаем бота
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")

