# Manual Test: Mini App MVP

## Preconditions
- Backend and bot are running.
- Mini App URL opens `/miniapp` in browser/Telegram WebApp.

## Core Scenario
1. Open Mini App screen (`/miniapp`).
2. Verify the main try-on screen is visible (model in center, controls left/right, price bar at bottom).
3. Tap `Галерея →`.
4. Verify bottom-sheet opens.
5. Select any tattoo from the grid.
6. Verify sheet closes and tattoo overlay changes on the stage.
7. Change size `S -> M -> L`.
8. Verify tattoo overlay scale changes and price updates.
9. Change `Пол` and `Вид` in left controls.
10. Verify model changes by crop of one sprite image:
   - `front` uses left half
   - `back` uses right half
11. Tap body zones on the model (`arm/leg/chest/back/neck/other`).
12. Verify selected zone is highlighted and text in right panel updates.
13. Verify price is recalculated with selected body part.

## View Switch Mapping Check
1. Select `chest` on `front`.
2. Switch to `back`.
3. Verify body part is normalized to `back`.
4. Select `back` on `back`, switch to `front`.
5. Verify body part is normalized to `chest`.

## Scroll Lock Check
1. Open gallery sheet.
2. Try to scroll background page: it must stay locked.
3. Scroll inside the sheet grid: it must scroll normally.

## Safe-Area Check
1. Open Mini App on iPhone/Android (or device emulation).
2. Verify bottom bar is fully visible and not clipped by system bottom inset/home indicator.
3. Verify sheet bottom content is not clipped when opened.
