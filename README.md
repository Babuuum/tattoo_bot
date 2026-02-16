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
  - `Примерить тату` (opens Telegram Mini App URL from `MINI_APP_URL`)
  - `Галерея` (stub)
  - `Чат с мастером` (stub)
  - `Админка` (stub, visible only for users in `ADMIN_USER_IDS`)

### Booking Flow: `Записаться на сеанс`
- The flow keeps a draft in Redis via aiogram FSM storage (no separate Redis client for draft data).
- The UI is always two bot messages:
  - верхнее: `Сводка заказа` (updated via edit, includes inline "Изменить" for filled fields)
  - нижнее: текущий вопрос (updated via edit on each step)
- Summary inline buttons (always available during the flow):
  - `Сбросить заявку` (clears draft fields and restarts from the first question)
  - `В меню` (cancels the flow and shows the main menu)
- Calendar policy (fact):
  - `days_ahead=90` (date range is inclusive, based on Moscow date)
  - timezone: `Europe/Moscow` (UI shows "МСК", persisted `start_at` is stored in UTC)
  - time slots: `12:00` .. `20:00` (hourly, inclusive)
- Current steps (fact): sketch? -> body part -> date -> time -> promo code -> confirm.
- `confirm` persists an `Order` record in Postgres (via `core.services.booking_orders.persist_booking_as_order`).

## Quick Start (Docker)
1. Create `.env` from `.env.example` and fill required values.
2. Run services:

```bash
docker compose up -d --build
curl -f http://localhost:8000/health
docker compose down -v --remove-orphans
```

API will be available at `http://localhost:8000/health`.
Mini App frontend (if code exists in `./miniapp`) will be available at
`http://localhost:3000`.

## Local Development (Poetry)
```bash
poetry install

# Unified app
uvicorn apps.app.main:app --host 0.0.0.0 --port 8000
```

## Mini App Frontend (Docker)
- `docker compose up -d miniapp` starts the frontend container.
- If `./miniapp` is still empty, container stays alive and logs a hint.
- After you add frontend files (`package.json` + scripts), restart:

```bash
docker compose restart miniapp
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

## Mini App API (MVP)
- `POST /api/webapp/auth`
  - `prod`: accepts only Telegram `init_data` (validated signature + `auth_date` max age).
  - `dev`: can also accept `dev_shared_secret` if `DEV_SHARED_SECRET` is configured.
- `GET /api/webapp/context` (Bearer token required)
- `POST /api/webapp/selected-design` (Bearer token required)
- `POST /api/pricing/calc` (Bearer token required)

Auth env vars:
- `WEBAPP_AUTH_MAX_AGE_SECONDS` (default `300`)
- `WEBAPP_AUTH_RATE_LIMIT_PER_MINUTE` (default `20`, per IP for `/api/webapp/auth`)
- `DEV_SHARED_SECRET` (used only in `APP_ENV=dev`)
- `MINI_APP_URL` (prod reply-menu WebApp button URL)
- `MINI_APP_DEV_URL` (dev reply-menu WebApp button URL, defaults to localhost)
- `DEV_ALLOW_ALL_ADMINS` (in dev: show/admin-gate for all users, default `true`)
