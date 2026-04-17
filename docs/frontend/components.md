# Frontend Components

The frontend composes two families of UI:

1. **View components** — screen-level compositions under `src/app/components/`
2. **UI primitives** — [shadcn/ui](https://ui.shadcn.com/) wrappers around Radix UI under `src/app/components/ui/`

On top of that, WELS-branded chrome (navigation, page headers, cards) is available
as plain CSS classes from `src/styles/wels.css`.

## View components

### `<App />` — `src/app/App.tsx`

Owns the single `AppState` state machine:

```ts
type AppState = 'dashboard' | 'upload' | 'processing' | 'results';
```

Transitions:

- `dashboard → upload` via `onNewUpload`
- `upload → processing` on file selection (auto-starts)
- `processing → results` once mock progress hits 100%
- `* → dashboard` via `handleReset`

### `<Dashboard />` — `Dashboard.tsx`

Match history grid with search, sort, and quick-stat cards. Invokes `onNewUpload`
to switch to the upload flow, or `onViewMatch` to jump into an existing analysis.

### `<VideoUpload />` — `VideoUpload.tsx`

Drag-and-drop / file-picker surface. Calls `onVideoUpload(file)` when a video is
selected.

### `<ProcessingStatus />` — `ProcessingStatus.tsx`

Progress bar with the current pipeline step text. Driven by `progress` and
`currentStep` props owned by `<App />`.

### `<AnalysisResults />` — `AnalysisResults.tsx`

Tabbed results view: overview, formations, offensive plays, shot positions, heatmap,
player stats, event timeline, and quality metrics.

## UI primitives (shadcn/ui)

`src/app/components/ui/` contains ~50 shadcn primitives wrapping Radix UI. All are
typed, accessible, and themed via the CSS variables declared in
`src/styles/theme.css`. Import them directly:

```tsx
import { Button } from "@/app/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/app/components/ui/card";
import { Dialog, DialogContent, DialogTrigger } from "@/app/components/ui/dialog";
```

The `@/` alias is wired in `vite.config.ts` and `tsconfig.app.json`.

Full roster: `accordion`, `alert`, `alert-dialog`, `aspect-ratio`, `avatar`, `badge`,
`breadcrumb`, `button`, `calendar`, `card`, `carousel`, `chart`, `checkbox`,
`collapsible`, `command`, `context-menu`, `dialog`, `drawer`, `dropdown-menu`,
`form`, `hover-card`, `input`, `input-otp`, `label`, `menubar`, `navigation-menu`,
`pagination`, `popover`, `progress`, `radio-group`, `resizable`, `scroll-area`,
`select`, `separator`, `sheet`, `sidebar`, `skeleton`, `slider`, `sonner`, `switch`,
`table`, `tabs`, `textarea`, `toggle`, `toggle-group`, `tooltip`.

## WELS semantic classes

From `src/styles/wels.css` — preserved from the previous frontend so WELS-branded
chrome stays consistent:

| Class | Use |
|-------|-----|
| `.nav`, `.nav__inner`, `.nav__brand`, `.nav__link`, `.nav__links` | Top navigation bar, navy background |
| `.main` | Centered main content column (max-width 72rem) |
| `.footer` | Muted footer strip |
| `.page-header`, `.page-header__title`, `.page-header__subtitle` | Page-level heading |
| `.section-heading` | Blue sub-section heading |
| `.card` | White card with border and `--shadow-sm` |
| `.btn-primary` | WELS-blue button |
| `.empty-state` | Centered empty-state block |
| `.loading-placeholder` | Pulsing muted text |

Example:

```tsx
<nav className="nav">
  <div className="nav__inner">
    <a href="/" className="nav__brand">WELS</a>
    <div className="nav__links">
      <a href="/" className="nav__link">Dashboard</a>
    </div>
  </div>
</nav>

<main className="main">
  <header className="page-header">
    <h1 className="page-header__title">Dashboard</h1>
    <p className="page-header__subtitle">Match intelligence at a glance.</p>
  </header>
  {/* … */}
</main>
```

## Adding a new view component

1. Create a new file under `src/app/components/`, e.g. `TeamStats.tsx`.
2. Export a named functional component with typed props:
   ```tsx
   interface TeamStatsProps {
     matchId: string;
     onSelectPlayer: (playerId: number) => void;
   }
   export function TeamStats({ matchId, onSelectPlayer }: TeamStatsProps) { /* … */ }
   ```
3. Compose from shadcn primitives + Tailwind utility classes + WELS brand tokens.
4. Wire it into `App.tsx` (or a route, once routing is introduced).

## Adding a new shadcn primitive

Use the [shadcn CLI](https://ui.shadcn.com/docs/cli) against a tsconfig that includes
the `@/` alias, or copy the source manually into `src/app/components/ui/`. The theme
CSS variables already cover every shadcn token, so new primitives pick up WELS
branding automatically.
