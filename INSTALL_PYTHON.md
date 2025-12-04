# Установка Python и зависимостей

## Проблема: Python не найден в системе

Если вы видите ошибку `pip : Имя "pip" не распознано`, это означает, что Python не установлен или не добавлен в PATH.

## Решение 1: Установка Python (если не установлен)

1. **Скачайте Python:**
   - Перейдите на https://www.python.org/downloads/
   - Скачайте последнюю версию Python 3.11 или 3.12

2. **Установите Python:**
   - Запустите установщик
   - ⚠️ **ВАЖНО:** Отметьте галочку "Add Python to PATH" (Добавить Python в PATH)
   - Нажмите "Install Now"

3. **Проверьте установку:**
   ```powershell
   python --version
   ```
   Должно вывести версию Python (например, `Python 3.12.0`)

## Решение 2: Если Python уже установлен, но не в PATH

### Вариант A: Использовать полный путь к Python

Найдите, где установлен Python, и используйте полный путь:

```powershell
# Пример (замените на ваш путь):
C:\Python312\python.exe -m pip install -r requirements.txt
```

### Вариант B: Добавить Python в PATH вручную

1. Найдите, где установлен Python (обычно `C:\Users\ВашеИмя\AppData\Local\Programs\Python\Python3XX\`)

2. Добавьте в PATH:
   - Нажмите `Win + R`, введите `sysdm.cpl` и нажмите Enter
   - Перейдите на вкладку "Дополнительно"
   - Нажмите "Переменные среды"
   - В "Системные переменные" найдите `Path` и нажмите "Изменить"
   - Нажмите "Создать" и добавьте путь к Python (например: `C:\Users\ВашеИмя\AppData\Local\Programs\Python\Python312\`)
   - Также добавьте путь к Scripts: `C:\Users\ВашеИмя\AppData\Local\Programs\Python\Python312\Scripts\`
   - Нажмите "ОК" везде
   - **Перезапустите PowerShell/терминал**

3. Проверьте:
   ```powershell
   python --version
   pip --version
   ```

## Решение 3: Использовать Python из Microsoft Store

1. Откройте Microsoft Store
2. Найдите "Python 3.12" или "Python 3.11"
3. Установите
4. Перезапустите PowerShell

## После установки Python

Установите зависимости проекта:

```powershell
# Перейдите в папку проекта
cd "V:\Vladik Botik"

# Установите зависимости
python -m pip install -r requirements.txt

# Или если не работает:
python -m pip install --upgrade pip
python -m pip install aiogram==3.11.0 aiohttp==3.9.5 aiosqlite==0.19.0 beautifulsoup4==4.12.3 lxml==5.1.0 python-dotenv==1.0.1
```

## Проверка установки

После установки проверьте:

```powershell
python -c "import aiogram; print('aiogram установлен!')"
```

Если команда выполнилась без ошибок, всё готово!

## Альтернатива: Использовать виртуальное окружение (рекомендуется)

```powershell
# Создайте виртуальное окружение
python -m venv venv

# Активируйте его
.\venv\Scripts\Activate.ps1

# Если получите ошибку о политике выполнения, выполните:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Установите зависимости
pip install -r requirements.txt
```


