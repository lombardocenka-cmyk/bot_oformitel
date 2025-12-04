"""
Скрипт для проверки конфигурации бота
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 50)
print("Проверка конфигурации бота")
print("=" * 50)

# Проверка токена
bot_token = os.getenv("BOT_TOKEN", "")
if not bot_token:
    print("❌ BOT_TOKEN не найден или пустой!")
    print("   Создайте файл .env и добавьте туда:")
    print("   BOT_TOKEN=ваш_токен_бота")
else:
    # Показываем только первые и последние символы для безопасности
    masked_token = bot_token[:10] + "..." + bot_token[-5:] if len(bot_token) > 15 else "***"
    print(f"✅ BOT_TOKEN найден: {masked_token}")

# Проверка ID администратора
admin_id = os.getenv("ADMIN_ID", "0")
try:
    admin_id_int = int(admin_id)
    if admin_id_int == 0:
        print("❌ ADMIN_ID не установлен или равен 0!")
        print("   Добавьте в .env:")
        print("   ADMIN_ID=ваш_telegram_id")
    else:
        print(f"✅ ADMIN_ID установлен: {admin_id_int}")
except ValueError:
    print(f"❌ ADMIN_ID имеет неверный формат: {admin_id}")
    print("   ADMIN_ID должен быть числом!")

# Проверка ID канала
channel_id = os.getenv("CHANNEL_ID", "")
if not channel_id:
    print("❌ CHANNEL_ID не найден или пустой!")
    print("   Добавьте в .env:")
    print("   CHANNEL_ID=@ваш_канал или -1001234567890")
else:
    print(f"✅ CHANNEL_ID установлен: {channel_id}")

print("=" * 50)

if not bot_token or admin_id == "0" or not channel_id:
    print("\n⚠️  ВНИМАНИЕ: Не все параметры настроены!")
    print("   Откройте файл .env и заполните все необходимые поля.")
    print("   Инструкция: см. файл SETUP.md")
else:
    print("\n✅ Все параметры настроены правильно!")
    print("   Можно запускать бота: py -3.11 main.py")

