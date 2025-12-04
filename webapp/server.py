"""
Веб-сервер для Telegram Mini App
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
import os
import sys
from typing import Dict, Any
from datetime import datetime

# Добавляем корневую директорию в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram.utils.web_app import safe_parse_webapp_init_data
from config import BOT_TOKEN

logger = logging.getLogger(__name__)

app = FastAPI(title="Telegram Mini App Server")

# CORS для работы с Telegram
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os

# Определяем путь к статическим файлам
# Работает как для разработки, так и для продакшена
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Если статики нет в текущей директории, ищем в корне проекта
if not os.path.exists(STATIC_DIR):
    # Для продакшена, когда файлы в /var/www/miniapp
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STATIC_DIR = os.path.join(BASE_DIR, "webapp", "static")

# Подключение статических файлов
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    """Главная страница Mini App"""
    index_path = os.path.join(STATIC_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/shop-addresses")
async def get_shop_addresses(request: Request):
    """Получить список адресов магазинов"""
    try:
        import globals as globals_module
        addresses = await globals_module.db.get_shop_addresses()
        
        return JSONResponse({
            "success": True,
            "addresses": [
                {"id": addr[0], "name": addr[1], "text": addr[2]}
                for addr in addresses
            ]
        })
    except Exception as e:
        logger.error(f"Error getting shop addresses: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/health")
async def health_check_get():
    """Health check endpoint для предотвращения спиндауна (GET)"""
    return JSONResponse({
        "status": "ok",
        "service": "telegram-miniapp",
        "timestamp": datetime.now().isoformat()
    })

@app.head("/health")
async def health_check_head():
    """Health check endpoint для предотвращения спиндауна (HEAD)"""
    return Response(status_code=200)

@app.get("/ping")
async def ping_get():
    """Ping endpoint (GET)"""
    return JSONResponse({
        "status": "ok",
        "service": "telegram-miniapp",
        "timestamp": datetime.now().isoformat()
    })

@app.head("/ping")
async def ping_head():
    """Ping endpoint (HEAD)"""
    return Response(status_code=200)

@app.post("/api/search-specs")
async def search_specs(request: Request):
    """Поиск характеристик товара"""
    try:
        data = await request.json()
        init_data = data.get("init_data")
        
        # Валидация initData (опционально для разработки, но рекомендуется для продакшена)
        if init_data:
            try:
                web_app_data = safe_parse_webapp_init_data(BOT_TOKEN, init_data)
                logger.info(f"Valid init data from user: {web_app_data.user.id if web_app_data.user else 'unknown'}")
            except ValueError as e:
                logger.warning(f"Invalid init data: {e}. Continuing without validation (dev mode)")
                # В режиме разработки продолжаем без валидации
                # Для продакшена раскомментируйте следующую строку:
                # return JSONResponse(status_code=401, content={"success": False, "error": "Неверные данные авторизации"})
        else:
            logger.warning("No init_data provided. Continuing without validation (dev mode)")
        
        # Импортируем функцию поиска
        try:
            from product_search import search_product_specs
        except ImportError:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from product_search import search_product_specs
        
        product_name = data.get("product_name")
        category = data.get("category")
        
        if not product_name or not category:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Не указаны название товара или категория"}
            )
        
        # Поиск характеристик
        specs = await search_product_specs(product_name, category)
        
        return JSONResponse({
            "success": True,
            "specifications": specs
        })
        
    except Exception as e:
        logger.error(f"Error in search_specs: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/preview-post")
async def preview_post(request: Request):
    """Предпросмотр поста перед отправкой"""
    try:
        data = await request.json()
        init_data = data.get("init_data")
        
        # Валидация initData (опционально для разработки)
        if init_data:
            try:
                web_app_data = safe_parse_webapp_init_data(BOT_TOKEN, init_data)
                logger.info(f"Valid init data from user: {web_app_data.user.id if web_app_data.user else 'unknown'}")
            except ValueError as e:
                logger.warning(f"Invalid init data: {e}. Continuing without validation (dev mode)")
                # В режиме разработки продолжаем без валидации
        else:
            logger.warning("No init_data provided. Continuing without validation (dev mode)")
        
        # Получаем данные поста
        category = data.get("category")
        product_name = data.get("productName")
        specifications = data.get("specifications", {})
        avito_link = data.get("avitoLink")
        price = data.get("price")
        product_id = data.get("productId")
        shop_address = data.get("shopAddress")
        shop_profile_link = data.get("shopProfileLink")
        
        if not all([category, product_name, avito_link]):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Не все обязательные поля заполнены"}
            )
        
        # Импортируем функцию форматирования
        try:
            import globals as globals_module
            from post_formatter import format_post
        except ImportError:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            import globals as globals_module
            from post_formatter import format_post
        
        # Формируем предпросмотр поста
        preview_text = await format_post(
            product_name,
            category,
            specifications,
            avito_link,
            price=price,
            product_id=product_id,
            shop_address=shop_address,
            shop_profile_link=shop_profile_link
        )
        
        # Формируем кнопки
        buttons = []
        if shop_profile_link:
            # Нормализуем ссылку на профиль
            profile_url = shop_profile_link
            if not profile_url.startswith('http'):
                if profile_url.startswith('@'):
                    profile_url = f"https://t.me/{profile_url[1:]}"
                else:
                    profile_url = f"https://t.me/{profile_url}"
            buttons.append({"text": "💬 Написать в магазин", "url": profile_url})
        
        buttons.append({"text": "🛒 Купить на Авито", "url": avito_link})
        
        return JSONResponse({
            "success": True,
            "preview": preview_text,
            "buttons": buttons
        })
        
    except Exception as e:
        logger.error(f"Error in preview_post: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/create-post")
async def create_post(request: Request):
    """Создание поста через Mini App"""
    try:
        data = await request.json()
        init_data = data.get("init_data")
        
        # Валидация initData
        user_id = None
        if init_data:
            try:
                web_app_data = safe_parse_webapp_init_data(BOT_TOKEN, init_data)
                user_id = web_app_data.user.id if web_app_data.user else None
                logger.info(f"Valid init data from user: {user_id}")
            except ValueError as e:
                logger.warning(f"Invalid init data: {e}. Continuing without validation (dev mode)")
                # В режиме разработки продолжаем без валидации
                # Для продакшена раскомментируйте следующую строку:
                # return JSONResponse(status_code=401, content={"success": False, "error": "Неверные данные авторизации"})
        else:
            logger.warning("No init_data provided. Continuing without validation (dev mode)")
        
        # Получаем данные поста
        category = data.get("category")
        product_name = data.get("productName")
        specifications = data.get("specifications", {})
        photos = data.get("photos", [])
        avito_link = data.get("avitoLink")
        price = data.get("price")
        product_id = data.get("productId")
        shop_address = data.get("shopAddress")
        shop_profile_link = data.get("shopProfileLink")
        
        if not all([category, product_name, avito_link]):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Не все обязательные поля заполнены"}
            )
        
        # Импортируем необходимые модули
        # Используем относительный импорт для работы на Railway
        try:
            import globals as globals_module
            from post_formatter import format_post
        except ImportError:
            # Для Railway может потребоваться абсолютный импорт
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            import globals as globals_module
            from post_formatter import format_post
        
        # Формируем пост
        post_text = await format_post(
            product_name,
            category,
            specifications,
            avito_link,
            price=price,
            product_id=product_id,
            shop_address=shop_address,
            shop_profile_link=shop_profile_link
        )
        
        # Сохраняем в базу данных (расширяем для новых полей)
        # Временно сохраняем дополнительные данные в specifications
        extended_specs = specifications.copy()
        if price:
            extended_specs['_price'] = price
        if product_id:
            extended_specs['_product_id'] = product_id
        if shop_address:
            extended_specs['_shop_address'] = shop_address
        if shop_profile_link:
            extended_specs['_shop_profile_link'] = shop_profile_link
        
        post_id = await globals_module.db.create_post(
            user_id=user_id,
            category=category,
            product_name=product_name,
            specifications=extended_specs,
            photos=photos,  # В реальности нужно загрузить фото на сервер
            avito_link=avito_link
        )
        
        await globals_module.db.update_post_text(post_id, post_text)
        
        # Отправляем администратору на модерацию
        from config import ADMIN_ID
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        
        # Кнопки для поста (две кнопки)
        post_keyboard = InlineKeyboardBuilder()
        if shop_profile_link:
            # Нормализуем ссылку на профиль
            profile_url = shop_profile_link
            if not profile_url.startswith('http'):
                if profile_url.startswith('@'):
                    profile_url = f"https://t.me/{profile_url[1:]}"
                else:
                    profile_url = f"https://t.me/{profile_url}"
            post_keyboard.button(text="💬 Написать в магазин", url=profile_url)
        post_keyboard.button(text="🛒 Купить на Авито", url=avito_link)
        post_keyboard.adjust(2)
        
        moderation_keyboard = InlineKeyboardBuilder()
        moderation_keyboard.button(text="✅ Одобрить", callback_data=f"approve_{post_id}")
        moderation_keyboard.button(text="❌ Отклонить", callback_data=f"reject_{post_id}")
        moderation_keyboard.adjust(2)
        
        try:
            # Отправляем пост администратору
            author_name = "Пользователь"
            if init_data:
                try:
                    web_app_data = safe_parse_webapp_init_data(BOT_TOKEN, init_data)
                    if web_app_data.user:
                        author_name = web_app_data.user.first_name or "Пользователь"
                except:
                    pass
            
            await globals_module.bot.send_message(
                ADMIN_ID,
                f"📝 <b>Новый пост на модерацию (Mini App)</b>\n\n"
                f"Автор: {author_name}\n"
                f"ID поста: {post_id}\n\n"
                f"{post_text}",
                parse_mode="HTML"
            )
            
            # Отправляем фотографии (если есть)
            if photos:
                # В реальности нужно загрузить фото на сервер и отправить file_id
                # Здесь упрощенная версия
                pass
            
            # Клавиатура для модерации
            await globals_module.bot.send_message(
                ADMIN_ID,
                "Выберите действие:",
                reply_markup=moderation_keyboard.as_markup()
            )
        except Exception as e:
            logger.error(f"Error sending to admin: {e}")
            # Продолжаем даже если не удалось отправить администратору
        
        return JSONResponse({
            "success": True,
            "post_id": post_id,
            "message": "Пост создан и отправлен на модерацию"
        })
        
    except Exception as e:
        logger.error(f"Error in create_post: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

