.PHONY: setup setup-backend setup-frontend setup-tailwind setup-hooks \
       dev run-backend run-frontend \
       lint lint-backend lint-frontend \
       typecheck typecheck-backend typecheck-frontend \
       format format-backend format-frontend \
       test test-backend test-frontend test-integration test-ui \
       tailwind tailwind-watch \
       docs docs-build \
       stop clean

FRONTEND_CSS_IN  := packages/frontend/src/frontend/static/css/input.css
FRONTEND_CSS_OUT := packages/frontend/src/frontend/static/css/style.css
FRONTEND_DIR     := packages/frontend

TAILWIND_VERSION := v4.1.3
TAILWIND_BIN     := tools/tailwindcss

PACKAGES := packages/backend packages/frontend

UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

ifeq ($(UNAME_S),Darwin)
  ifeq ($(UNAME_M),arm64)
    TAILWIND_PLATFORM := macos-arm64
  else
    TAILWIND_PLATFORM := macos-x64
  endif
else ifeq ($(UNAME_S),Linux)
  ifeq ($(UNAME_M),aarch64)
    TAILWIND_PLATFORM := linux-arm64
  else
    TAILWIND_PLATFORM := linux-x64
  endif
else
  TAILWIND_PLATFORM := windows-x64.exe
endif

TAILWIND_URL := https://github.com/tailwindlabs/tailwindcss/releases/download/$(TAILWIND_VERSION)/tailwindcss-$(TAILWIND_PLATFORM)

setup: setup-backend setup-frontend setup-tailwind setup-hooks

setup-backend:
	cd packages/backend && uv sync --all-extras

setup-frontend:
	cd packages/frontend && uv sync --all-extras

setup-hooks:
	cd packages/backend && uv run pre-commit install

setup-tailwind: $(TAILWIND_BIN)

$(TAILWIND_BIN):
	@mkdir -p tools
	@echo "Downloading Tailwind CSS $(TAILWIND_VERSION) for $(TAILWIND_PLATFORM)..."
	@curl -sL $(TAILWIND_URL) -o $(TAILWIND_BIN)
	@chmod +x $(TAILWIND_BIN)
	@echo "Tailwind CSS installed at $(TAILWIND_BIN)"

dev: $(TAILWIND_BIN)
	@echo "Starting WELS platform..."
	@echo "  Backend  → http://localhost:8000"
	@echo "  Frontend → http://localhost:3000"
	@echo "  Docs     → http://localhost:8001"
	@echo "  Tailwind → watching for changes"
	@echo "  Press Ctrl+C to stop all services"
	@trap 'kill 0' INT TERM; \
	 cd packages/backend && uv run uvicorn backend.app:app --reload --port 8000 & \
	 cd packages/frontend && uv run uvicorn frontend.app:app --reload --port 3000 & \
	 cd $(FRONTEND_DIR) && ../../$(TAILWIND_BIN) -i src/frontend/static/css/input.css -o src/frontend/static/css/style.css --watch & \
	 make docs & \
	 wait

run-backend:
	cd packages/backend && uv run uvicorn backend.app:app --reload --port 8000

run-frontend:
	cd packages/frontend && uv run uvicorn frontend.app:app --reload --port 3000

lint: lint-backend lint-frontend

lint-backend:
	cd packages/backend && uv run ruff check src/ tests/

lint-frontend:
	cd packages/frontend && uv run ruff check src/ tests/

typecheck: typecheck-backend typecheck-frontend

typecheck-backend:
	cd packages/backend && uv run ty check --config-file ../../ty.toml src/

typecheck-frontend:
	cd packages/frontend && uv run ty check --config-file ../../ty.toml src/

format: format-backend format-frontend

format-backend:
	cd packages/backend && uv run ruff format src/ tests/

format-frontend:
	cd packages/frontend && uv run ruff format src/ tests/

test: test-backend test-frontend

test-backend:
	cd packages/backend && uv run pytest

test-frontend:
	cd packages/frontend && uv run pytest

test-integration:
	cd packages/backend && uv run pytest -m integration
	cd packages/frontend && uv run pytest -m integration

test-ui:
	cd packages/frontend && uv run pytest -m ui

# ─── Tailwind ───────────────────────────────────────────
tailwind: $(TAILWIND_BIN)
	cd $(FRONTEND_DIR) && ../../$(TAILWIND_BIN) -i src/frontend/static/css/input.css -o src/frontend/static/css/style.css --minify

tailwind-watch: $(TAILWIND_BIN)
	cd $(FRONTEND_DIR) && ../../$(TAILWIND_BIN) -i src/frontend/static/css/input.css -o src/frontend/static/css/style.css --watch

# ─── Docs ───────────────────────────────────────────────
docs:
	cd packages/backend && uv run mkdocs serve -f ../../mkdocs.yml -a localhost:8080

docs-build:
	cd packages/backend && uv run mkdocs build -f ../../mkdocs.yml

clean:
	@for pkg in $(PACKAGES); do \
		echo "Cleaning $$pkg..."; \
		rm -rf $$pkg/.venv $$pkg/uv.lock; \
	done
