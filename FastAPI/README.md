# URL Shortener API

Сервис сокращения ссылок с регистрацией, статистикой и кэшированием (Redis).

## Запуск через Docker Compose

```bash
cd FastAPI
docker compose up --build
```

API для локального запуска доступен по адресу: http://localhost:8000

- Документация: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

## Описание API

Базовый префикс: `/api/v1`

### Регистрация и вход

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/v1/auth/register` | Регистрация (email, password) |
| POST | `/api/v1/auth/login` | Вход, возвращает JWT token |

Для защищённых методов в заголовок добавлять: `Authorization: Bearer <token>`.

### Ссылки

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/v1/links/shorten` | Создать короткую ссылку (доступно всем). Тело: `original_url`, опционально `custom_alias`, `expires_at` (ISO datetime до минуты) |
| GET | `/api/v1/links/search/?original_url=...` | Поиск ссылок по оригинальному URL |
| GET | `/api/v1/links/{short_code}` | Редирект на оригинальный URL (учёт переходов) |
| GET | `/api/v1/links/{short_code}/stats` | Статистика: URL, дата создания, кол-во переходов, дата последнего перехода |
| PUT | `/api/v1/links/{short_code}` | Обновить длинный URL (только владелец, нужен Bearer token) |
| DELETE | `/api/v1/links/{short_code}` | Удалить ссылку (только владелец, нужен Bearer token) |

**Автоудаление неиспользуемых ссылок:** раз в N часов (по умолчанию 24) в фоне удаляются ссылки, по которым не было переходов дольше `link_inactive_days` дней (по умолчанию 30). Настраивается через `LINK_INACTIVE_DAYS` и `CLEANUP_INTERVAL_HOURS` в окружении.

### Примеры запросов

**Создать короткую ссылку (без авторизации):**
```bash
curl -X POST http://localhost:8000/api/v1/links/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com/page"}'
```

**С кастомным alias и временем жизни:**
```bash
curl -X POST http://localhost:8000/api/v1/links/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com", "custom_alias": "my-link", "expires_at": "2026-12-31T23:59:00"}'
```

**Регистрация и создание ссылки от имени пользователя:**
```bash
# Регистрация
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass"}'

# Вход
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass"}' | jq -r '.access_token')

# Создать ссылку (от владельца)
curl -X POST http://localhost:8000/api/v1/links/shorten \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"original_url": "https://example.com"}'

# Удалить свою ссылку
curl -X DELETE http://localhost:8000/api/v1/links/abc123 \
  -H "Authorization: Bearer $TOKEN"
```

**Поиск по оригинальному URL:**
```bash
curl "http://localhost:8000/api/v1/links/search/?original_url=https://example.com"
```

**Статистика:**
```bash
curl http://localhost:8000/api/v1/links/abc123/stats
```

**Переход по короткой ссылке (редирект на оригинальный URL):**
```bash
# Перейти по короткой ссылке
curl -L "http://localhost:8000/api/v1/links/abc123"

# Только посмотреть, куда ведёт ссылка
curl -s -I "http://localhost:8000/api/v1/links/abc123"
```
В ответе будет `307 Temporary Redirect` и заголовок `Location: <оригинальный URL>`. При каждом таком GET-запросе увеличивается счётчик переходов.

## Покрытие тестами

Текущий отчёт о покрытии кода тестами: **94%**.

**Визуализация:** откройте в браузере файл [htmlcov/index.html](htmlcov/index.html) — там сводка по модулям и построчная разметка.


Проведено **нагрузочное тестирование** с помощью Locust: сценарии создания ссылок, перехода по короткой ссылке и запросов статистики; сравнение производительности с Redis и без кэша.

## Структура проекта

```
FastAPI/
├── app/
│   ├── main.py              # Точка входа FastAPI
│   ├── config/              # Настройки (settings)
│   ├── core/                # database, cache, security
│   ├── models/              # SQLAlchemy (User, Link)
│   ├── schemas/             # Pydantic (запросы/ответы)
│   ├── api/
│   │   └── v1/              # Роутеры: auth, links
│   └── services/            # Бизнес-логика (LinkService, UserService)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## База данных

- **PostgreSQL**: основное хранилище пользователей и ссылок. Таблицы создаются при старте приложения.

  - Таблица `users`:
    - `id` (int, PK)
    - `email` (str, unique, not null)
    - `hashed_password` (str, not null)
    - `created_at` (datetime)

  - Таблица `links`:
    - `id` (int, PK)
    - `short_code` (str, unique, not null)
    - `original_url` (text, not null)
    - `created_at` (datetime)
    - `expires_at` (datetime, nullable)
    - `click_count` (int, default 0)
    - `last_clicked_at` (datetime, nullable)
    - `owner_id` (int, FK → `users.id`, nullable)

- **Redis**: кэш для разрешения short_code → URL и для статистики (кэшируются популярные ссылки и данные по переходам); кэш инвалидируется при обновлении/удалении ссылки.

Переменные окружения задаются в `docker-compose.yml`; для локального запуска без Docker скопируйте `.env_example` в `.env` и укажите `DATABASE_URL` и `REDIS_URL`.

### Влияние кэширования (отчёт)

Эндпоинты перехода по короткой ссылке (`GET /api/v1/links/{short_code}`) и статистики (`GET /api/v1/links/{short_code}/stats`) кэшируются в Redis. Ниже — результаты нагрузочного теста Locust (1 мин, 20 пользователей, `-u 20 -r 5 -t 1m`) при работе **с Redis** и **без Redis** (нерабочий `REDIS_URL`, перезапуск API).

**С Redis (обычный запуск):**

| Эндпоинт | Avg | Med | p95 | RPS |
|----------|-----|-----|-----|-----|
| GET /links/{short_code} | 10 ms | 10 ms | 18 ms | 5.25 |
| GET /links/{short_code}/stats | 5 ms | 5 ms | 8 ms | 1.94 |
| Всего | 10 ms | 9 ms | 18 ms | 37.38 |

**Без Redis:**

| Эндпоинт | Avg | Med | p95 | RPS |
|----------|-----|-----|-----|-----|
| GET /links/{short_code} | 30 ms | 27 ms | 58 ms | 4.58 |
| GET /links/{short_code}/stats | 16 ms | 14 ms | 36 ms | 1.87 |
| Всего | 13 ms | 10 ms | 31 ms | 36.84 |

**Вывод:** при включённом кэше среднее время ответа для перехода по ссылке и для статистики примерно в 3 раза ниже (10 ms и 5 ms против 30 ms и 16 ms), p95 также значительно ниже. RPS по этим эндпоинтам с Redis выше. Повторные запросы к одной и той же ссылке обрабатываются быстрее за счёт кэша и меньшей нагрузки на PostgreSQL.

---

## Прод-развёртывание

Рабочий экземпляр сервиса развёрнут на Render и доступен по адресу: `https://ai-advanced-python-1.onrender.com`.

Все примеры запросов из этого README можно выполнять, заменив `http://localhost:8000` на `https://ai-advanced-python-1.onrender.com`.
