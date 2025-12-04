from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, User, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List
import re

from config import CATEGORIES, MAX_PHOTOS
from database import Database
from product_search import search_product_specs
from post_formatter import format_post
import globals as globals_module

router = Router()

def get_user_full_name(user: User) -> str:
    """Получить полное имя пользователя"""
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    return full_name or user.username or "Пользователь"

class PostCreation(StatesGroup):
    waiting_category = State()
    waiting_product_name = State()
    waiting_specs_confirmation = State()
    editing_spec = State()
    waiting_photos = State()
    waiting_avito_link = State()

# Глобальные переменные для хранения данных поста
user_posts = {}

def get_category_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру выбора категории"""
    builder = InlineKeyboardBuilder()
    for key, value in CATEGORIES.items():
        builder.button(text=value, callback_data=f"category_{key}")
    builder.adjust(2)
    return builder.as_markup()

def get_specs_keyboard(specs: dict) -> InlineKeyboardMarkup:
    """Создать клавиатуру для подтверждения/изменения характеристик"""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="specs_confirm")
    builder.button(text="✏️ Изменить", callback_data="specs_edit")
    builder.adjust(2)
    return builder.as_markup()

def get_edit_specs_keyboard(specs: dict) -> InlineKeyboardMarkup:
    """Создать клавиатуру для редактирования характеристик"""
    builder = InlineKeyboardBuilder()
    for spec_name in specs.keys():
        builder.button(text=f"✏️ {spec_name}", callback_data=f"edit_{spec_name}")
    builder.button(text="✅ Завершить редактирование", callback_data="edit_done")
    builder.adjust(1)
    return builder.as_markup()

def get_start_keyboard() -> InlineKeyboardMarkup:
    """Создать клавиатуру для команды /start с WebApp кнопкой"""
    from config import WEBAPP_URL
    
    builder = InlineKeyboardBuilder()
    if WEBAPP_URL:
        builder.button(
            text="📱 Открыть приложение",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    builder.button(text="💬 Использовать бота", callback_data="use_bot")
    builder.adjust(1)
    return builder.as_markup()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = get_user_full_name(message.from_user)
    
    await globals_module.db.add_user(user_id, username, full_name)
    
    await message.answer(
        f"👋 Привет, {full_name}!\n\n"
        "Я помогу вам создать пост для канала.\n\n"
        "Выберите способ создания поста:",
        reply_markup=get_start_keyboard()
    )

@router.callback_query(F.data == "use_bot")
async def use_bot_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора использования бота"""
    await callback.message.edit_text(
        "Давайте начнем! Выберите категорию товара:",
        reply_markup=get_category_keyboard()
    )
    await callback.answer()
    await state.set_state(PostCreation.waiting_category)

@router.callback_query(F.data.startswith("category_"))
async def process_category(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории"""
    category = callback.data.split("_")[1]
    
    await state.update_data(category=category)
    await callback.message.edit_text(
        f"✅ Выбрана категория: {CATEGORIES[category]}\n\n"
        "📝 Теперь введите точное название товара:"
    )
    await callback.answer()
    await state.set_state(PostCreation.waiting_product_name)

@router.message(StateFilter(PostCreation.waiting_product_name))
async def process_product_name(message: Message, state: FSMContext):
    """Обработка названия товара и поиск характеристик"""
    product_name = message.text
    data = await state.get_data()
    category = data.get("category")
    
    # Сохраняем название
    await state.update_data(product_name=product_name)
    
    # Показываем индикатор загрузки
    loading_msg = await message.answer("🔍 Ищу характеристики товара...")
    
    # Ищем характеристики
    specs = await search_product_specs(product_name, category)
    
    # Сохраняем характеристики
    await state.update_data(specifications=specs)
    
    # Форматируем характеристики для отображения
    specs_text = "📋 Найденные характеристики:\n\n"
    for spec_name, spec_value in specs.items():
        specs_text += f"• {spec_name}: <b>{spec_value}</b>\n"
    
    specs_text += "\n✅ Подтвердить или ✏️ изменить?"
    
    await loading_msg.delete()
    await message.answer(
        specs_text,
        reply_markup=get_specs_keyboard(specs),
        parse_mode="HTML"
    )
    
    await state.set_state(PostCreation.waiting_specs_confirmation)

@router.callback_query(F.data == "specs_confirm")
async def confirm_specs(callback: CallbackQuery, state: FSMContext):
    """Подтверждение характеристик"""
    await callback.message.edit_text(
        "✅ Характеристики подтверждены!\n\n"
        f"📸 Теперь отправьте фотографии товара (до {MAX_PHOTOS} штук).\n"
        "Можно отправить несколько фото сразу или по одному.\n"
        "Когда закончите, отправьте /done"
    )
    await callback.answer()
    
    # Инициализируем список фотографий
    await state.update_data(photos=[])
    await state.set_state(PostCreation.waiting_photos)

@router.callback_query(F.data == "specs_edit")
async def edit_specs(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования характеристик"""
    data = await state.get_data()
    specs = data.get("specifications", {})
    
    specs_text = "✏️ Выберите характеристику для редактирования:\n\n"
    for spec_name, spec_value in specs.items():
        specs_text += f"• {spec_name}: <b>{spec_value}</b>\n"
    
    await callback.message.edit_text(
        specs_text,
        reply_markup=get_edit_specs_keyboard(specs),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("edit_"))
async def process_edit_spec(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора характеристики для редактирования"""
    if callback.data == "edit_done":
        # Завершение редактирования
        data = await state.get_data()
        specs = data.get("specifications", {})
        
        specs_text = "✅ Характеристики обновлены:\n\n"
        for spec_name, spec_value in specs.items():
            specs_text += f"• {spec_name}: <b>{spec_value}</b>\n"
        
        specs_text += "\n✅ Подтвердить или ✏️ изменить?"
        
        await callback.message.edit_text(
            specs_text,
            reply_markup=get_specs_keyboard(specs),
            parse_mode="HTML"
        )
        await callback.answer()
        await state.set_state(PostCreation.waiting_specs_confirmation)
    else:
        # Выбор характеристики для редактирования
        spec_name = callback.data.replace("edit_", "")
        await state.update_data(editing_spec_name=spec_name)
        
        await callback.message.edit_text(
            f"✏️ Введите новое значение для характеристики <b>'{spec_name}'</b>:",
            parse_mode="HTML"
        )
        await callback.answer()
        await state.set_state(PostCreation.editing_spec)

@router.message(StateFilter(PostCreation.editing_spec))
async def process_spec_value(message: Message, state: FSMContext):
    """Обработка нового значения характеристики"""
    data = await state.get_data()
    spec_name = data.get("editing_spec_name")
    specs = data.get("specifications", {})
    
    # Обновляем значение характеристики
    specs[spec_name] = message.text
    await state.update_data(specifications=specs)
    
    # Показываем клавиатуру для дальнейшего редактирования
    specs_text = "✏️ Выберите характеристику для редактирования:\n\n"
    for name, value in specs.items():
        specs_text += f"• {name}: <b>{value}</b>\n"
    
    await message.answer(
        specs_text,
        reply_markup=get_edit_specs_keyboard(specs),
        parse_mode="HTML"
    )

@router.message(StateFilter(PostCreation.waiting_photos), F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Обработка фотографий"""
    data = await state.get_data()
    photos = data.get("photos", [])
    
    if len(photos) >= MAX_PHOTOS:
        await message.answer(f"⚠️ Максимальное количество фотографий ({MAX_PHOTOS}) достигнуто!")
        return
    
    # Получаем file_id самой большой фотографии
    photo = message.photo[-1]
    photos.append(photo.file_id)
    
    await state.update_data(photos=photos)
    
    await message.answer(
        f"✅ Фото добавлено ({len(photos)}/{MAX_PHOTOS})\n"
        "Отправьте еще фото или /done для продолжения"
    )

@router.message(StateFilter(PostCreation.waiting_photos), Command("done"))
async def photos_done(message: Message, state: FSMContext):
    """Завершение загрузки фотографий"""
    data = await state.get_data()
    photos = data.get("photos", [])
    
    if not photos:
        await message.answer("⚠️ Пожалуйста, отправьте хотя бы одну фотографию!")
        return
    
    await message.answer(
        f"✅ Фотографии загружены ({len(photos)} шт.)\n\n"
        "🔗 Теперь отправьте ссылку на объявление Авито:"
    )
    await state.set_state(PostCreation.waiting_avito_link)

@router.message(StateFilter(PostCreation.waiting_avito_link))
async def process_avito_link(message: Message, state: FSMContext):
    """Обработка ссылки на Авито"""
    avito_link = message.text
    
    # Простая проверка на ссылку
    if not (avito_link.startswith("http://") or avito_link.startswith("https://")):
        await message.answer("⚠️ Пожалуйста, отправьте корректную ссылку!")
        return
    
    data = await state.get_data()
    
    # Формируем пост
    post_text = format_post(
        data.get("product_name"),
        data.get("category"),
        data.get("specifications", {}),
        avito_link
    )
    
    # Сохраняем пост в базу данных
    post_id = await globals_module.db.create_post(
        user_id=message.from_user.id,
        category=data.get("category"),
        product_name=data.get("product_name"),
        specifications=data.get("specifications", {}),
        photos=data.get("photos", []),
        avito_link=avito_link
    )
    
    await globals_module.db.update_post_text(post_id, post_text)
    
    # Отправляем пост администратору на модерацию
    from config import ADMIN_ID
    
    # Создаем кнопку "Купить"
    buy_keyboard = InlineKeyboardBuilder()
    buy_keyboard.button(text="🛒 Купить", url=avito_link)
    
    # Отправляем пост администратору
    author_name = get_user_full_name(message.from_user)
    admin_message = await globals_module.bot.send_message(
        ADMIN_ID,
        f"📝 <b>Новый пост на модерацию</b>\n\n"
        f"Автор: {author_name}\n"
        f"ID поста: {post_id}\n\n"
        f"{post_text}",
        parse_mode="HTML"
    )
    
    # Отправляем фотографии администратору
    photos = data.get("photos", [])
    if photos:
        if len(photos) == 1:
            await globals_module.bot.send_photo(ADMIN_ID, photos[0])
        else:
            # Отправляем медиа-группу
            from aiogram.types import InputMediaPhoto
            media = [InputMediaPhoto(media=photo_id) for photo_id in photos[:10]]
            await globals_module.bot.send_media_group(ADMIN_ID, media)
    
    # Клавиатура для модерации
    moderation_keyboard = InlineKeyboardBuilder()
    moderation_keyboard.button(text="✅ Одобрить", callback_data=f"approve_{post_id}")
    moderation_keyboard.button(text="❌ Отклонить", callback_data=f"reject_{post_id}")
    moderation_keyboard.adjust(2)
    
    await globals_module.bot.send_message(
        ADMIN_ID,
        "Выберите действие:",
        reply_markup=moderation_keyboard.as_markup()
    )
    
    await message.answer(
        "✅ Пост создан и отправлен на модерацию!\n"
        "Ожидайте одобрения администратора."
    )
    
    await state.clear()

