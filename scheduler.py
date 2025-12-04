import asyncio
from datetime import datetime
from database import Database
from moderation import publish_post

class PostScheduler:
    def __init__(self, db: Database):
        self.db = db
        self.running = False
    
    async def start(self):
        """Запуск планировщика"""
        self.running = True
        asyncio.create_task(self._scheduler_loop())
    
    async def _scheduler_loop(self):
        """Основной цикл планировщика"""
        while self.running:
            try:
                # Получаем запланированные посты
                scheduled_posts = await self.db.get_scheduled_posts()
                current_time = datetime.now()
                
                for post in scheduled_posts:
                    scheduled_time = datetime.fromisoformat(post["scheduled_time"])
                    
                    # Если время публикации наступило
                    if scheduled_time <= current_time:
                        await publish_post(post["post_id"], post)
                
                # Проверяем каждую минуту
                await asyncio.sleep(60)
            except Exception as e:
                print(f"Ошибка в планировщике: {e}")
                await asyncio.sleep(60)
    
    def stop(self):
        """Остановка планировщика"""
        self.running = False

