"""
Админ-панель для управления категориями и характеристиками
"""
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Dict, List
import json

from config import ADMIN_ID, CATEGORIES
import globals as globals_module

router = Router()

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id == ADMIN_ID

class AdminPanel(StatesGroup):
    waiting_category_name = State()
    waiting_category_emoji = State()
    waiting_spec_name = State()
    waiting_spec_value = State()
    editing_category = State()
    editing_specs = State()
    waiting_shop_address_name = State()
    waiting_shop_address_text = State()
    waiting_template_name = State()
    waiting_template_text = State()
    editing_template = State()
    waiting_step_name = State()
    waiting_step_config = State()

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Открытие админ-панели"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав доступа к админ-панели!")
        return
    
    await show_admin_menu(message)

async def show_admin_menu(message: Message):
    """Показать главное меню админ-панели"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📂 Управление категориями", callback_data="admin_categories")
    keyboard.button(text="⚙️ Управление характеристиками", callback_data="admin_specs")
    keyboard.button(text="📍 Управление адресами магазинов", callback_data="admin_shop_addresses")
    keyboard.button(text="📝 Управление шаблонами постов", callback_data="admin_templates")
    keyboard.button(text="🔨 Конструктор шагов", callback_data="admin_steps_builder")
    keyboard.button(text="📊 Статистика", callback_data="admin_stats")
    keyboard.adjust(1)
    
    await message.answer(
        "🔧 <b>Админ-панель</b>\n\n"
        "Выберите раздел для управления:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_menu")
async def admin_menu_callback(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.delete()
    await show_admin_menu(callback.message)

@router.callback_query(F.data == "admin_categories")
async def admin_categories(callback: CallbackQuery):
    """Управление категориями"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    # Получаем категории из БД или используем дефолтные
    categories = await globals_module.db.get_categories()
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="➕ Добавить категорию", callback_data="admin_add_category")
    
    for cat_id, cat_name, cat_emoji in categories:
        keyboard.button(
            text=f"{cat_emoji} {cat_name}",
            callback_data=f"admin_edit_category_{cat_id}"
        )
    
    keyboard.button(text="🔙 Назад", callback_data="admin_menu")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        "📂 <b>Управление категориями</b>\n\n"
        "Выберите категорию для редактирования или добавьте новую:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_add_category")
async def admin_add_category(callback: CallbackQuery, state: FSMContext):
    """Добавление новой категории"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "➕ <b>Добавление категории</b>\n\n"
        "Введите название категории:",
        parse_mode="HTML"
    )
    await state.set_state(AdminPanel.waiting_category_name)
    await callback.answer()

@router.message(AdminPanel.waiting_category_name)
async def process_category_name(message: Message, state: FSMContext):
    """Обработка названия категории"""
    category_name = message.text.strip()
    await state.update_data(category_name=category_name)
    
    await message.answer(
        "Введите эмодзи для категории (например: 📱):"
    )
    await state.set_state(AdminPanel.waiting_category_emoji)

@router.message(AdminPanel.waiting_category_emoji)
async def process_category_emoji(message: Message, state: FSMContext):
    """Обработка эмодзи категории"""
    emoji = message.text.strip()
    data = await state.get_data()
    category_name = data.get("category_name")
    
    # Сохраняем категорию в БД
    category_id = await globals_module.db.add_category(category_name, emoji)
    
    await message.answer(
        f"✅ Категория добавлена!\n\n"
        f"{emoji} {category_name}"
    )
    
    await state.clear()
    await show_admin_menu(message)

@router.callback_query(F.data.startswith("admin_edit_category_"))
async def admin_edit_category(callback: CallbackQuery):
    """Редактирование категории"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    category_id = int(callback.data.split("_")[-1])
    category = await globals_module.db.get_category(category_id)
    
    if not category:
        await callback.answer("❌ Категория не найдена!", show_alert=True)
        return
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✏️ Изменить название", callback_data=f"admin_rename_category_{category_id}")
    keyboard.button(text="🗑️ Удалить", callback_data=f"admin_delete_category_{category_id}")
    keyboard.button(text="⚙️ Управление характеристиками", callback_data=f"admin_category_specs_{category_id}")
    keyboard.button(text="🔙 Назад", callback_data="admin_categories")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        f"📂 <b>Редактирование категории</b>\n\n"
        f"{category[2]} {category[1]}\n\n"
        f"Выберите действие:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_category_specs_"))
async def admin_category_specs(callback: CallbackQuery):
    """Управление характеристиками категории"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    category_id = int(callback.data.split("_")[-1])
    specs = await globals_module.db.get_category_specs(category_id)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="➕ Добавить характеристику", callback_data=f"admin_add_spec_{category_id}")
    
    for spec_id, spec_name in specs:
        keyboard.button(
            text=f"⚙️ {spec_name}",
            callback_data=f"admin_edit_spec_{spec_id}"
        )
    
    keyboard.button(text="🔙 Назад", callback_data=f"admin_edit_category_{category_id}")
    keyboard.adjust(1)
    
    specs_text = "\n".join([f"• {name}" for _, name in specs]) if specs else "Нет характеристик"
    
    await callback.message.edit_text(
        f"⚙️ <b>Характеристики категории</b>\n\n"
        f"{specs_text}\n\n"
        f"Выберите характеристику для редактирования или добавьте новую:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_add_spec_"))
async def admin_add_spec(callback: CallbackQuery, state: FSMContext):
    """Добавление характеристики"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    category_id = int(callback.data.split("_")[-1])
    await state.update_data(category_id=category_id)
    
    await callback.message.edit_text(
        "➕ <b>Добавление характеристики</b>\n\n"
        "Введите название характеристики (например: Память, Процессор):",
        parse_mode="HTML"
    )
    await state.set_state(AdminPanel.waiting_spec_name)
    await callback.answer()

@router.message(AdminPanel.waiting_spec_name)
async def process_spec_name(message: Message, state: FSMContext):
    """Обработка названия характеристики"""
    spec_name = message.text.strip()
    data = await state.get_data()
    category_id = data.get("category_id")
    
    # Сохраняем характеристику
    spec_id = await globals_module.db.add_category_spec(category_id, spec_name)
    
    await message.answer(
        f"✅ Характеристика добавлена!\n\n"
        f"⚙️ {spec_name}"
    )
    
    await state.clear()
    # Возвращаемся к списку характеристик
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 К характеристикам", callback_data=f"admin_category_specs_{category_id}")
    await message.answer("Выберите действие:", reply_markup=keyboard.as_markup())

@router.callback_query(F.data.startswith("admin_delete_category_"))
async def admin_delete_category(callback: CallbackQuery):
    """Удаление категории"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    category_id = int(callback.data.split("_")[-1])
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅ Да, удалить", callback_data=f"admin_confirm_delete_{category_id}")
    keyboard.button(text="❌ Отмена", callback_data=f"admin_edit_category_{category_id}")
    keyboard.adjust(2)
    
    await callback.message.edit_text(
        "⚠️ <b>Подтверждение удаления</b>\n\n"
        "Вы уверены, что хотите удалить эту категорию?",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_confirm_delete_"))
async def admin_confirm_delete(callback: CallbackQuery):
    """Подтверждение удаления категории"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    category_id = int(callback.data.split("_")[-1])
    await globals_module.db.delete_category(category_id)
    
    await callback.answer("✅ Категория удалена!")
    
    # Возвращаемся к списку категорий
    categories = await globals_module.db.get_categories()
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="➕ Добавить категорию", callback_data="admin_add_category")
    
    for cat_id, cat_name, cat_emoji in categories:
        keyboard.button(
            text=f"{cat_emoji} {cat_name}",
            callback_data=f"admin_edit_category_{cat_id}"
        )
    
    keyboard.button(text="🔙 Назад", callback_data="admin_menu")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        "📂 <b>Управление категориями</b>\n\n"
        "Выберите категорию для редактирования или добавьте новую:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("admin_edit_spec_"))
async def admin_edit_spec(callback: CallbackQuery):
    """Редактирование характеристики"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    spec_id = int(callback.data.split("_")[-1])
    spec = await globals_module.db.get_spec(spec_id)
    
    if not spec:
        await callback.answer("❌ Характеристика не найдена!", show_alert=True)
        return
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✏️ Изменить название", callback_data=f"admin_rename_spec_{spec_id}")
    keyboard.button(text="🗑️ Удалить", callback_data=f"admin_delete_spec_{spec_id}")
    keyboard.button(text="🔙 Назад", callback_data=f"admin_category_specs_{spec[2]}")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        f"⚙️ <b>Редактирование характеристики</b>\n\n"
        f"{spec[1]}\n\n"
        f"Выберите действие:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_delete_spec_"))
async def admin_delete_spec(callback: CallbackQuery):
    """Удаление характеристики"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    spec_id = int(callback.data.split("_")[-1])
    spec = await globals_module.db.get_spec(spec_id)
    
    if not spec:
        await callback.answer("❌ Характеристика не найдена!", show_alert=True)
        return
    
    await globals_module.db.delete_spec(spec_id)
    
    await callback.answer("✅ Характеристика удалена!")
    
    # Возвращаемся к списку характеристик
    category_id = spec[2]
    specs = await globals_module.db.get_category_specs(category_id)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="➕ Добавить характеристику", callback_data=f"admin_add_spec_{category_id}")
    
    for spec_id, spec_name in specs:
        keyboard.button(
            text=f"⚙️ {spec_name}",
            callback_data=f"admin_edit_spec_{spec_id}"
        )
    
    keyboard.button(text="🔙 Назад", callback_data=f"admin_edit_category_{category_id}")
    keyboard.adjust(1)
    
    specs_text = "\n".join([f"• {name}" for _, name in specs]) if specs else "Нет характеристик"
    
    await callback.message.edit_text(
        f"⚙️ <b>Характеристики категории</b>\n\n"
        f"{specs_text}\n\n"
        f"Выберите характеристику для редактирования или добавьте новую:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_shop_addresses")
async def admin_shop_addresses(callback: CallbackQuery):
    """Управление адресами магазинов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    addresses = await globals_module.db.get_shop_addresses()
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="➕ Добавить адрес", callback_data="admin_add_shop_address")
    
    for addr_id, addr_name, addr_text in addresses:
        keyboard.button(
            text=f"📍 {addr_name}",
            callback_data=f"admin_edit_shop_address_{addr_id}"
        )
    
    keyboard.button(text="🔙 Назад", callback_data="admin_menu")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        "📍 <b>Управление адресами магазинов</b>\n\n"
        "Выберите адрес для редактирования или добавьте новый:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_add_shop_address")
async def admin_add_shop_address(callback: CallbackQuery, state: FSMContext):
    """Добавление адреса магазина"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "➕ <b>Добавление адреса магазина</b>\n\n"
        "Введите название адреса (например: Главный магазин):",
        parse_mode="HTML"
    )
    await state.set_state(AdminPanel.waiting_shop_address_name)
    await callback.answer()

@router.message(AdminPanel.waiting_shop_address_name)
async def process_shop_address_name(message: Message, state: FSMContext):
    """Обработка названия адреса"""
    address_name = message.text.strip()
    await state.update_data(address_name=address_name)
    
    await message.answer(
        "Введите адрес магазина (например: г. Москва, ул. Примерная, д. 1):"
    )
    await state.set_state(AdminPanel.waiting_shop_address_text)

@router.message(AdminPanel.waiting_shop_address_text)
async def process_shop_address_text(message: Message, state: FSMContext):
    """Обработка текста адреса"""
    address_text = message.text.strip()
    data = await state.get_data()
    address_name = data.get("address_name")
    
    # Сохраняем адрес
    address_id = await globals_module.db.add_shop_address(address_name, address_text)
    
    await message.answer(
        f"✅ Адрес добавлен!\n\n"
        f"📍 {address_name}\n"
        f"{address_text}"
    )
    
    await state.clear()
    await show_admin_menu(message)

@router.callback_query(F.data.startswith("admin_edit_shop_address_"))
async def admin_edit_shop_address(callback: CallbackQuery):
    """Редактирование адреса магазина"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    address_id = int(callback.data.split("_")[-1])
    address = await globals_module.db.get_shop_address(address_id)
    
    if not address:
        await callback.answer("❌ Адрес не найден!", show_alert=True)
        return
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🗑️ Удалить", callback_data=f"admin_delete_shop_address_{address_id}")
    keyboard.button(text="🔙 Назад", callback_data="admin_shop_addresses")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        f"📍 <b>Редактирование адреса</b>\n\n"
        f"<b>{address[1]}</b>\n"
        f"{address[2]}\n\n"
        f"Выберите действие:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_delete_shop_address_"))
async def admin_delete_shop_address(callback: CallbackQuery):
    """Удаление адреса магазина"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    address_id = int(callback.data.split("_")[-1])
    await globals_module.db.delete_shop_address(address_id)
    
    await callback.answer("✅ Адрес удален!")
    
    # Возвращаемся к списку адресов
    addresses = await globals_module.db.get_shop_addresses()
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="➕ Добавить адрес", callback_data="admin_add_shop_address")
    
    for addr_id, addr_name, addr_text in addresses:
        keyboard.button(
            text=f"📍 {addr_name}",
            callback_data=f"admin_edit_shop_address_{addr_id}"
        )
    
    keyboard.button(text="🔙 Назад", callback_data="admin_menu")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        "📍 <b>Управление адресами магазинов</b>\n\n"
        "Выберите адрес для редактирования или добавьте новый:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_specs")
async def admin_specs(callback: CallbackQuery):
    """Управление характеристиками (глобальное)"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    # Показываем список категорий для выбора
    categories = await globals_module.db.get_categories()
    
    keyboard = InlineKeyboardBuilder()
    for cat_id, cat_name, cat_emoji in categories:
        keyboard.button(
            text=f"{cat_emoji} {cat_name}",
            callback_data=f"admin_category_specs_{cat_id}"
        )
    
    keyboard.button(text="🔙 Назад", callback_data="admin_menu")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        "⚙️ <b>Управление характеристиками</b>\n\n"
        "Выберите категорию для управления характеристиками:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_templates")
async def admin_templates(callback: CallbackQuery):
    """Управление шаблонами постов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    # Показываем список категорий для выбора
    categories = await globals_module.db.get_categories()
    
    keyboard = InlineKeyboardBuilder()
    for cat_id, cat_name, cat_emoji in categories:
        keyboard.button(
            text=f"{cat_emoji} {cat_name}",
            callback_data=f"admin_category_templates_{cat_id}"
        )
    
    keyboard.button(text="🔙 Назад", callback_data="admin_menu")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        "📝 <b>Управление шаблонами постов</b>\n\n"
        "Выберите категорию для управления шаблонами:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_category_templates_"))
async def admin_category_templates(callback: CallbackQuery):
    """Управление шаблонами для категории"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    category_id = int(callback.data.split("_")[-1])
    category = await globals_module.db.get_category(category_id)
    templates = await globals_module.db.get_all_post_templates(category_id)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="➕ Добавить шаблон", callback_data=f"admin_add_template_{category_id}")
    
    for template_id, cat_id, template_name, template_text, is_default in templates:
        default_mark = "⭐ " if is_default else ""
        keyboard.button(
            text=f"{default_mark}📝 {template_name}",
            callback_data=f"admin_edit_template_{template_id}"
        )
    
    keyboard.button(text="🔙 Назад", callback_data="admin_templates")
    keyboard.adjust(1)
    
    category_name = category[1] if category else "Неизвестная категория"
    templates_text = "\n".join([f"• {name} {'(⭐ по умолчанию)' if default else ''}" 
                               for _, _, name, _, default in templates]) if templates else "Нет шаблонов"
    
    await callback.message.edit_text(
        f"📝 <b>Шаблоны постов для категории: {category_name}</b>\n\n"
        f"{templates_text}\n\n"
        f"Выберите шаблон для редактирования или добавьте новый:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_add_template_"))
async def admin_add_template(callback: CallbackQuery, state: FSMContext):
    """Добавление шаблона"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    category_id = int(callback.data.split("_")[-1])
    await state.update_data(category_id=category_id)
    
    await callback.message.edit_text(
        "➕ <b>Добавление шаблона</b>\n\n"
        "Введите название шаблона (например: Стандартный шаблон):",
        parse_mode="HTML"
    )
    await state.set_state(AdminPanel.waiting_template_name)
    await callback.answer()

@router.message(AdminPanel.waiting_template_name)
async def process_template_name(message: Message, state: FSMContext):
    """Обработка названия шаблона"""
    template_name = message.text.strip()
    await state.update_data(template_name=template_name)
    
    await message.answer(
        "Введите текст шаблона. Используйте переменные:\n"
        "{product_name} - название товара\n"
        "{category} - категория\n"
        "{price} - цена\n"
        "{product_id} - ID товара\n"
        "{shop_address} - адрес магазина\n"
        "{shop_profile_link} - ссылка на профиль магазина\n"
        "{avito_link} - ссылка на Авито\n"
        "{specifications} - характеристики (будут вставлены автоматически)\n\n"
        "Пример:\n"
        "🔥 <b>{product_name} - {price} ₽</b>\n\n"
        "{specifications}\n\n"
        "📍 <b>Адрес:</b> {shop_address}"
    )
    await state.set_state(AdminPanel.waiting_template_text)

@router.message(AdminPanel.waiting_template_text)
async def process_template_text(message: Message, state: FSMContext):
    """Обработка текста шаблона"""
    template_text = message.text.strip()
    data = await state.get_data()
    category_id = data.get("category_id")
    template_name = data.get("template_name")
    
    # Сохраняем шаблон
    template_id = await globals_module.db.add_post_template(category_id, template_name, template_text, is_default=0)
    
    await message.answer(
        f"✅ Шаблон добавлен!\n\n"
        f"📝 {template_name}"
    )
    
    await state.clear()
    # Возвращаемся к списку шаблонов
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 К шаблонам", callback_data=f"admin_category_templates_{category_id}")
    await message.answer("Выберите действие:", reply_markup=keyboard.as_markup())

@router.callback_query(F.data.startswith("admin_edit_template_"))
async def admin_edit_template(callback: CallbackQuery):
    """Редактирование шаблона"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    template_id = int(callback.data.split("_")[-1])
    template = await globals_module.db.get_template(template_id)
    
    if not template:
        await callback.answer("❌ Шаблон не найден!", show_alert=True)
        return
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="⭐ Установить по умолчанию", callback_data=f"admin_set_default_template_{template_id}")
    keyboard.button(text="✏️ Изменить текст", callback_data=f"admin_change_template_text_{template_id}")
    keyboard.button(text="🗑️ Удалить", callback_data=f"admin_delete_template_{template_id}")
    keyboard.button(text="🔙 Назад", callback_data=f"admin_category_templates_{template[1]}")
    keyboard.adjust(1)
    
    default_mark = "⭐ " if template[4] else ""
    
    await callback.message.edit_text(
        f"📝 <b>Редактирование шаблона</b>\n\n"
        f"{default_mark}<b>{template[2]}</b>\n\n"
        f"<code>{template[3][:200]}{'...' if len(template[3]) > 200 else ''}</code>\n\n"
        f"Выберите действие:",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_set_default_template_"))
async def admin_set_default_template(callback: CallbackQuery):
    """Установка шаблона по умолчанию"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    template_id = int(callback.data.split("_")[-1])
    await globals_module.db.update_post_template(template_id, is_default=1)
    
    await callback.answer("✅ Шаблон установлен по умолчанию!", show_alert=True)
    
    # Обновляем экран
    await admin_edit_template(callback)

@router.callback_query(F.data.startswith("admin_change_template_text_"))
async def admin_change_template_text(callback: CallbackQuery, state: FSMContext):
    """Изменение текста шаблона"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    template_id = int(callback.data.split("_")[-1])
    template = await globals_module.db.get_template(template_id)
    
    if not template:
        await callback.answer("❌ Шаблон не найден!", show_alert=True)
        return
    
    await state.update_data(template_id=template_id)
    
    await callback.message.edit_text(
        f"✏️ <b>Изменение текста шаблона</b>\n\n"
        f"Текущий текст:\n"
        f"<code>{template[3]}</code>\n\n"
        f"Отправьте новый текст шаблона:",
        parse_mode="HTML"
    )
    await state.set_state(AdminPanel.editing_template)
    await callback.answer()

@router.message(AdminPanel.editing_template)
async def process_template_edit(message: Message, state: FSMContext):
    """Обработка редактирования шаблона"""
    template_text = message.text.strip()
    data = await state.get_data()
    template_id = data.get("template_id")
    
    await globals_module.db.update_post_template(template_id, template_text=template_text)
    
    await message.answer("✅ Текст шаблона обновлен!")
    
    await state.clear()
    
    # Возвращаемся к редактированию шаблона
    template = await globals_module.db.get_template(template_id)
    if template:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔙 К шаблонам", callback_data=f"admin_category_templates_{template[1]}")
        await message.answer("Выберите действие:", reply_markup=keyboard.as_markup())

@router.callback_query(F.data.startswith("admin_delete_template_"))
async def admin_delete_template(callback: CallbackQuery):
    """Удаление шаблона"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    template_id = int(callback.data.split("_")[-1])
    template = await globals_module.db.get_template(template_id)
    
    if not template:
        await callback.answer("❌ Шаблон не найден!", show_alert=True)
        return
    
    category_id = template[1]
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅ Да, удалить", callback_data=f"admin_confirm_delete_template_{template_id}")
    keyboard.button(text="❌ Отмена", callback_data=f"admin_edit_template_{template_id}")
    keyboard.adjust(2)
    
    await callback.message.edit_text(
        "⚠️ <b>Подтверждение удаления</b>\n\n"
        "Вы уверены, что хотите удалить этот шаблон?",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_confirm_delete_template_"))
async def admin_confirm_delete_template(callback: CallbackQuery):
    """Подтверждение удаления шаблона"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    template_id = int(callback.data.split("_")[-1])
    template = await globals_module.db.get_template(template_id)
    
    if template:
        category_id = template[1]
        await globals_module.db.delete_post_template(template_id)
        await callback.answer("✅ Шаблон удален!")
        
        # Возвращаемся к списку шаблонов
        category = await globals_module.db.get_category(category_id)
        templates = await globals_module.db.get_all_post_templates(category_id)
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="➕ Добавить шаблон", callback_data=f"admin_add_template_{category_id}")
        
        for template_id, cat_id, template_name, template_text, is_default in templates:
            default_mark = "⭐ " if is_default else ""
            keyboard.button(
                text=f"{default_mark}📝 {template_name}",
                callback_data=f"admin_edit_template_{template_id}"
            )
        
        keyboard.button(text="🔙 Назад", callback_data="admin_templates")
        keyboard.adjust(1)
        
        category_name = category[1] if category else "Неизвестная категория"
        templates_text = "\n".join([f"• {name} {'(⭐ по умолчанию)' if default else ''}" 
                                   for _, _, name, _, default in templates]) if templates else "Нет шаблонов"
        
        await callback.message.edit_text(
            f"📝 <b>Шаблоны постов для категории: {category_name}</b>\n\n"
            f"{templates_text}\n\n"
            f"Выберите шаблон для редактирования или добавьте новый:",
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Статистика"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав!", show_alert=True)
        return
    
    stats = await globals_module.db.get_stats()
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="admin_menu")
    
    await callback.message.edit_text(
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Всего пользователей: {stats.get('users', 0)}\n"
        f"📝 Всего постов: {stats.get('posts', 0)}\n"
        f"⏳ На модерации: {stats.get('pending', 0)}\n"
        f"✅ Одобрено: {stats.get('approved', 0)}\n"
        f"📢 Опубликовано: {stats.get('published', 0)}\n"
        f"❌ Отклонено: {stats.get('rejected', 0)}",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

