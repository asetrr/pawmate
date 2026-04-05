# PawMate MVP (Django)

Прототип превращен в рабочий MVP:
- регистрация и вход
- профиль владельца и питомцы
- Tinder-подобные свайпы
- мэтчи
- базовый чат
- загрузка фото питомцев (файл + URL)

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

## Запуск через Docker

1. Скопируй `.env.example` в `.env` и заполни реальные значения.
2. Для Docker Compose используйте внутренние имена сервисов:

```text
DATABASE_URL=postgresql://user:password@db:5432/pawmate
CACHE_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
```

3. Убедись, что Docker запущен.
4. Построй и запусти сервисы:

```powershell
docker compose up --build
```

5. Сайт и фоновые задачи запустятся автоматически: `web`, `worker`, `redis`, `db`.

6. Сайт будет доступен на `http://127.0.0.1:8000/`.

> Если локального Docker CLI нет, установи Docker Desktop for Windows и перезапусти терминал. В репозитории добавлена CI-проверка Docker в `.github/workflows/docker-ci.yml`.

## Production базово

1. Скопируй `.env.example` в `.env` и заполни переменные.
2. Поставь `DJANGO_DEBUG=False`.
3. Укажи `DJANGO_ALLOWED_HOSTS` и при необходимости `DJANGO_CSRF_TRUSTED_ORIGINS`.
4. Для PostgreSQL задай `DATABASE_URL`, например:

```text
postgresql://user:password@localhost:5432/pawmate
```

### Качество сайта и надежность

- В продакшене используйте `DJANGO_SECURE_SSL_REDIRECT=True`, `DJANGO_SECURE_HSTS_SECONDS=31536000` и `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True`.
- Проверяйте работоспособность через `http://<host>/healthz/`.
- Для отказоустойчивости держите `db`, `redis` и `worker` в отдельных службах и используйте `docker compose` с healthchecks.
- В продакшене включите `SENTRY_DSN`, реальную SMTP-конфигурацию и безопасный `DJANGO_SECRET_KEY`.
- Пользовательский опыт улучшен: SEO-теги, PWA-манифест, service worker, sitemap, robots и кастомные страницы ошибок `404`/`500`.

## Что добавлено

- Поддержка `Redis` и `django-redis` для кэширования.
- `Celery` для фоновых задач: отправка писем, асинхронная обработка.
- `django-celery-results` для хранения результатов задач.
- `Sentry` для централизованного логирования ошибок (DSN из `.env`).
- `Dockerfile` и `docker-compose.yml` для быстрого запуска контейнеров.
- `sitemap.xml`, `robots.txt`, PWA-манифест и Service Worker.
- Кастомные страницы `404` и `500`.
- HTTPS / HSTS / secure cookie / CSRF cookie настройки для продакшена.
- Улучшенное логирование и файловый лог `django.log`.

5. Собери статику:

```powershell
python manage.py collectstatic
```

6. Настрой почту для реальных писем (подтверждение email, 2FA, сброс пароля).
Минимальный SMTP-набор в `.env`:

```text
DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DJANGO_DEFAULT_FROM_EMAIL=PawMate <no-reply@pawmate.local>
DJANGO_EMAIL_HOST=smtp.mail.ru
DJANGO_EMAIL_PORT=587
DJANGO_EMAIL_HOST_USER=your_mailbox@mail.ru
DJANGO_EMAIL_HOST_PASSWORD=your_app_password
DJANGO_EMAIL_USE_TLS=True
DJANGO_EMAIL_USE_SSL=False
```

Если оставишь `console.EmailBackend`, письма будут печататься только в терминал сервера.

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

