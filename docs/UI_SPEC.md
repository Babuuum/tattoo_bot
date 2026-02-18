# Mini App UI Spec (Try-On)

## 1. Screen Layout (mobile-first)
Single-screen composition:
1. Header
2. Main stage (model + tattoo overlay)
3. Left controls (gender/body/view)
4. Right panel (selected tattoo + size)
5. Bottom bar (price + CTA)
6. Gallery bottom-sheet (overlay + sheet)

## 2. Visual Rules
- No interactive body zones.
- Center stage is static 2D silhouette image.
- Tattoo appears as image overlay centered on stage.
- Size affects overlay scale only (`S/M/L`) + price.

## 3. Controls
### LeftControls
- Gender: `M`, `Ж`
- Body: `Худое`, `Стандарт`, `Плотное`
- View: `Front`, `Back`

### RightPanel
- Selected tattoo preview + name/style
- Size switch: `S`, `M`, `L`

### BottomBar
- Final price text
- CTA button (`Продолжить`)

## 4. GallerySheet Behavior
- Open via `Галерея →`
- Close via:
  - close button
  - overlay click
  - Escape key (desktop preview)
- Contains:
  - search input
  - style filter chips
  - responsive tattoo grid
- Selecting tile:
  - updates selected tattoo
  - closes sheet

## 5. Data-UI Bindings
- Model image source:
  - `assets/models/{gender}_{body}_{view}.png`
- Tattoo image source:
  - `assets/tattoos/{id}.png`
- Filters and search apply to tattoo list in real-time.

## 6. CSS/Theming Recommendations
Use CSS custom properties:
- `--bg`, `--text`, `--hint`, `--stroke`
- `--accent`, `--accent2`
- `--r-lg`, `--r-md`, `--r-sm`

Telegram theme mapping:
- defaults from `--tg-theme-bg-color`, `--tg-theme-text-color`
- keep fallbacks for browser mode

## 7. Interaction Edge Cases
- **Sheet scroll**: sheet content scrolls independently.
- **Body scroll lock**: while sheet open, prevent background body scroll.
- **Safe area**: top/bottom paddings via `env(safe-area-inset-*)`.
- **No results**: show empty gallery state.
- **Broken image**: graceful placeholder.

## 8. Component List (required)
- `AppShell`
- `Header`
- `Stage`
- `LeftControls`
- `RightPanel`
- `BottomBar`
- `GallerySheet`
- `GalleryGrid`
- `PriceCalculator`
