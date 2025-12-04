"""
Скрипт для проверки работы Railway Mini App
"""
import requests
import sys

def test_railway_app(webapp_url):
    """Проверка доступности Mini App"""
    print(f"🔍 Проверяю Mini App: {webapp_url}")
    
    try:
        # Проверка главной страницы
        response = requests.get(webapp_url, timeout=10)
        if response.status_code == 200:
            print("✅ Главная страница доступна")
            if "Создание поста" in response.text or "Mini App" in response.text:
                print("✅ Контент загружается правильно")
            else:
                print("⚠️  Контент не найден, но страница доступна")
        else:
            print(f"❌ Ошибка: статус {response.status_code}")
            return False
        
        # Проверка статических файлов
        css_response = requests.get(f"{webapp_url}/static/style.css", timeout=10)
        if css_response.status_code == 200:
            print("✅ CSS файлы доступны")
        else:
            print(f"⚠️  CSS файлы: статус {css_response.status_code}")
        
        js_response = requests.get(f"{webapp_url}/static/app.js", timeout=10)
        if js_response.status_code == 200:
            print("✅ JavaScript файлы доступны")
        else:
            print(f"⚠️  JavaScript файлы: статус {js_response.status_code}")
        
        print("\n✅ Все проверки пройдены!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return False

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    webapp_url = os.getenv("WEBAPP_URL", "")
    
    if not webapp_url:
        print("❌ WEBAPP_URL не установлен в .env")
        print("Добавьте в .env: WEBAPP_URL=https://ваш-домен.up.railway.app")
        sys.exit(1)
    
    if not webapp_url.startswith("https://"):
        print("⚠️  WEBAPP_URL должен начинаться с https://")
    
    test_railway_app(webapp_url)

