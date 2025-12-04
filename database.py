import aiosqlite
from datetime import datetime
from typing import Optional, List, Dict
import json

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    is_admin INTEGER DEFAULT 0,
                    created_at TEXT
                )
            """)
            
            # Таблица постов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    category TEXT,
                    product_name TEXT,
                    specifications TEXT,
                    photos TEXT,
                    avito_link TEXT,
                    post_text TEXT,
                    status TEXT DEFAULT 'pending',
                    scheduled_time TEXT,
                    created_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Таблица характеристик (для редактирования)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS post_specs (
                    spec_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER,
                    spec_name TEXT,
                    spec_value TEXT,
                    FOREIGN KEY (post_id) REFERENCES posts (post_id)
                )
            """)
            
            # Таблица категорий (для админ-панели)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT NOT NULL,
                    category_emoji TEXT,
                    created_at TEXT
                )
            """)
            
            # Таблица характеристик категорий
            await db.execute("""
                CREATE TABLE IF NOT EXISTS category_specs (
                    spec_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER,
                    spec_name TEXT NOT NULL,
                    FOREIGN KEY (category_id) REFERENCES categories (category_id)
                )
            """)
            
            # Таблица адресов магазинов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS shop_addresses (
                    address_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address_name TEXT NOT NULL,
                    address_text TEXT NOT NULL,
                    created_at TEXT
                )
            """)
            
            # Таблица шаблонов постов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS post_templates (
                    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER,
                    template_name TEXT NOT NULL,
                    template_text TEXT NOT NULL,
                    is_default INTEGER DEFAULT 0,
                    created_at TEXT,
                    FOREIGN KEY (category_id) REFERENCES categories (category_id)
                )
            """)
            
            # Таблица шагов процесса создания поста
            await db.execute("""
                CREATE TABLE IF NOT EXISTS post_steps (
                    step_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    step_order INTEGER NOT NULL,
                    step_name TEXT NOT NULL,
                    step_type TEXT NOT NULL,
                    step_config TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT
                )
            """)
            
            await db.commit()
            
            # Инициализация дефолтных категорий, если их нет
            await self._init_default_categories()
            
            # Инициализация дефолтных адресов магазинов, если их нет
            await self._init_default_shop_addresses()
            
            # Инициализация дефолтных шагов, если их нет
            await self._init_default_post_steps()

    async def add_user(self, user_id: int, username: str = None, full_name: str = None):
        """Добавить пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO users (user_id, username, full_name, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, full_name, datetime.now().isoformat()))
            await db.commit()

    async def is_admin(self, user_id: int) -> bool:
        """Проверить, является ли пользователь администратором"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] == 1 if row else False

    async def create_post(self, user_id: int, category: str, product_name: str, 
                         specifications: Dict, photos: List[str], avito_link: str) -> int:
        """Создать новый пост"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO posts (user_id, category, product_name, specifications, 
                                 photos, avito_link, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (
                user_id,
                category,
                product_name,
                json.dumps(specifications, ensure_ascii=False),
                json.dumps(photos, ensure_ascii=False),
                avito_link,
                datetime.now().isoformat()
            ))
            post_id = cursor.lastrowid
            await db.commit()
            return post_id

    async def update_post_text(self, post_id: int, post_text: str):
        """Обновить текст поста"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE posts SET post_text = ? WHERE post_id = ?
            """, (post_text, post_id))
            await db.commit()

    async def update_post_status(self, post_id: int, status: str, scheduled_time: str = None):
        """Обновить статус поста"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE posts SET status = ?, scheduled_time = ? WHERE post_id = ?
            """, (status, scheduled_time, post_id))
            await db.commit()

    async def get_post(self, post_id: int) -> Optional[Dict]:
        """Получить пост по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT post_id, user_id, category, product_name, specifications,
                       photos, avito_link, post_text, status, scheduled_time, created_at
                FROM posts WHERE post_id = ?
            """, (post_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    # Обрабатываем specifications
                    try:
                        specs = json.loads(row[4]) if row[4] else {}
                    except (json.JSONDecodeError, TypeError):
                        specs = {}
                    
                    # Обрабатываем photos
                    try:
                        photos = json.loads(row[5]) if row[5] else []
                    except (json.JSONDecodeError, TypeError):
                        photos = []
                    
                    return {
                        "post_id": row[0],
                        "user_id": row[1],
                        "category": row[2],
                        "product_name": row[3],
                        "specifications": specs,
                        "photos": photos,
                        "avito_link": row[6] or "",
                        "post_text": row[7] or "",
                        "status": row[8] or "pending",
                        "scheduled_time": row[9],
                        "created_at": row[10]
                    }
                return None

    async def get_pending_posts(self) -> List[Dict]:
        """Получить все посты на модерации"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT post_id, user_id, category, product_name, specifications,
                       photos, avito_link, post_text, status, scheduled_time, created_at
                FROM posts WHERE status = 'pending'
                ORDER BY created_at DESC
            """) as cursor:
                rows = await cursor.fetchall()
                return [{
                    "post_id": row[0],
                    "user_id": row[1],
                    "category": row[2],
                    "product_name": row[3],
                    "specifications": json.loads(row[4]),
                    "photos": json.loads(row[5]),
                    "avito_link": row[6],
                    "post_text": row[7],
                    "status": row[8],
                    "scheduled_time": row[9],
                    "created_at": row[10]
                } for row in rows]

    async def get_scheduled_posts(self) -> List[Dict]:
        """Получить запланированные посты"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT post_id, user_id, category, product_name, specifications,
                       photos, avito_link, post_text, status, scheduled_time, created_at
                FROM posts WHERE status = 'approved' AND scheduled_time IS NOT NULL
                ORDER BY scheduled_time ASC
            """) as cursor:
                rows = await cursor.fetchall()
                return [{
                    "post_id": row[0],
                    "user_id": row[1],
                    "category": row[2],
                    "product_name": row[3],
                    "specifications": json.loads(row[4]),
                    "photos": json.loads(row[5]),
                    "avito_link": row[6],
                    "post_text": row[7],
                    "status": row[8],
                    "scheduled_time": row[9],
                    "created_at": row[10]
                } for row in rows]

    async def _init_default_categories(self):
        """Инициализация дефолтных категорий"""
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем, есть ли категории
            async with db.execute("SELECT COUNT(*) FROM categories") as cursor:
                count = (await cursor.fetchone())[0]
            
            if count == 0:
                # Добавляем дефолтные категории
                default_categories = [
                    ("Смартфон (Android)", "📱"),
                    ("Смартфон (Apple)", "🍎"),
                    ("Ноутбук", "💻"),
                    ("ПК", "🖥️"),
                    ("Другая техника", "🔧")
                ]
                
                for name, emoji in default_categories:
                    await db.execute("""
                        INSERT INTO categories (category_name, category_emoji, created_at)
                        VALUES (?, ?, ?)
                    """, (name, emoji, datetime.now().isoformat()))
                
                await db.commit()

    async def _init_default_shop_addresses(self):
        """Инициализация дефолтных адресов магазинов"""
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем, есть ли адреса
            async with db.execute("SELECT COUNT(*) FROM shop_addresses") as cursor:
                count = (await cursor.fetchone())[0]
            
            if count == 0:
                # Добавляем дефолтные адреса
                default_addresses = [
                    ("Главный магазин", "г. Москва, ул. Примерная, д. 1"),
                    ("Филиал 1", "г. Санкт-Петербург, пр. Невский, д. 10"),
                ]
                
                for name, address in default_addresses:
                    await db.execute("""
                        INSERT INTO shop_addresses (address_name, address_text, created_at)
                        VALUES (?, ?, ?)
                    """, (name, address, datetime.now().isoformat()))
                
                await db.commit()

    async def _init_default_post_steps(self):
        """Инициализация дефолтных шагов процесса создания поста"""
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем, есть ли шаги
            async with db.execute("SELECT COUNT(*) FROM post_steps") as cursor:
                count = (await cursor.fetchone())[0]
            
            if count == 0:
                # Добавляем дефолтные шаги
                import json
                default_steps = [
                    (1, "Выбор категории", "category", "{}"),
                    (2, "Название товара", "text", "{}"),
                    (3, "Характеристики", "specs", "{}"),
                    (4, "Фотографии", "photos", "{}"),
                    (5, "Состояние товара", "choice", json.dumps({"choices": ["Отличное", "Хорошее", "Удовлетворительное", "Плохое"]}, ensure_ascii=False)),
                    (6, "Цена", "text", "{}"),
                    (7, "Артикул", "text", "{}"),
                    (8, "Адрес магазина", "text", "{}"),
                    (9, "Ссылка на профиль", "text", "{}"),
                    (10, "Ссылка на Авито", "text", "{}"),
                ]
                
                for order, name, step_type, config in default_steps:
                    await db.execute("""
                        INSERT INTO post_steps (step_order, step_name, step_type, step_config, is_active, created_at)
                        VALUES (?, ?, ?, ?, 1, ?)
                    """, (order, name, step_type, config, datetime.now().isoformat()))
                
                await db.commit()

    async def get_categories(self) -> List[tuple]:
        """Получить все категории"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT category_id, category_name, category_emoji
                FROM categories
                ORDER BY category_id
            """) as cursor:
                return await cursor.fetchall()

    async def get_category(self, category_id: int) -> Optional[tuple]:
        """Получить категорию по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT category_id, category_name, category_emoji
                FROM categories
                WHERE category_id = ?
            """, (category_id,)) as cursor:
                return await cursor.fetchone()

    async def add_category(self, name: str, emoji: str) -> int:
        """Добавить категорию"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO categories (category_name, category_emoji, created_at)
                VALUES (?, ?, ?)
            """, (name, emoji, datetime.now().isoformat()))
            await db.commit()
            return cursor.lastrowid

    async def delete_category(self, category_id: int):
        """Удалить категорию"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM categories WHERE category_id = ?", (category_id,))
            await db.commit()

    async def get_category_specs(self, category_id: int) -> List[tuple]:
        """Получить характеристики категории"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT spec_id, spec_name
                FROM category_specs
                WHERE category_id = ?
                ORDER BY spec_id
            """, (category_id,)) as cursor:
                return await cursor.fetchall()

    async def add_category_spec(self, category_id: int, spec_name: str) -> int:
        """Добавить характеристику категории"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO category_specs (category_id, spec_name)
                VALUES (?, ?)
            """, (category_id, spec_name))
            await db.commit()
            return cursor.lastrowid

    async def get_spec(self, spec_id: int) -> Optional[tuple]:
        """Получить характеристику по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT spec_id, spec_name, category_id
                FROM category_specs
                WHERE spec_id = ?
            """, (spec_id,)) as cursor:
                return await cursor.fetchone()

    async def delete_spec(self, spec_id: int):
        """Удалить характеристику"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM category_specs WHERE spec_id = ?", (spec_id,))
            await db.commit()

    async def get_stats(self) -> Dict:
        """Получить статистику"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Количество пользователей
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                stats['users'] = (await cursor.fetchone())[0]
            
            # Количество постов
            async with db.execute("SELECT COUNT(*) FROM posts") as cursor:
                stats['posts'] = (await cursor.fetchone())[0]
            
            # Посты на модерации
            async with db.execute("SELECT COUNT(*) FROM posts WHERE status = 'pending'") as cursor:
                stats['pending'] = (await cursor.fetchone())[0]
            
            # Одобренные посты
            async with db.execute("SELECT COUNT(*) FROM posts WHERE status = 'approved'") as cursor:
                stats['approved'] = (await cursor.fetchone())[0]
            
            # Опубликованные посты
            async with db.execute("SELECT COUNT(*) FROM posts WHERE status = 'published'") as cursor:
                stats['published'] = (await cursor.fetchone())[0]
            
            # Отклоненные посты
            async with db.execute("SELECT COUNT(*) FROM posts WHERE status = 'rejected'") as cursor:
                stats['rejected'] = (await cursor.fetchone())[0]
            
            return stats

    async def get_shop_addresses(self) -> List[tuple]:
        """Получить все адреса магазинов"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT address_id, address_name, address_text
                FROM shop_addresses
                ORDER BY address_id
            """) as cursor:
                return await cursor.fetchall()

    async def add_shop_address(self, name: str, address: str) -> int:
        """Добавить адрес магазина"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO shop_addresses (address_name, address_text, created_at)
                VALUES (?, ?, ?)
            """, (name, address, datetime.now().isoformat()))
            await db.commit()
            return cursor.lastrowid

    async def delete_shop_address(self, address_id: int):
        """Удалить адрес магазина"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM shop_addresses WHERE address_id = ?", (address_id,))
            await db.commit()

    async def get_shop_address(self, address_id: int) -> Optional[tuple]:
        """Получить адрес магазина по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT address_id, address_name, address_text
                FROM shop_addresses
                WHERE address_id = ?
            """, (address_id,)) as cursor:
                return await cursor.fetchone()

    # Методы для работы с шаблонами постов
    async def add_post_template(self, category_id: int, template_name: str, template_text: str, is_default: int = 0) -> int:
        """Добавить шаблон поста"""
        async with aiosqlite.connect(self.db_path) as db:
            # Если это дефолтный шаблон, снимаем флаг с других шаблонов этой категории
            if is_default:
                await db.execute("""
                    UPDATE post_templates SET is_default = 0 WHERE category_id = ?
                """, (category_id,))
            
            cursor = await db.execute("""
                INSERT INTO post_templates (category_id, template_name, template_text, is_default, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (category_id, template_name, template_text, is_default, datetime.now().isoformat()))
            await db.commit()
            return cursor.lastrowid

    async def get_post_template(self, category_id: int) -> Optional[tuple]:
        """Получить шаблон поста для категории (дефолтный или первый)"""
        async with aiosqlite.connect(self.db_path) as db:
            # Сначала ищем дефолтный
            async with db.execute("""
                SELECT template_id, category_id, template_name, template_text, is_default
                FROM post_templates
                WHERE category_id = ? AND is_default = 1
                LIMIT 1
            """, (category_id,)) as cursor:
                result = await cursor.fetchone()
                if result:
                    return result
            
            # Если дефолтного нет, берем первый
            async with db.execute("""
                SELECT template_id, category_id, template_name, template_text, is_default
                FROM post_templates
                WHERE category_id = ?
                LIMIT 1
            """, (category_id,)) as cursor:
                return await cursor.fetchone()

    async def get_all_post_templates(self, category_id: int = None) -> List[tuple]:
        """Получить все шаблоны постов (для категории или все)"""
        async with aiosqlite.connect(self.db_path) as db:
            if category_id:
                async with db.execute("""
                    SELECT template_id, category_id, template_name, template_text, is_default
                    FROM post_templates
                    WHERE category_id = ?
                    ORDER BY is_default DESC, template_id
                """, (category_id,)) as cursor:
                    return await cursor.fetchall()
            else:
                async with db.execute("""
                    SELECT template_id, category_id, template_name, template_text, is_default
                    FROM post_templates
                    ORDER BY category_id, is_default DESC, template_id
                """) as cursor:
                    return await cursor.fetchall()

    async def update_post_template(self, template_id: int, template_name: str = None, template_text: str = None, is_default: int = None):
        """Обновить шаблон поста"""
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем category_id шаблона
            async with db.execute("SELECT category_id FROM post_templates WHERE template_id = ?", (template_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return
                category_id = row[0]
            
            # Если устанавливаем дефолтный, снимаем флаг с других
            if is_default:
                await db.execute("""
                    UPDATE post_templates SET is_default = 0 WHERE category_id = ? AND template_id != ?
                """, (category_id, template_id))
            
            # Обновляем поля
            updates = []
            params = []
            if template_name is not None:
                updates.append("template_name = ?")
                params.append(template_name)
            if template_text is not None:
                updates.append("template_text = ?")
                params.append(template_text)
            if is_default is not None:
                updates.append("is_default = ?")
                params.append(is_default)
            
            if updates:
                params.append(template_id)
                await db.execute(f"""
                    UPDATE post_templates SET {', '.join(updates)} WHERE template_id = ?
                """, params)
                await db.commit()

    async def delete_post_template(self, template_id: int):
        """Удалить шаблон поста"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM post_templates WHERE template_id = ?", (template_id,))
            await db.commit()

    async def get_template(self, template_id: int) -> Optional[tuple]:
        """Получить шаблон по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT template_id, category_id, template_name, template_text, is_default
                FROM post_templates
                WHERE template_id = ?
            """, (template_id,)) as cursor:
                return await cursor.fetchone()

    # Методы для работы с шагами процесса создания поста
    async def add_post_step(self, step_order: int, step_name: str, step_type: str, step_config: str = "{}", is_active: int = 1) -> int:
        """Добавить шаг процесса создания поста"""
        async with aiosqlite.connect(self.db_path) as db:
            # Обновляем порядок существующих шагов
            await db.execute("""
                UPDATE post_steps SET step_order = step_order + 1 
                WHERE step_order >= ? AND is_active = 1
            """, (step_order,))
            
            cursor = await db.execute("""
                INSERT INTO post_steps (step_order, step_name, step_type, step_config, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (step_order, step_name, step_type, step_config, is_active, datetime.now().isoformat()))
            await db.commit()
            return cursor.lastrowid

    async def get_post_steps(self, active_only: bool = True) -> List[tuple]:
        """Получить все шаги процесса создания поста"""
        async with aiosqlite.connect(self.db_path) as db:
            if active_only:
                async with db.execute("""
                    SELECT step_id, step_order, step_name, step_type, step_config, is_active
                    FROM post_steps
                    WHERE is_active = 1
                    ORDER BY step_order
                """) as cursor:
                    return await cursor.fetchall()
            else:
                async with db.execute("""
                    SELECT step_id, step_order, step_name, step_type, step_config, is_active
                    FROM post_steps
                    ORDER BY step_order
                """) as cursor:
                    return await cursor.fetchall()

    async def get_post_step(self, step_id: int) -> Optional[tuple]:
        """Получить шаг по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT step_id, step_order, step_name, step_type, step_config, is_active
                FROM post_steps
                WHERE step_id = ?
            """, (step_id,)) as cursor:
                return await cursor.fetchone()

    async def update_post_step(self, step_id: int, step_order: int = None, step_name: str = None, 
                              step_type: str = None, step_config: str = None, is_active: int = None):
        """Обновить шаг процесса создания поста"""
        async with aiosqlite.connect(self.db_path) as db:
            updates = []
            params = []
            
            if step_order is not None:
                updates.append("step_order = ?")
                params.append(step_order)
            if step_name is not None:
                updates.append("step_name = ?")
                params.append(step_name)
            if step_type is not None:
                updates.append("step_type = ?")
                params.append(step_type)
            if step_config is not None:
                updates.append("step_config = ?")
                params.append(step_config)
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(is_active)
            
            if updates:
                params.append(step_id)
                await db.execute(f"""
                    UPDATE post_steps SET {', '.join(updates)} WHERE step_id = ?
                """, params)
                await db.commit()

    async def delete_post_step(self, step_id: int):
        """Удалить шаг процесса создания поста"""
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем порядок удаляемого шага
            step = await self.get_post_step(step_id)
            if step:
                step_order = step[1]
                # Удаляем шаг
                await db.execute("DELETE FROM post_steps WHERE step_id = ?", (step_id,))
                # Обновляем порядок остальных шагов
                await db.execute("""
                    UPDATE post_steps SET step_order = step_order - 1 
                    WHERE step_order > ? AND is_active = 1
                """, (step_order,))
                await db.commit()

