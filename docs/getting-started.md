# Getting Started

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — install with `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Setup

Clone the repo and run the setup command:

```bash
git clone <repo-url> && cd wels-monorepo
make setup
```

This will:

1. Create virtual environments for both `packages/backend` and `packages/frontend`
2. Install all dependencies (including dev extras)
3. Download the moon task runner binary
4. Install pre-commit hooks

## Running Locally

Start the entire platform with a single command:

```bash
make dev
```

This launches:

| Service | URL |
|---------|-----|
| Backend API | [http://localhost:8000](http://localhost:8000) |
| Frontend | [http://localhost:3000](http://localhost:3000) |

Press `Ctrl+C` to stop all services.

To run services individually:

```bash
make run-backend    # Backend only
make run-frontend   # Frontend only
```

## Common Commands

```bash
make lint           # Lint both packages with ruff
make format         # Auto-format both packages
make typecheck      # Type check both packages with ty
make test           # Run all tests
make test-integration  # Integration tests only
make test-ui        # UI tests only (frontend)
make docs           # Serve documentation locally
```

## Adding Dependencies

Each package has its own virtual environment:

```bash
cd packages/backend && uv add <package>
cd packages/frontend && uv add --dev <package>
```
