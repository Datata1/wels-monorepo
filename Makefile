.PHONY: setup setup-backend setup-frontend setup-tailwind setup-moon setup-hooks \
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

MOON_VERSION     := latest
MOON_BIN         := tools/moon

PACKAGES := packages/backend packages/frontend

UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

ifeq ($(UNAME_S),Darwin)
  ifeq ($(UNAME_M),arm64)
    TAILWIND_PLATFORM := macos-arm64
    MOON_PLATFORM     := aarch64-apple-darwin
  else
    TAILWIND_PLATFORM := macos-x64
    MOON_PLATFORM     := x86_64-apple-darwin
  endif
else ifeq ($(UNAME_S),Linux)
  ifeq ($(UNAME_M),aarch64)
    TAILWIND_PLATFORM := linux-arm64
    MOON_PLATFORM     := aarch64-unknown-linux-gnu
  else
    TAILWIND_PLATFORM := linux-x64
    MOON_PLATFORM     := x86_64-unknown-linux-gnu
  endif
else
  TAILWIND_PLATFORM := windows-x64.exe
  MOON_PLATFORM     := x86_64-pc-windows-msvc
endif

TAILWIND_URL := https://github.com/tailwindlabs/tailwindcss/releases/download/$(TAILWIND_VERSION)/tailwindcss-$(TAILWIND_PLATFORM)
MOON_URL     := https://github.com/moonrepo/moon/releases/$(MOON_VERSION)/download/moon_cli-$(MOON_PLATFORM).tar.xz

setup: setup-backend setup-frontend setup-tailwind setup-moon setup-hooks

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

setup-moon: $(MOON_BIN)

$(MOON_BIN):
	@mkdir -p tools
	@echo "Downloading moon for $(MOON_PLATFORM)..."
	@curl -sL $(MOON_URL) | tar -xJf - -C tools --strip-components=1 "moon_cli-$(MOON_PLATFORM)/moon"
	@chmod +x $(MOON_BIN)
	@echo "moon installed at $(MOON_BIN)"

dev: $(TAILWIND_BIN) $(MOON_BIN)
	@echo "Starting WELS platform..."
	@echo "  Backend  → http://localhost:8000"
	@echo "  Frontend → http://localhost:3000"
	@echo "  Docs     → http://localhost:8080"
	@echo "  Tailwind → watching for changes"
	@echo "  Press Ctrl+C to stop all services"
	@trap 'kill 0; exit 0' INT TERM; \
	 $(MOON_BIN) run backend:run frontend:run 2>&1 & \
	 cd $(FRONTEND_DIR) && ../../$(TAILWIND_BIN) -i src/frontend/static/css/input.css -o src/frontend/static/css/style.css --watch & \
	 cd packages/backend && uv run mkdocs serve -f ../../mkdocs.yml -a localhost:8080 & \
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

tailwind: $(TAILWIND_BIN)
	cd $(FRONTEND_DIR) && ../../$(TAILWIND_BIN) -i src/frontend/static/css/input.css -o src/frontend/static/css/style.css --minify

tailwind-watch: $(TAILWIND_BIN)
	cd $(FRONTEND_DIR) && ../../$(TAILWIND_BIN) -i src/frontend/static/css/input.css -o src/frontend/static/css/style.css --watch

docs:
	cd packages/backend && uv run mkdocs serve -f ../../mkdocs.yml -a localhost:8080

docs-build:
	cd packages/backend && uv run mkdocs build -f ../../mkdocs.yml

clean:
	@for pkg in $(PACKAGES); do \
		echo "Cleaning $$pkg..."; \
		rm -rf $$pkg/.venv $$pkg/uv.lock; \
	done
