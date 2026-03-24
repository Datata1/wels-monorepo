---
description: "Python code quality standards for the WELS monorepo: type annotations, Pydantic models, FastAPI patterns, async conventions, project structure, and testing practices"
applyTo: "**/*.py"
---

# Python Code Standards — WELS Monorepo

## Language & Runtime
* Python ≥ 3.12. Use modern syntax: `list[X]` not `List[X]`, `X | None` not `Optional[X]`, `type` statements for aliases.
* Tooling: **uv** (package manager), **ruff** (lint + format), **ty** (type checker), **pytest** (tests).
* Line length: 100. Quotes: double. Formatter enforces both — don't fight it.

## Type Annotations
* **Annotate every function signature** — parameters and return type. No exceptions.
* Prefer concrete types over `Any`. Use `Any` only at true FFI / serialization boundaries.
* Use `X | None` for optional values, never bare `Optional`.
* Use built-in generics: `list[str]`, `dict[str, int]`, `tuple[int, ...]`.
* For complex types, define a `type` alias at module level:
  ```python
  type JsonDict = dict[str, Any]
  ```
* Annotate class attributes and instance variables, including Pydantic fields.
* Use `Self` (from `typing`) for fluent / builder return types.

## Pydantic
* All domain data flows through **Pydantic `BaseModel`** subclasses — never raw dicts across boundaries.
* Use `model_config` dict, never the legacy `class Config`:
  ```python
  model_config = {"env_prefix": "WELS_", "frozen": True}
  ```
* Use `Field()` for validation, defaults, and descriptions:
  ```python
  goals: int = Field(default=0, ge=0, description="Goals scored")
  ```
* Use **field validators** (`@field_validator`) and **model validators** (`@model_validator`) over `__init__` overrides.
* Constrain string fields with `Literal` types where the value set is known:
  ```python
  status: Literal["completed", "live", "upcoming"]
  event_type: Literal["goal", "save", "turnover", "timeout", "substitution"]
  ```
* Configuration / settings use `pydantic_settings.BaseSettings` with an explicit `env_prefix`.
* Never call `.dict()` — use `.model_dump()`. Never call `.json()` — use `.model_dump_json()`.

## FastAPI
* Declare `response_model` on every route. Let FastAPI serialize — don't manually call `jsonable_encoder`.
* Use `APIRouter` with a `prefix` and `tags` for logical grouping.
* Use dependency injection (`Depends`) for shared resources (DB sessions, auth, settings).
* Path parameters get type-annotated in the function signature; FastAPI validates them.
* Raise `HTTPException` for error responses — never return raw `{"error": ...}` dicts.
* All route handlers are `async def`. Use `async with` for HTTP clients and DB connections.
* Add a one-line docstring to every route — it becomes the OpenAPI description.

## Async / HTTP Clients
* Use `httpx.AsyncClient` as an async context manager — never leave connections open.
* Always set an explicit `timeout` on external HTTP calls.
* Prefer `response.raise_for_status()` over manual status code checks.
* Catch specific exceptions (`httpx.HTTPError`, `httpx.TimeoutException`) — not bare `except`.

## Project Structure
* Each package follows the **`src/` layout**: `packages/<name>/src/<name>/`.
* One router per domain in `routes/`, exported via `__init__.py`.
* Keep models in `models.py` (or a `models/` package for large domains).
* Config stays in `config.py` using `BaseSettings`.
* Avoid circular imports: models → no app imports; routes → can import models + config.

## Naming
* Modules and packages: `snake_case`.
* Classes: `PascalCase`. Pydantic models are nouns: `Match`, `PlayerStats`, `TeamOverview`.
* Functions and variables: `snake_case`. Prefix booleans with `is_`, `has_`, `should_`.
* Constants: `UPPER_SNAKE_CASE`.
* Private / internal helpers: single leading underscore `_fetch_json()`.

## Code Style
* **Guard clauses / early returns** to reduce nesting — don't wrap whole functions in `if`.
* One import per line for third-party; group: stdlib → third-party → first-party (ruff + isort enforces this).
* No mutable default arguments (ruff's `B006` catches this).
* Prefer list/dict/set comprehensions over `map()`/`filter()` with lambdas.
* Use f-strings for interpolation, never `%` or `.format()`.
* `pathlib.Path` for file system operations, not `os.path`.

## Error Handling
* Only catch exceptions you can meaningfully handle.
* Never use bare `except:` or `except Exception:` unless re-raising.
* Log the original exception with `from` when wrapping: `raise AppError(...) from e`.
* At API boundaries (routes), catch domain exceptions and map to `HTTPException`.

## Testing
* Tests live in `tests/` at the package root, mirroring `src/` structure.
* Use pytest markers: `@pytest.mark.integration`, `@pytest.mark.ui`, `@pytest.mark.unit`.
* Test names: `test_<what>_<condition>_<expected>` — e.g., `test_get_match_not_found_returns_404`.
* Use `httpx.ASGITransport` for testing FastAPI apps — not `TestClient` (we're async-native).
* Mock external HTTP calls, never make real network requests in tests.
* Use `conftest.py` for shared fixtures — keep fixture scope as narrow as possible.
* Assert behavior, not implementation. Test public API, not private methods.
* Each test should be independent — no shared mutable state between tests.

## Documentation
* Module-level docstring for files containing non-trivial logic.
* One-line docstrings for routes and public functions. Multi-line only when parameters need explanation.
* Don't add docstrings or comments to code you didn't write or change.
* Comments explain *why*, never *what* — the code shows what.

## What NOT to Do
* Don't add `# type: ignore` without a specific error code and justification comment.
* Don't use `datetime.datetime.now()` without a timezone — use `datetime.now(tz=UTC)`.
* Don't store secrets in code or config files — use environment variables.
* Don't add empty `__init__.py` with only `pass` — leave them truly empty or add `__all__`.
* Don't over-abstract — no factory classes or service layers until the second concrete use case.
