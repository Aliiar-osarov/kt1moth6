# backend.md — Стандарты и требования к backend-разработке (Python + Django + DRF)

Документ обязателен к прочтению **всем backend-разработчикам**. Цель — единая архитектура, предсказуемая структура, безопасность секретов и одинаковый стиль реализации.

---

## 0) Зачем мы это делаем

1) **Поддерживаемость**: новый разработчик заходит в проект и сразу понимает, где что лежит.  
2) **Безопасность**: секреты не попадают в репозиторий и логи.  
3) **Масштабирование**: вьюхи тонкие, логика в сервисах, модели “чистые”.  
4) **Стабильные окружения**: dev и prod не мешаются; настройки разделены.

---

## 1) Структура репозитория (как у нас)

Пример (ориентир как на реальном проекте):


Названия проекта/
apps/ # все доменные приложения
back_media/ # медиа (локально/на сервере через storage/nginx)
back_static/ # статика
core/ # django-проект: urls/asgi/wsgi/settings/и т.д.
    settings/
        base.py # все основные настройки сайта
        development.py # (dev.py по смыслу)
        production.py # (prod.py по смыслу)
        jazzmin.py # тема админки
        init.py
    asgi.py
    wsgi.py
    urls.py # здесь только корневые пути приложений
    yasg.py # swagger/redoc
.env # локальные секреты
.env.example # шаблон переменных
manage.py
requirements.txt # только те библиотеки которые используется. лишнее не добавляем
README.md


**Правило:** все приложения — **только внутри `apps/`**.  
**Правило:** проектные “Настройки” — **внутри `core/`**.

---

## 2) Настройки проекта (settings) — разделение на 4 части

Настройки делим на модули, чтобы:
- не таскать dev-настройки в production,
- безопасно управлять секретами,
- переиспользовать базовые настройки.

### 2.1 `core/settings/base.py` — базовые настройки (общие)

Тут лежит **всё общее**:
- `INSTALLED_APPS`, `MIDDLEWARE`,
- `REST_FRAMEWORK`, JWT/авторизация (если есть),
- `LANGUAGE_CODE`, `TIME_ZONE`,
- `STATIC_URL`, `MEDIA_URL` (без привязки к окружению),
- **все настройки, одинаковые для dev и prod**.

**⬅️ Пример в коде:**


Почему так: base — единая точка правды. Dev и Prod только “переопределяют” то, что отличается.

2.2 core/settings/development.py (dev.py) — локальная разработка

Тут:

DATABASES на SQLite3

DEBUG=True

упрощённые настройки, удобные для разработки (например, email в консоль)

допускается ALLOWED_HOSTS=["*"] локально

**⬅️ Пример в коде:**

Почему так: разработка должна стартовать “из коробки” без PostgreSQL и внешних сервисов.

# 2.3 core/settings/production.py (prod.py) — прод окружение

Тут:

DATABASES на PostgreSQL

строгие настройки безопасности

CORS/CSRF/AllowedHosts — только явно

**⬅️ Пример в коде:**

# core/settings/production.py

Почему так: production должен быть предсказуемым и закрытым. Никаких * на бою.

# 2.4 core/settings/jazzmin.py — только настройки админки

Тут только конфиг Jazzmin (UI админки).
Не смешиваем admin UI с остальными настройками.

**⬅️ Пример в коде:**

# core/settings/jazzmin.py

Как подключаем: обычно в base.py просто импортируем:

# core/settings/base.py
from .jazzmin import *  # только UI-настройки

Почему так: админка — отдельный слой. Её легче менять, не рискуя базовыми настройками.


4) ASGI/WSGI/URLs (как на проекте)
core/asgi.py

Используется для ASGI-сервера (например, если будут WebSocket/Channels).

core/wsgi.py

Классический вход для gunicorn/uwsgi.

core/urls.py

Подключаем:

admin

api (v1)

документацию swagger/redoc из yasg.py

5) Swagger / Redoc — core/yasg.py

Правило: вся конфигурация документации — в одном файле yasg.py, чтобы не разносить по проекту.

**⬅️ Пример в коде:**

# core/yasg.py

Подключение в core/urls.py:

from django.contrib import admin
from django.urls import path, include
from core.yasg import urlpatterns_yasg

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/название приложения", include("apps.equipments.urls")),
]

if settings.DEBUG:
    urlpatterns += (
        static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + 
        static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    )
else:
    urlpatterns += [
        re_path(r'^back_media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]

Почему так: документация должна быть “рядом” и одинаковой во всех проектах. Один файл — один источник правды.

6) Секреты и .env — строгое правило
6.1 Главное правило

✅ Все чувствительные данные берём только из .env / переменных окружения
❌ Никаких секретов в коде (ключи, пароли, токены, DSN, приватные ключи)

Что относится к секретам:

DJANGO_SECRET_KEY

креды БД (POSTGRES_*)

JWT ключи, API keys, SMTP пароли

S3 ключи / Firebase / private key

DSN Sentry и т.п.

6.2 Какие библиотеки используем

python-dotenv — чтобы загрузить .env локально

python-decouple (decouple) — чтобы красиво и безопасно читать переменные (cast, default)

Пример чтения:

from decouple import config, Csv

DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

6.3 .env.example обязателен

В репозитории должен быть .env.example (или .env copy → переименовать в .env.example), где перечислены ВСЕ переменные, но без секретных значений.

**⬅️ Пример в коде:**

6.4 .gitignore

.env должен быть в .gitignore.

Почему так: безопасность + возможность деплоя в разные окружения без изменения кода.

7) Приложения (apps) — как мы декомпозируем проект
7.1 Правило размещения

Все Django apps — внутри apps/
Примеры:

apps/equipments/

apps/users/

apps/orders/

apps/payments/

7.2 Рекомендуемая структура приложения
apps/equipments/
  __init__.py
  admin.py
  apps.py
  models.py
  serializers.py
  selectors.py      # выборки/чтение (query logic)
  utils.py          # простые помощники (чистые функции)
  permissions.py
  filters.py
  urls.py
  views.py          # ViewSet/API слой (тонкий)
  tests/

Почему так: уменьшаем “кашу”, упрощаем поиск кода и тестирование.

8) Декомпозиция логики: models vs services vs utils
8.1 Models (models.py)

В models.py — только модели и их простые вещи:

поля

__str__

Meta

простые clean() или валидаторы, если это прям “правило данных”

никаких запросов к внешним API

никакой бизнес-оркестрации

✅ Можно:

class Equipment(models.Model):
    title = models.CharField(max_length=255)
    in_stock = models.BooleanField(default=False)

    def __str__(self):
        return self.title

❌ Нельзя:

ходить в Telegram/WhatsApp/Payment

делать сложные пересчёты “по бизнесу”

смешивать запросы по другим моделям пачками

8.2 Services (services.py)

Сервисы — место бизнес-логики.
Они:

принимают входные данные

валидируют бизнес-правила

делают транзакции

вызывают внешние интеграции

возвращают результат (модель/DTO)

Мини-пример:

# apps/equipments/services.py
from django.db import transaction
from .models import Equipment

@transaction.atomic
def set_equipment_stock(equipment_id: int, in_stock: bool) -> Equipment:
    eq = Equipment.objects.select_for_update().get(id=equipment_id)
    eq.in_stock = in_stock
    eq.save(update_fields=["in_stock"])
    return eq

Почему так: вьюхи остаются тонкими, тестировать сервисы проще, логика переиспользуется.

8.3 Utils (utils.py)

utils.py — простые чистые утилиты, которые:

не знают про HTTP слой

часто не знают про Django ORM (в идеале)

не делают побочных эффектов (или делают очень локально)

Мини-пример:

# apps/equipments/utils.py
def normalize_phone(phone: str) -> str:
    return "".join(ch for ch in phone if ch.isdigit())

Когда utils, когда services?

utils — маленькие чистые функции

services — бизнес-операции, транзакции, orchestration



9) DRF-слой (views/serializers) — “тонкий контроллер”
9.1 Views

В views.py:

принимаем request

вызываем selector/service

отдаём serializer response

Мини-пример:

# apps/equipments/views.py
from rest_framework.viewsets import ModelViewSet
from .models import Equipment
from .serializers import EquipmentSerializer
from .selectors import equipment_list_qs

class EquipmentViewSet(ModelViewSet):
    serializer_class = EquipmentSerializer

    def get_queryset(self):
        return equipment_list_qs()

9.2 Serializers

валидация входа

форматирование выхода

простые validate_*

НЕ держим там “бизнес”

10) Что ещё обязательно (минимальный стандарт качества)
10.1 Миграции

миграции не пушем никогда на GitLab & GitHub.
оставляем только папку миграции и __init__.py

10.3 Зависимости

Все зависимости фиксируем в requirements.txt

Не тащим “лишнее” в base settings

10.4 API-версионирование

Все эндпоинты живут под /api/v1/названия приложения/…

Новая версия — /api/v2/названия приложения  без поломки старой

11) Чек-лист перед PROD

 Секреты не попали в код/коммиты

 Настройки окружения добавлены в .env.example

 Модели чистые, бизнес-логика в services.py

 Swagger/Redoc не сломался

 Миграции не были запушены (добавляем в .gitignore)

 Код читаемый (без “магии” во вьюхах)

12) Быстрый шаблон для нового приложения

Создать папку apps/<name>/

Добавить базовые файлы: models.py, views.py, serializers.py, urls.py, services.py, utils.py

Подключить app в INSTALLED_APPS (в base.py)

Подключить urls app в core/urls.py под /api/v1/названия приложения

и в каждом прокте должен быть установлен библиотека gunicorn и всё

и настроен whitenoise

**⬅️ Пример:**

# core/settings/base.py

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # объязательно после SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Зачем она нужна? Когда проект будет в проде сервер будет Kubernetes и там статики не собирает Nginx, вот поэтому с whitenoise мы собираем сами.

# Команда python manage.py collectstatic  после запуска не должно быть конфликтов