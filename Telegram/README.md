# Telegram-бот для расчёта нормы воды, калорий и трекинга активности

Telegram-бот для отслеживания воды, калорий и активности с использованием SQLAlchemy для хранения данных.

## Функционал

- ✅ Настройка профиля пользователя (`/set_profile`)
- ✅ Логирование воды (`/log_water`)
- ✅ Логирование еды с использованием OpenFoodFacts API (`/log_food`)
- ✅ Логирование тренировок (`/log_workout`)
- ✅ Проверка прогресса (`/check_progress`)
- ✅ База данных SQLAlchemy (SQLite по умолчанию)

## Установка

1. Создайте виртуальное окружение:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` в корневой директории `Telegram/`:
```env
BOT_TOKEN=ваш_токен_бота
DATABASE_URL=sqlite:///bot.db  # по умолчанию SQLite
```

4. Получите токен бота:
   - Перейдите к [@BotFather](https://t.me/BotFather) в Telegram
   - Используйте команду `/newbot` для создания нового бота
   - Сохраните токен в `.env` файл

## Запуск

Из директории `Telegram/`:
```bash
python3 -m bot.main
```

Или с активированным виртуальным окружением:
```bash
source venv/bin/activate
python3 -m bot.main
```

## Команды бота

- `/start` - Начать работу с ботом
- `/set_profile` - Настроить профиль (вес, рост, возраст, пол, активность, город)
- `/log_water <количество>` - Записать выпитую воду (в мл)
- `/log_food <название продукта>` - Записать съеденную еду
- `/log_workout <тип> <время>` - Записать тренировку (время в минутах)
- `/check_progress` - Проверить прогресс по воде и калориям

## Структура проекта

```
Telegram/
├── bot/
│   ├── __init__.py
│   ├── main.py                 # Точка входа
│   ├── config/
│   │   ├── __init__.py
│   │   ├── bot_config.py       # Конфигурация бота (токен)
│   │   ├── db_config.py        # Конфигурация БД (URL, Base)
│   │   └── open_food_facts_config.py  # Конфигурация OpenFoodFacts API
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # Модель User
│   │   ├── water_log.py         # Модель WaterLog
│   │   ├── food_log.py          # Модель FoodLog
│   │   └── workout_log.py       # Модель WorkoutLog
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py            # /start
│   │   ├── profile.py          # /set_profile
│   │   ├── water.py            # /log_water
│   │   ├── food.py             # /log_food
│   │   ├── workout.py          # /log_workout
│   │   └── progress.py         # /check_progress
│   ├── clients/
│   │   ├── __init__.py
│   │   └── food_client.py      # OpenFoodFacts API клиент
│   └── utils/
│       ├── __init__.py
│       ├── calculations.py     # Расчёты норм воды и калорий
│       └── db_utils.py         # Утилиты для работы с БД (init_db, get_session)
├── requirements.txt
├── Dockerfile                  # Docker-образ для деплоя
├── .env                        # Переменные окружения (не в git)
└── README.md
```

## Архитектура проекта

### Модели данных (models/)
Модели SQLAlchemy разделены по отдельным файлам для лучшей организации кода:
- **user.py** — модель `User` (профиль пользователя: вес, рост, возраст, цели и т.д.)
- **water_log.py** — модель `WaterLog` (записи о выпитой воде)
- **food_log.py** — модель `FoodLog` (записи о съеденной еде)
- **workout_log.py** — модель `WorkoutLog` (записи о тренировках)

### Утилиты (utils/)
- **calculations.py** — функции для расчёта норм воды и калорий
- **db_utils.py** — утилиты для работы с базой данных:
  - `init_db()` — инициализация базы данных
  - `get_session()` — получение сессии для работы с БД

### Обработчики (handlers/)
Каждая команда бота имеет свой отдельный обработчик:
- **start.py** — приветствие и список команд
- **profile.py** — настройка профиля пользователя (conversation handler)
- **water.py** — логирование воды
- **food.py** — логирование еды (conversation handler)
- **workout.py** — логирование тренировок
- **progress.py** — отображение прогресса

### Клиенты (clients/)
- **food_client.py** — клиент для работы с OpenFoodFacts API

### Конфигурация (config/)
- **bot_config.py** — конфигурация бота (токен)
- **db_config.py** — конфигурация базы данных (URL, Base для SQLAlchemy)
- **open_food_facts_config.py** — конфигурация OpenFoodFacts API

## База данных

По умолчанию используется SQLite (`bot.db`). Для продакшена можно использовать PostgreSQL, указав в `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost/dbname
```

## Деплой

Проект включает `Dockerfile` для деплоя на различных платформах (Render.com, Railway, Heroku и т.д.).

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "bot.main"]
```

### Шаги для деплоя:

1. **Подготовка переменных окружения:**
   Убедитесь, что на платформе деплоя установлены следующие переменные:
   - `BOT_TOKEN` — токен вашего Telegram бота
   - `DATABASE_URL` — URL базы данных (для PostgreSQL в продакшене)

2. **Деплой:**
   - Загрузите код на платформу деплоя
   - Платформа автоматически соберёт Docker-образ из `Dockerfile`
   - После успешного билда бот запустится автоматически

3. **Проверка работы:**
   - Проверьте логи на платформе деплоя
   - Отправьте команду `/start` боту в Telegram для проверки работоспособности

### Локальный запуск через Docker:

```bash
# Сборка образа
docker build -t telegram-bot .

# Запуск контейнера
docker run --env-file .env telegram-bot
```

## Лицензия

Учебный проект
