Scaffold a new Python package in the wels-monorepo. The package to create: $ARGUMENTS

Read `packages/backend/pyproject.toml` and `packages/backend/moon.yml` first to mirror the exact conventions.

## Files to create

### `packages/<name>/pyproject.toml`
- Package name: `wels-<name>`
- Python `>=3.12`
- Build system: hatchling
- Runtime deps: add only what's clearly needed
- Dev deps: `pytest>=8.0`, `pytest-asyncio>=0.24`, `httpx>=0.28`, `ruff>=0.9`, `ty>=0.0.25`
- pytest config: `asyncio_mode = "auto"`, markers for `integration` and `ui`, testpaths = `["tests"]`

### `packages/<name>/moon.yml`
Include these tasks mirroring the backend moon.yml:
- `setup`: `uv sync`
- `lint`: `uv run ruff check src/ tests/`
- `format`: `uv run ruff format src/ tests/`
- `typecheck`: `uv run ty check --config ../../ty.toml src/`
- `test`: `uv run pytest`

### Source layout
```
packages/<name>/
  src/<name>/__init__.py
  src/<name>/app.py          # main entrypoint stub
  tests/__init__.py
  tests/conftest.py          # async http client fixture if applicable
```

## After creating files

Tell the user to run:
```bash
cd packages/<name> && uv sync
```

And to verify moon picks it up:
```bash
./tools/moon run <name>:lint
```
