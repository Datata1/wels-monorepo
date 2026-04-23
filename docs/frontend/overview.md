# Frontend Overview

The frontend is a **React 18 + Vite** single-page application written in TypeScript.
It renders the handball analytics dashboard, fetches data from the backend API, and
uses [shadcn/ui](https://ui.shadcn.com/) primitives on top of Tailwind CSS v4 for
presentation.

## Running

```bash
make run-frontend
# → http://localhost:3000 (Vite dev server, HMR enabled)
```

Or directly via moon:

```bash
./tools/moon run frontend:run
```

A production build is generated with:

```bash
make build-frontend      # or: ./tools/moon run frontend:build
```

The output lands in `packages/frontend/dist/`.

## Configuration

The dev server is pinned to port 3000 via `package.json` (`--strictPort`). The
backend URL is read from a Vite env var at runtime:

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_BACKEND_URL` | `http://localhost:8000` | Backend API base URL, available at `import.meta.env.VITE_BACKEND_URL` |

Put environment variables in `packages/frontend/.env.local` (gitignored).

## Project Structure

```
packages/frontend/
├── package.json              # React + Vite + shadcn deps, scripts
├── pnpm-lock.yaml            # pnpm lockfile (committed)
├── tsconfig.json             # Root TS project (composite)
├── tsconfig.app.json         # App sources (strict, bundler resolution)
├── tsconfig.node.json        # vite.config.ts, eslint.config.js
├── vite.config.ts            # React + Tailwind v4 plugin, @/ → src/ alias
├── eslint.config.js          # Flat config: tseslint + react-hooks + react-refresh
├── postcss.config.mjs        # Empty — Tailwind v4 handles PostCSS internally
├── index.html                # Vite HTML entry
├── moon.yml                  # setup / run / lint / typecheck / build
└── src/
    ├── main.tsx              # React entry, mounts <App />
    ├── app/
    │   ├── App.tsx           # Top-level routing: dashboard / upload / processing / results
    │   └── components/
    │       ├── Dashboard.tsx
    │       ├── VideoUpload.tsx
    │       ├── ProcessingStatus.tsx
    │       ├── AnalysisResults.tsx
    │       ├── figma/
    │       │   └── ImageWithFallback.tsx
    │       └── ui/           # shadcn/ui primitives (button, card, dialog, …)
    ├── imports/
    │   └── Logo.png
    └── styles/
        ├── index.css         # Entry: pulls the four stylesheets below
        ├── fonts.css         # @font-face declarations (if any)
        ├── tailwind.css      # Tailwind v4 source + custom keyframes (blob animation)
        ├── theme.css         # shadcn CSS vars remapped to WELS brand tokens
        └── wels.css          # WELS semantic classes: .nav, .card, .page-header, …
```

## How It Works

1. Browser loads `index.html`, which boots `src/main.tsx`.
2. `main.tsx` imports `styles/index.css` (which chains `fonts → tailwind → theme → wels`) and mounts `<App />`.
3. `App.tsx` owns a single `AppState` (`dashboard | upload | processing | results`) and swaps between the four view components.
4. View components are plain React functional components using Tailwind utility classes and shadcn primitives.
5. For real data, components will call the backend over HTTP (via `fetch` or a client of your choice). Today the dashboard uses mock data generated inline — see `generateMockAnalysis()` in `Dashboard.tsx` / `App.tsx`.

## CSS architecture

There are two layered systems composed in `src/styles/index.css`:

### shadcn theme (`theme.css`)

Defines every CSS variable the shadcn/ui primitives read (`--background`, `--primary`,
`--card`, `--ring`, `--chart-1..5`, sidebar vars, …) and a `@theme inline` block that
exposes them to Tailwind. All colour variables resolve to WELS brand tokens:

```css
--primary: var(--color-wels-blue);
--destructive: var(--color-wels-accent);
--ring: var(--color-wels-accent);
--sidebar-primary: var(--color-wels-navy);
```

A `.dark` override remaps the same variables for dark mode.

### WELS semantic classes (`wels.css`)

Preserved verbatim from the previous HTMX frontend. Provides `.nav`, `.nav__brand`,
`.page-header`, `.section-heading`, `.card`, `.btn-primary`, `.empty-state`,
`.loading-placeholder`, plus spacing (`--sp-*`) and radius (`--radius-wels-*`) tokens.
Use these when a component needs WELS-branded chrome rather than a shadcn primitive.

### Brand tokens

`theme.css` defines the brand palette at the top of `:root`:

```css
--color-wels-dark: #1a1a2e;
--color-wels-navy: #16213e;
--color-wels-blue: #0f3460;
--color-wels-accent: #e94560;
```

Always reference these via `var(--color-wels-*)` rather than hard-coding hex values.

## Adding dependencies

```bash
cd packages/frontend
pnpm add <package>         # runtime
pnpm add -D <package>      # dev
```

Then re-run setup so moon's cache picks up the new `pnpm-lock.yaml`:

```bash
./tools/moon run frontend:setup
```

## Tooling summary

| Tool | Purpose |
|------|---------|
| [Vite 6](https://vitejs.dev/) | Dev server + bundler |
| [React 18](https://react.dev/) + TypeScript 5 | UI framework |
| [Tailwind CSS v4](https://tailwindcss.com/) via `@tailwindcss/vite` | Styling |
| [shadcn/ui](https://ui.shadcn.com/) + [Radix UI](https://www.radix-ui.com/) | Accessible component primitives |
| [motion](https://motion.dev/) | Animations |
| [lucide-react](https://lucide.dev/) | Icon set |
| [recharts](https://recharts.org/) | Charts |
| [eslint](https://eslint.org/) + [typescript-eslint](https://typescript-eslint.io/) | Linting |
| [tsc](https://www.typescriptlang.org/) | Type checking (`tsc -b --noEmit`) |
| [pnpm 9](https://pnpm.io/) | Package manager, installed via the moon node toolchain |
