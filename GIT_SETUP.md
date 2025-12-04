# Настройка Git для отправки на GitHub

## Проблема

Git требует указать ваше имя и email перед созданием коммита.

## Решение

Выполните следующие команды (замените на ваши данные):

```powershell
# Укажите ваше имя (можно использовать GitHub username)
git config --global user.name "lombardocenka-cmyk"

# Укажите ваш email (тот, который используется на GitHub)
git config --global user.email "ваш-email@example.com"
```

**Пример:**
```powershell
git config --global user.name "lombardocenka-cmyk"
git config --global user.email "lombardocenka@example.com"
```

## После настройки

Выполните команды для отправки на GitHub:

```powershell
# 1. Создайте коммит
git commit -m "Initial commit - Telegram Mini App Bot"

# 2. Отправьте на GitHub
git push -u origin main
```

## Если нужно настроить только для этого проекта

Вместо `--global` используйте без флага:

```powershell
git config user.name "lombardocenka-cmyk"
git config user.email "ваш-email@example.com"
```

## Проверка настроек

```powershell
git config --list
```

Должны увидеть:
```
user.name=lombardocenka-cmyk
user.email=ваш-email@example.com
```

