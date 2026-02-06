# Telegram Bot + FastAPI Skeleton

Minimal project scaffold for a Telegram bot with FastAPI, Postgres, and Redis. Focuses on clean architecture and infrastructure only.

There is a single FastAPI service (`app`) that hosts both the API and the bot webhook.

## Requirements
- Docker + Docker Compose
- Python 3.13
- Poetry

## Bot UI (MVP Stub)
- `/start` shows the main menu (reply keyboard).
- Main menu buttons:
  - `Записаться на сеанс` (FSM flow)
  - `Примерить тату` (stub)
  - `Галерея` (stub)
  - `Чат с мастером` (stub)
  - `Админка` (stub, visible only for users in `ADMIN_USER_IDS`)

### Booking Flow: `Записаться на сеанс`
- The flow keeps a draft in Redis via aiogram FSM storage (no separate Redis client for draft data).
- The UI is always two bot messages:
  - верхнее: `Сводка заказа` (updated via edit, includes inline "Изменить" for filled fields)
  - нижнее: текущий вопрос (updated via edit on each step)
- Current steps (stubs): sketch? -> body part -> date (7 days) -> time (skip) -> promo code -> confirm.

## Quick Start (Docker)
1. Create `.env` from `.env.example` and fill required values.
2. Run services:

```bash
docker compose up -d --build
curl -f http://localhost:8000/health
docker compose down -v --remove-orphans
```

API will be available at `http://localhost:8000/health`.

## Local Development (Poetry)
```bash
poetry install

# Unified app
uvicorn apps.app.main:app --host 0.0.0.0 --port 8000
```

## Dev vs Prod Mode
- `APP_ENV=dev` -> bot uses polling inside FastAPI startup
- `APP_ENV=prod` -> bot uses webhook endpoint inside FastAPI

## Webhook Setup (Prod)
1. Ensure `WEBHOOK_URL` is a публичный URL (например, через ngrok):

```bash
ngrok http 8000
```

2. Set `WEBHOOK_URL` to the HTTPS URL from ngrok.
3. Приложение слушает `0.0.0.0:8000` и принимает `/tg/webhook`.

## Checks
```bash
poetry run pytest
poetry run ruff check .
poetry run black .
poetry run pre-commit run -a
```

## Health Endpoint
```bash
curl http://localhost:8000/health
```
