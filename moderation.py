from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import re
import logging

from config import ADMIN_ID, CHANNEL_ID
from database import Database
import globals as globals_module

logger = logging.getLogger(__name__)

router = Router()

class Moderation(StatesGroup):
    waiting_schedule_time = State()

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id == ADMIN_ID

@router.callback_query(F.data.startswith("approve_"))
async def approve_post(callback: CallbackQuery, state: FSMContext):
    """Одобрение поста"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав для модерации!", show_alert=True)
        return
    
    try:
        # Парсим post_id из callback_data (формат: "approve_123")
        post_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка: неверный формат данных!", show_alert=True)
        return
    
    try:
        post = await globals_module.db.get_post(post_id)
    except Exception as e:
        await callback.answer(f"❌ Ошибка при получении поста: {str(e)}", show_alert=True)
        return
    
    if not post:
        await callback.answer("❌ Пост не найден!", show_alert=True)
        return
    
    # Обновляем статус
    try:
        await globals_module.db.update_post_status(post_id, "approved")
    except Exception as e:
        await callback.answer(f"❌ Ошибка при обновлении статуса: {str(e)}", show_alert=True)
        return
    
    # Запрашиваем время публикации
    try:
        await callback.message.edit_text(
            f"✅ Пост одобрен!\n\n"
            f"📅 Укажите время публикации в формате:\n"
            f"• <b>DD.MM.YYYY HH:MM</b> (например: 25.12.2024 15:30)\n"
            f"• или <b>now</b> для немедленной публикации",
            parse_mode="HTML"
        )
    except Exception as e:
        # Если не удалось отредактировать сообщение, отправляем новое
        await callback.message.answer(
            f"✅ Пост одобрен!\n\n"
            f"📅 Укажите время публикации в формате:\n"
            f"• <b>DD.MM.YYYY HH:MM</b> (например: 25.12.2024 15:30)\n"
            f"• или <b>now</b> для немедленной публикации",
            parse_mode="HTML"
        )
    
    await callback.answer()
    
    await state.update_data(post_id=post_id)
    await state.set_state(Moderation.waiting_schedule_time)

@router.callback_query(F.data.startswith("reject_"))
async def reject_post(callback: CallbackQuery):
    """Отклонение поста"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав для модерации!", show_alert=True)
        return
    
    try:
        # Парсим post_id из callback_data (формат: "reject_123")
        post_id = int(callback.data.split("_")[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка: неверный формат данных!", show_alert=True)
        return
    
    try:
        post = await globals_module.db.get_post(post_id)
    except Exception as e:
        await callback.answer(f"❌ Ошибка при получении поста: {str(e)}", show_alert=True)
        return
    
    if not post:
        await callback.answer("❌ Пост не найден!", show_alert=True)
        return
    
    # Обновляем статус
    try:
        await globals_module.db.update_post_status(post_id, "rejected")
    except Exception as e:
        await callback.answer(f"❌ Ошибка при обновлении статуса: {str(e)}", show_alert=True)
        return
    
    # Уведомляем автора
    try:
        await globals_module.bot.send_message(
            post["user_id"],
            f"❌ Ваш пост был отклонен администратором.\n"
            f"Товар: {post['product_name']}\n\n"
            f"Создайте новый пост с исправлениями."
        )
    except:
        pass
    
    try:
        await callback.message.edit_text("❌ Пост отклонен")
    except:
        # Если не удалось отредактировать сообщение, отправляем новое
        await callback.message.answer("❌ Пост отклонен")
    
    await callback.answer()

@router.message(Moderation.waiting_schedule_time)
async def process_schedule_time(message: Message, state: FSMContext):
    """Обработка времени публикации"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав!")
        await state.clear()
        return
    
    data = await state.get_data()
    post_id = data.get("post_id")
    post = await globals_module.db.get_post(post_id)
    
    if not post:
        await message.answer("❌ Пост не найден!")
        await state.clear()
        return
    
    schedule_time_str = message.text.strip()
    
    if schedule_time_str.lower() == "now":
        # Немедленная публикация
        await publish_post(post_id, post)
        await message.answer("✅ Пост опубликован в канал!")
    else:
        # Парсим время
        try:
            # Формат: DD.MM.YYYY HH:MM
            schedule_time = datetime.strptime(schedule_time_str, "%d.%m.%Y %H:%M")
            
            # Проверяем, что время в будущем
            if schedule_time <= datetime.now():
                await message.answer("⚠️ Время публикации должно быть в будущем!")
                return
            
            # Сохраняем время публикации
            await globals_module.db.update_post_status(post_id, "approved", schedule_time.isoformat())
            
            await message.answer(
                f"✅ Время публикации установлено: {schedule_time_str}\n"
                f"Пост будет опубликован автоматически."
            )
        except ValueError:
            await message.answer(
                "⚠️ Неверный формат времени!\n"
                "Используйте формат: DD.MM.YYYY HH:MM\n"
                "Например: 25.12.2024 15:30"
            )
            return
    
    await state.clear()

async def publish_post(post_id: int, post: dict):
    """Публикация поста в канал"""
    from config import CHANNEL_ID
    
    # Извлекаем дополнительные данные из specifications
    specs = post.get("specifications", {})
    shop_profile_link = specs.get("_shop_profile_link")
    avito_link = post["avito_link"]
    
    # Создаем две кнопки
    post_keyboard = InlineKeyboardBuilder()
    
    # Кнопка "Написать в магазин" (если есть ссылка)
    if shop_profile_link:
        # Нормализуем ссылку на профиль
        profile_url = shop_profile_link
        if not profile_url.startswith('http'):
            if profile_url.startswith('@'):
                profile_url = f"https://t.me/{profile_url[1:]}"
            else:
                profile_url = f"https://t.me/{profile_url}"
        post_keyboard.button(text="💬 Написать в магазин", url=profile_url)
    
    # Кнопка "Купить на Авито"
    post_keyboard.button(text="🛒 Купить на Авито", url=avito_link)
    post_keyboard.adjust(2)
    
    # Отправляем фотографии с текстом в одном сообщении
    photos = post.get("photos", [])
    
    # Обрабатываем photos, если это строка JSON
    if isinstance(photos, str):
        import json
        try:
            photos = json.loads(photos)
        except:
            photos = []
    
    if photos and len(photos) > 0:
        if len(photos) == 1:
            # Одна фотография с текстом
            await globals_module.bot.send_photo(
                CHANNEL_ID,
                photos[0],
                caption=post["post_text"],
                reply_markup=post_keyboard.as_markup(),
                parse_mode="HTML"
            )
        else:
            # Медиа-группа: первое фото с текстом, остальные без текста
            from aiogram.types import InputMediaPhoto
            media = [InputMediaPhoto(media=photo_id) for photo_id in photos[:10]]
            # Текст и кнопки только на первом фото
            media[0].caption = post["post_text"]
            media[0].parse_mode = "HTML"
            
            sent_messages = await globals_module.bot.send_media_group(CHANNEL_ID, media)
            
            # Добавляем кнопки к первому сообщению (с текстом)
            try:
                await globals_module.bot.edit_message_reply_markup(
                    chat_id=CHANNEL_ID,
                    message_id=sent_messages[0].message_id,
                    reply_markup=post_keyboard.as_markup(),
                    business_connection_id=None  # Явно указываем None, чтобы избежать ошибки валидации
                )
            except Exception as e:
                logger.error(f"Error editing message reply markup: {e}")
                # Продолжаем работу даже если не удалось добавить кнопки
    else:
        # Только текст
        await globals_module.bot.send_message(
            CHANNEL_ID,
            post["post_text"],
            reply_markup=post_keyboard.as_markup(),
            parse_mode="HTML"
        )
    
    # Обновляем статус
    await globals_module.db.update_post_status(post_id, "published")
    
    # Уведомляем автора
    try:
        await globals_module.bot.send_message(
            post["user_id"],
            f"✅ Ваш пост опубликован в канал!\n"
            f"Товар: {post['product_name']}"
        )
    except:
        pass

