"""
Production конфигурация веб-сервера для поддомена
"""
import os
import sys

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    import uvicorn
    
    # Настройки из переменных окружения
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 8000))
    workers = int(os.getenv("WORKERS", 4))
    
    # Для продакшена используем несколько воркеров
    uvicorn.run(
        "webapp.server:app",
        host=host,
        port=port,
        workers=workers if workers > 1 else None,  # Один процесс для разработки
        log_level="info",
        access_log=True
    )

