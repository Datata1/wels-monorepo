.PHONY: setup setup-backend setup-frontend setup-moon setup-hooks \
       dev run-backend run-frontend build-frontend \
       lint lint-backend lint-frontend \
       typecheck typecheck-backend typecheck-frontend \
       format format-backend \
       test test-backend test-integration \
       docs docs-build \
       stop clean

MOON_VERSION     := latest
MOON_BIN         := tools/moon

PY_PACKAGES := packages/backend packages/ingestion packages/ml
JS_PACKAGES := packages/frontend

UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

ifeq ($(UNAME_S),Darwin)
  ifeq ($(UNAME_M),arm64)
    MOON_PLATFORM     := aarch64-apple-darwin
  else
    MOON_PLATFORM     := x86_64-apple-darwin
  endif
else ifeq ($(UNAME_S),Linux)
  ifeq ($(UNAME_M),aarch64)
    MOON_PLATFORM     := aarch64-unknown-linux-gnu
  else
    MOON_PLATFORM     := x86_64-unknown-linux-gnu
  endif
else
  MOON_PLATFORM     := x86_64-pc-windows-msvc
endif

MOON_URL     := https://github.com/moonrepo/moon/releases/$(MOON_VERSION)/download/moon_cli-$(MOON_PLATFORM).tar.xz

setup: setup-backend setup-frontend setup-moon setup-hooks

setup-backend:
	cd packages/backend && uv sync --all-extras

setup-frontend: $(MOON_BIN)
	$(MOON_BIN) run frontend:setup

setup-hooks:
	cd packages/backend && uv run pre-commit install

setup-moon: $(MOON_BIN)

$(MOON_BIN):
	@mkdir -p tools
	@echo "Downloading moon for $(MOON_PLATFORM)..."
	@curl -sL $(MOON_URL) | tar -xJf - -C tools --strip-components=1 "moon_cli-$(MOON_PLATFORM)/moon"
	@chmod +x $(MOON_BIN)
	@echo "moon installed at $(MOON_BIN)"

dev: $(MOON_BIN)
	@echo "Starting WELS platform..."
	@echo "  Backend  → http://localhost:8000"
	@echo "  Frontend → http://localhost:3000"
	@echo "  Docs     → http://localhost:8080"
	@echo "  Press Ctrl+C to stop all services"
	@trap 'kill 0; exit 0' INT TERM; \
	 $(MOON_BIN) run backend:run frontend:run 2>&1 & \
	 cd packages/backend && uv run mkdocs serve -f ../../mkdocs.yml -a localhost:8080 & \
	 wait

run-backend:
	cd packages/backend && uv run uvicorn backend.app:app --reload --port 8000

run-frontend: $(MOON_BIN)
	$(MOON_BIN) run frontend:run

build-frontend: $(MOON_BIN)
	$(MOON_BIN) run frontend:build

lint: lint-backend lint-frontend

lint-backend:
	cd packages/backend && uv run ruff check src/ tests/

lint-frontend: $(MOON_BIN)
	$(MOON_BIN) run frontend:lint

typecheck: typecheck-backend typecheck-frontend

typecheck-backend:
	cd packages/backend && uv run ty check --config-file ../../ty.toml src/

typecheck-frontend: $(MOON_BIN)
	$(MOON_BIN) run frontend:typecheck

format: format-backend

format-backend:
	cd packages/backend && uv run ruff format src/ tests/

test: test-backend

test-backend:
	cd packages/backend && uv run pytest

test-integration:
	cd packages/backend && uv run pytest -m integration

docs:
	cd packages/backend && uv run mkdocs serve -f ../../mkdocs.yml -a localhost:8080

docs-build:
	cd packages/backend && uv run mkdocs build -f ../../mkdocs.yml

clean:
	@for pkg in $(PY_PACKAGES); do \
		echo "Cleaning $$pkg..."; \
		rm -rf $$pkg/.venv $$pkg/uv.lock; \
	done
	@for pkg in $(JS_PACKAGES); do \
		echo "Cleaning $$pkg..."; \
		rm -rf $$pkg/node_modules $$pkg/dist; \
	done
