# Архитектура: Автоматизация воронки «Тихий вечер»

## 🏗️ Общая архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                       ПОЛЬЗОВАТЕЛИ                              │
│                                                                 │
│   ┌─────────────────┐         ┌──────────────────┐              │
│   │  Лиды (Insta)   │         │  Telegram канал  │              │
│   │ → Директ Insta  │         │   подписчики     │              │
│   └────────┬────────┘         └────────┬─────────┘              │
└────────────┼──────────────────────────┼────────────────────────┘
             │ (вручную, см. ниже)      │ (deep link)
             ▼                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              TELEGRAM-БОТ @TihiyVecherBot                       │
│                                                                 │
│   ┌────────────────────────────────────────────────────────┐   │
│   │  Хэндлеры команд                                        │   │
│   │   /start, /help, /stats (для автора)                    │   │
│   ├────────────────────────────────────────────────────────┤   │
│   │  Хэндлеры ключевых слов                                 │   │
│   │   СОН  → выдача лид-магнита + старт прогрева            │   │
│   │   ТИХО → описание продукта + кнопка "Купить"            │   │
│   ├────────────────────────────────────────────────────────┤   │
│   │  Планировщик (APScheduler)                              │   │
│   │   - Прогрев: 5 сообщений по расписанию                  │   │
│   │   - Уроки программы: 1 урок/день в 09:00                │   │
│   │   - Автопостинг в канал                                 │   │
│   ├────────────────────────────────────────────────────────┤   │
│   │  Webhook-сервер (FastAPI) на /webhooks/payment          │   │
│   │   - Tinkoff/ЮKassa → подтверждение оплаты               │   │
│   └────────────────────────────────────────────────────────┘   │
└──────────┬──────────────────────────────────┬───────────────────┘
           │                                  │
           ▼                                  ▼
┌──────────────────────┐         ┌─────────────────────────────────┐
│   SQLite / Postgres  │         │  ВНЕШНИЕ СЕРВИСЫ                │
│                      │         │                                 │
│  Таблицы:            │         │  - Telegram Bot API             │
│   users              │         │  - Tinkoff Касса API            │
│   funnel_state       │         │  - ЮKassa API                   │
│   payments           │         │  - (опционально) Google Sheets  │
│   content_schedule   │         │                                 │
│   logs               │         └─────────────────────────────────┘
└──────────────────────┘
```

## 🛠️ Технологический стек

| Слой | Технология | Обоснование |
|------|-----------|-------------|
| Язык | **Python 3.11+** | Богатая экосистема для ботов и веба |
| Telegram-фреймворк | **aiogram 3.x** | Современный async-фреймворк, поддерживает Telegram Bot API 7+ |
| Веб-сервер для webhooks | **FastAPI** | Быстрый, async, автоматическая валидация |
| База данных | **SQLite** (MVP) → **PostgreSQL** (масштаб) | SQLite — нулевой setup, файл рядом с ботом |
| ORM | **SQLAlchemy 2.0** | Стандарт, поддерживает async |
| Миграции | **Alembic** | Стандарт для SQLAlchemy |
| Планировщик | **APScheduler** | Async, встраивается в aiogram, persistent jobs |
| Логирование | **loguru** | Просто и красиво |
| Конфиги | **pydantic-settings** | Валидация `.env` |
| Контейнеризация | **Docker + docker-compose** | Простой деплой |
| Деплой | **VPS + systemd** или **Docker** | Полный контроль |
| Платежи | **Tinkoff Касса API** или **ЮKassa SDK** | Выбор пользователя |

## 📂 Структура проекта

```
bot/
├── README.md
├── pyproject.toml                  # зависимости (через poetry или uv)
├── .env.example
├── docker-compose.yml
├── Dockerfile
│
├── src/
│   ├── __init__.py
│   ├── main.py                     # точка входа (запуск бота + webhook-сервера)
│   ├── config.py                   # настройки из .env
│   │
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers/
│   │   │   ├── start.py            # /start, /help
│   │   │   ├── keywords.py         # СОН, ТИХО
│   │   │   ├── admin.py            # /stats (только для автора)
│   │   │   └── lessons.py          # выдача уроков купившим
│   │   ├── keyboards.py            # инлайн-кнопки
│   │   ├── middlewares.py          # логирование, антифлуд
│   │   └── messages.py             # все тексты сообщений (для редактирования без кода)
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py               # SQLAlchemy модели
│   │   ├── session.py              # async-движок и сессии
│   │   └── repositories/
│   │       ├── users.py
│   │       ├── funnel.py
│   │       └── payments.py
│   │
│   ├── scheduler/
│   │   ├── __init__.py
│   │   ├── jobs.py                 # задачи: прогрев, уроки, автопостинг
│   │   └── scheduler.py            # настройка APScheduler
│   │
│   ├── payments/
│   │   ├── __init__.py
│   │   ├── tinkoff.py              # клиент Tinkoff Касса
│   │   ├── yookassa.py             # клиент ЮKassa
│   │   └── webhook.py              # FastAPI handler для webhooks
│   │
│   └── content/
│       ├── lead_magnet.pdf         # PDF лид-магнита
│       ├── audio/                  # аудиопрактики
│       │   ├── day1_relax.mp3
│       │   └── ...
│       └── lessons/                # тексты уроков 1-7
│           ├── day1.md
│           └── ...
│
├── data/
│   ├── bot.db                      # SQLite (создаётся автоматически)
│   └── content_schedule.csv        # расписание постов в канал
│
├── migrations/                     # Alembic миграции
│
└── tests/
    ├── conftest.py
    └── test_handlers.py
```

## 💾 Модель данных

### Таблица `users`
| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PK | внутренний id |
| telegram_id | BIGINT UNIQUE | id в Telegram |
| username | TEXT | @username |
| first_name | TEXT | имя |
| source | TEXT | СОН / ТИХО / start / unknown |
| first_seen_at | TIMESTAMP | первый контакт |
| status | TEXT | lead / warmed / paid / churned |
| utm_source | TEXT | (опционально) откуда пришёл |

### Таблица `funnel_state`
| Поле | Тип | Описание |
|------|-----|----------|
| user_id | INTEGER FK | связь с users |
| got_lead_magnet | BOOLEAN | получил ли PDF |
| warmup_step | INTEGER | текущий шаг прогрева (0-5) |
| warmup_paused | BOOLEAN | приостановлен ли |
| got_product_details | BOOLEAN | получил ли описание продукта |
| asked_price | BOOLEAN | спрашивал ли цену |
| updated_at | TIMESTAMP | |

### Таблица `payments`
| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PK | |
| user_id | INTEGER FK | |
| provider | TEXT | tinkoff / yookassa |
| provider_payment_id | TEXT | id в платёжной системе |
| amount | INTEGER | в копейках |
| currency | TEXT | RUB |
| status | TEXT | pending / succeeded / failed / refunded |
| created_at | TIMESTAMP | |
| paid_at | TIMESTAMP | |

### Таблица `program_progress`
| Поле | Тип | Описание |
|------|-----|----------|
| user_id | INTEGER FK | |
| started_at | TIMESTAMP | |
| current_day | INTEGER | 1-7 |
| completed | BOOLEAN | |
| feedback | TEXT | отзыв в конце |

### Таблица `content_schedule` (для автопостинга)
| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PK | |
| publish_at | TIMESTAMP | время публикации |
| channel_id | TEXT | id канала |
| text | TEXT | текст поста |
| media_path | TEXT | путь к фото/видео (опц) |
| poll_options | JSON | (опц) для опросов |
| status | TEXT | scheduled / published / failed |

## 🔄 Ключевые потоки

### Поток 1. Получение лид-магнита

```
Пользователь                Бот                    БД
     │                       │                      │
     │── /start ────────────▶│                      │
     │                       │── upsert user ──────▶│
     │◀── приветствие ───────│                      │
     │                       │                      │
     │── СОН ───────────────▶│                      │
     │                       │── update source ────▶│
     │                       │── set funnel_state ─▶│
     │◀── PDF + сообщение ───│                      │
     │                       │── schedule warmup ──▶│ (APScheduler)
     │                       │                      │
     │   через 1 час         │                      │
     │◀── прогрев день 1 ────│                      │
     │   через 24 часа       │                      │
     │◀── прогрев день 2 ────│                      │
     │   ...                 │                      │
```

### Поток 2. Покупка продукта

```
Пользователь                Бот               Tinkoff/ЮKassa        БД
     │                       │                       │               │
     │── ТИХО ──────────────▶│                       │               │
     │◀── описание + кнопка ─│                       │               │
     │                       │                       │               │
     │── клик "Купить" ─────▶│                       │               │
     │                       │── создать payment ───▶│               │
     │                       │                       │── insert ────▶│
     │                       │◀── ссылка на оплату ──│               │
     │◀── ссылка на оплату ──│                       │               │
     │                       │                       │               │
     │── оплата на странице Tinkoff/ЮKassa ─────────▶│               │
     │                       │                       │               │
     │                       │◀── webhook: paid ─────│               │
     │                       │── update payment ───────────────────▶ │
     │                       │── add to product channel ────────────▶│
     │◀── ссылка на канал ───│                       │               │
     │                       │── notify admin ───────│               │
     │                       │── start lesson schedule ─────────────▶│
```

### Поток 3. Доставка уроков

```
APScheduler         Бот              Пользователь          БД
    │                │                    │                  │
    │ каждый день в 9:00 для каждого active покупателя       │
    │── trigger job ▶│                    │                  │
    │                │── get current_day ─────────────────▶  │
    │                │◀── day = 3 ──────────────────────────│
    │                │── send lesson 3 ──▶│                  │
    │                │── update day = 4 ────────────────────▶│
    │                │                    │                  │
    │ день 7 → отправка опроса-отзыва ────│                  │
```

## 🔐 Безопасность

### Telegram Bot
- Токен бота в `.env`, никогда не в коде
- Команда `/stats` — только для `ADMIN_TELEGRAM_ID` из `.env`
- Антифлуд (rate limit) на пользовательские сообщения: 1 сообщение/сек

### Webhooks от платёжек
- Проверка HMAC-подписи запроса
- Только https, проверка SSL
- Идемпотентность: повторные webhook не приводят к двойной выдаче доступа

### База данных
- SQLite-файл в защищённой директории `data/`
- Регулярные бэкапы (cron каждые 24 часа)

## 🚀 Развёртывание

### Минимальная конфигурация VPS
- 1 CPU, 1 GB RAM, 20 GB SSD
- Ubuntu 22.04 LTS
- ~200-300 ₽/месяц (Selectel, Reg.ru, TimeWeb)

### Способ 1: Docker (рекомендую)

```yaml
# docker-compose.yml
version: '3.9'
services:
  bot:
    build: .
    restart: always
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./content:/app/content
    ports:
      - "8000:8000"  # webhook-сервер
```

Запуск:
```bash
docker-compose up -d
```

### Способ 2: systemd на VPS

```ini
# /etc/systemd/system/tihiy-vecher-bot.service
[Unit]
Description=Tihiy Vecher Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bot
ExecStart=/home/ubuntu/bot/.venv/bin/python -m src.main
Restart=always
EnvironmentFile=/home/ubuntu/bot/.env

[Install]
WantedBy=multi-user.target
```

### Webhook-URL для платежей
- Нужен HTTPS-домен (можно через Cloudflare Tunnel бесплатно)
- Альтернатива: ngrok для тестирования

## 📊 Мониторинг (после MVP)

- Логи через `loguru` в файл + stdout
- Опционально: отправка ошибок в личку администратору в Telegram
- Health-check эндпоинт `/health` для uptime-мониторов (UptimeRobot бесплатно)

## ⚖️ Альтернативные варианты (которые НЕ выбраны и почему)

| Альтернатива | Почему НЕ выбрано |
|--------------|--------------------|
| ManyChat / SaleBot | Подписка от 30$/мес, vendor lock-in, ограничения Telegram |
| BotHelp | RU-сервис, но платные тарифы, ограничения автопостинга |
| n8n / Make | Хорошо для прототипа, но сложно настроить надёжно для платежей |
| Zapier | Слишком дорого для русскоязычного проекта |
| Чистый webhook без бота | Требует лендинга, а пользователь хочет сначала бота |

## 🔮 Расширения (после MVP)

1. **Веб-админка** (FastAPI + простой HTML) — для удобства автора
2. **A/B-тесты текстов прогрева**
3. **Сегментация лидов** по поведению
4. **Интеграция с Instagram** через Manychat или собственное API-решение
5. **CRM экспорт** в Bitrix24 / AmoCRM
6. **Email-канал** для тех, кто оставил почту
