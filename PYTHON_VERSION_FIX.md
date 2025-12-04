# Решение проблемы с Python 3.14

## Проблема

Python 3.14 слишком новый для текущих версий aiogram. Для Python 3.14 нужен `pydantic>=2.12`, но `aiogram 3.22.0` требует `pydantic<2.12`.

## Решение: Использовать Python 3.11 или 3.12

### Вариант 1: Установить Python 3.12 (рекомендуется)

1. **Скачайте Python 3.12:**
   - Перейдите на https://www.python.org/downloads/release/python-3120/
   - Скачайте "Windows installer (64-bit)"

2. **Установите Python 3.12:**
   - Запустите установщик
   - ⚠️ **ВАЖНО:** Отметьте "Add Python 3.12 to PATH"
   - Выберите "Customize installation"
   - Отметьте все опции
   - Нажмите "Next"
   - Отметьте "Add Python to environment variables"
   - Нажмите "Install"

3. **Проверьте установку:**
   ```powershell
   python3.12 --version
   ```
   Должно вывести: `Python 3.12.0`

4. **Установите зависимости:**
   ```powershell
   python3.12 -m pip install -r requirements.txt
   ```

5. **Запустите бота:**
   ```powershell
   python3.12 main.py
   ```

### Вариант 2: Использовать виртуальное окружение с Python 3.12

Если у вас установлено несколько версий Python:

```powershell
# Создайте виртуальное окружение с Python 3.12
py -3.12 -m venv venv

# Активируйте его
.\venv\Scripts\Activate.ps1

# Если получите ошибку о политике выполнения:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Установите зависимости
pip install -r requirements.txt

# Запустите бота
python main.py
```

### Вариант 3: Установить Rust (для сборки из исходников)

Если вы хотите использовать Python 3.14:

1. **Установите Rust:**
   - Перейдите на https://rustup.rs/
   - Скачайте и запустите установщик
   - Следуйте инструкциям

2. **Перезапустите PowerShell**

3. **Проверьте установку:**
   ```powershell
   rustc --version
   cargo --version
   ```

4. **Установите зависимости:**
   ```powershell
   python -m pip install -r requirements.txt
   ```

⚠️ **Внимание:** Сборка из исходников может занять много времени (10-30 минут).

## Рекомендация

**Используйте Python 3.12** - это стабильная версия, которая полностью поддерживается всеми необходимыми пакетами.

## Обновление requirements.txt для Python 3.12

После установки Python 3.12, используйте этот `requirements.txt`:

```
aiogram==3.22.0
aiohttp>=3.9.0,<3.13
aiosqlite>=0.19.0
beautifulsoup4>=4.12.3
lxml>=5.1.0
python-dotenv>=1.0.1
```

