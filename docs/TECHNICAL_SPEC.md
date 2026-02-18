# Mini App Technical Spec (Vite + React + TypeScript)

## 1. Scope
Цель: подготовить архитектуру Mini App "Примерка" (mobile-first), без интерактивных зон тела.

Вне scope:
- drag&drop, hitmap/zone selection
- сложная 3D/Canvas сцена
- внедрение фронт-фреймворков кроме React

## 2. Stack
- Build/runtime: `Vite`
- UI: `React`
- Language: `TypeScript`
- Styling: plain CSS + CSS variables (без CSS-in-JS)
- State: React hooks (`useState`, `useMemo`), без Redux/Zustand
- Telegram: `@telegram-apps/sdk` (или fallback на `window.Telegram.WebApp`)

## 3. Project Structure
```text
miniapp/
  package.json
  pnpm-lock.yaml
  tsconfig.json
  vite.config.ts
  index.html
  src/
    main.tsx
    App.tsx
    app/
      AppShell.tsx
      providers/
        TelegramProvider.tsx
    components/
      Header/
      Stage/
      LeftControls/
      RightPanel/
      BottomBar/
      GallerySheet/
      GalleryGrid/
      PriceCalculator/
    domain/
      pricing/
        model.ts
        calc.ts
      fitting/
        model.ts
        selectors.ts
    data/
      tattoos.mock.ts
      models.mock.ts
      filters.mock.ts
    styles/
      variables.css
      base.css
      components.css
    assets/
      models/
      tattoos/
```

## 4. Component Responsibilities
- `AppShell`: root layout, safe-area paddings, orchestration.
- `Header`: title + utility actions.
- `Stage`: model image + tattoo overlay image.
- `LeftControls`: gender/body/view toggles.
- `RightPanel`: selected tattoo card + size switch S/M/L.
- `BottomBar`: final price + CTA.
- `GallerySheet`: bottom-sheet container, open/close, search/filter toolbar.
- `GalleryGrid`: filtered tattoo list and selection.
- `PriceCalculator`: pure UI/helper wrapper around pricing output.

## 5. State Model (minimum)
```ts
type Gender = 'm' | 'f';
type Body = 'slim' | 'std' | 'bulk';
type View = 'front' | 'back';
type Size = 's' | 'm' | 'l';

type TattooItem = {
  id: string;
  name: string;
  style: 'linework' | 'blackwork' | 'minimal' | 'japan';
  label: string;
  src: string;
};

type FittingState = {
  gender: Gender;
  body: Body;
  view: View;
  size: Size;
  selectedTattoo: TattooItem;
  galleryOpen: boolean;
  search: string;
  styleFilter: 'all' | TattooItem['style'];
};
```

Derived data:
- `modelSrc = assets/models/{gender}_{body}_{view}.png`
- `filteredTattoos` по `search + styleFilter`
- `price` через pricing formula
- `overlayScale` по размеру S/M/L

## 6. Mock Data Location
- `src/data/models.mock.ts`: карта `gender_body_view -> image path`
- `src/data/tattoos.mock.ts`: массив тату
- `src/data/filters.mock.ts`: конфиг фильтров sheet

## 7. Pricing (mock)
Formula:
- `final = max(MIN_PRICE, BASE_PRICE * SIZE_K[size] * STYLE_K[tattoo.style])`

Example constants:
- `BASE_PRICE = 5900`
- `MIN_PRICE = 4900`
- `SIZE_K = { s: 1.0, m: 1.25, l: 1.55 }`
- `STYLE_K = { linework: 1.0, blackwork: 1.15, minimal: 0.95, japan: 1.2 }`

## 8. Telegram WebApp Integration
On app bootstrap:
1. `WebApp.ready()`
2. `WebApp.expand()`
3. Sync CSS vars from Telegram theme (or rely on `--tg-theme-*` vars directly)
4. Optional main button wiring deferred

Theme:
- Base CSS variables map to `--tg-theme-bg-color`, `--tg-theme-text-color`, etc.
- Keep fallback values for non-Telegram browser preview.

## 9. UX Edge Cases
- Bottom-sheet open:
  - lock body scroll
  - keep sheet scroll enabled
- Safe-area:
  - `env(safe-area-inset-top/bottom)` in root paddings
- Search edge case:
  - empty results state in grid
- Asset missing:
  - show placeholder/alt fallback, do not crash

## 10. Definition of Done
- Mobile-first page assembled in `miniapp` frontend code.
- No interactive body zones, only static model switching.
- Gallery sheet supports open/close/search/filter/select.
- Tattoo selection updates stage overlay + right panel.
- Size switch updates overlay scale + price.
- Safe-area and body scroll lock implemented.
- `pnpm i`, `pnpm lint`, `pnpm build` pass.
- If tests are added: `pnpm test` pass.
- Backend checks remain green (`pytest`, `ruff`, `black`, `pre-commit`).

## 11. Run / Test Commands
```bash
# frontend
cd miniapp
pnpm i
pnpm lint
pnpm test   # if tests configured
pnpm build

# backend repo checks
cd ..
poetry run pytest -q
poetry run ruff check .
poetry run black --check .
PRE_COMMIT_HOME=/tmp/pre-commit-cache poetry run pre-commit run -a
```
