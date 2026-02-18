# Mini App (Frontend)

Фронтенд Mini App реализован в `miniapp` на `Vite + React + TypeScript`.

## Запуск локально

```bash
cd miniapp
npm ci
npm run dev -- --host 0.0.0.0 --port 3000
```

Открыть: `http://localhost:3000`.

## Сборка

```bash
cd miniapp
npm run build
npm run preview -- --host 0.0.0.0 --port 3000
```

## Модели (sprite front/back)

Модели лежат в `miniapp/public/assets/models/` и представлены 6 PNG:
- `f_slim.png`
- `f_std.png`
- `f_bulk.png`
- `m_slim.png`
- `m_std.png`
- `m_bulk.png`

Каждый PNG содержит две половины:
- левая половина: `front`
- правая половина: `back`

Переключение `front/back` делается в рендере (`Stage.tsx`) через SVG crop/offset без нарезки файлов.

## Зоны тела

Конфиг интерактивных зон находится в `miniapp/src/data/bodyZones.ts`.
Поддерживаемые coarse-ключи:
- `arm`
- `leg`
- `back`
- `chest`
- `neck`
- `other`

Выбранная зона подсвечивается и участвует в расчете цены.

## Telegram WebApp

Инициализация сделана в `miniapp/src/hooks/useTelegramWebApp.ts`:
- `window.Telegram.WebApp.ready()`
- `window.Telegram.WebApp.expand()`

Тема подхватывается через CSS переменные Telegram (`--tg-theme-*`) с fallback-значениями.
