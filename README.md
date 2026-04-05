# PawMate MVP (Django)

Прототип превращен в рабочий MVP:
- регистрация и вход
- профиль владельца и питомцы
- Tinder-подобные свайпы
- мэтчи
- базовый чат

## Быстрый старт

1. Активируй окружение:

```powershell
.\.venv\Scripts\Activate.ps1
```

2. Установи зависимости:

```powershell
python -m pip install -r requirements.txt
```

3. Прогони миграции:

```powershell
python manage.py migrate
```

4. Запусти сервер:

```powershell
python manage.py runserver
```

5. Открой:

`http://127.0.0.1:8000/`

## Примечания

- Демо-питомцы создаются автоматически при открытии страницы свайпов.
- Для админки создай суперпользователя:

```powershell
python manage.py createsuperuser
```

- Если команда `python` в системе недоступна из-за алиасов Windows, используй явный путь:

```powershell
C:\Users\maste\AppData\Local\Programs\Python\Python312\python.exe manage.py runserver
```

