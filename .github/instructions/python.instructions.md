---
description: "Python code quality standards for the WELS monorepo: type annotations, Pydantic models, FastAPI patterns, async conventions, DuckDB access, PyTorch/ML patterns, and testing practices"
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
* All domain data that crosses HTTP or config boundaries flows through **Pydantic `BaseModel`** subclasses — never raw dicts.
* Use `model_config` dict, never the legacy `class Config`:
  ```python
  model_config = {"env_prefix": "WELS_", "frozen": True}
  ```
* Use `Field()` for validation, defaults, and descriptions.
* Use `Literal` types where the value set is known:
  ```python
  team: Literal["A", "B", "unknown"]
  action: Literal["pass", "shot", "dribble", "hold"]
  ```
* Configuration / settings use `pydantic_settings.BaseSettings` with `env_prefix = "WELS_"`.
* Never call `.dict()` — use `.model_dump()`. Never call `.json()` — use `.model_dump_json()`.

## Internal data (ingestion pipeline)
* Data passed **between pipeline stages** uses `@dataclass`, not Pydantic — stages are internal and don't need validation overhead.
* Use `@dataclass(frozen=True)` for value objects that shouldn't mutate after creation (`BoundingBox`, `Detection`, `Keypoint`).
* Mutable stage outputs (`PlayerState`, `FrameState`) use plain `@dataclass`.
* Define all shared types in `ingestion.types` — never define types inside pipeline modules.

## FastAPI
* Declare `response_model` on every route.
* Use `APIRouter` with `prefix` and `tags`.
* Use dependency injection (`Depends`) for shared resources.
* Raise `HTTPException` for errors — never return raw `{"error": ...}` dicts.
* All route handlers are `async def`.
* Add a one-line docstring to every route — it becomes the OpenAPI description.

## Async / HTTP Clients
* Use `httpx.AsyncClient` as an async context manager — never leave connections open.
* Always set an explicit `timeout` on external HTTP calls.
* Prefer `response.raise_for_status()` over manual status code checks.

## DuckDB
* **Read-only by default**: open connections with `read_only=True` unless writing. The `ml` package never writes.
  ```python
  conn = duckdb.connect("data/matches.duckdb", read_only=True)
  ```
* Use parameterised queries — never f-string SQL:
  ```python
  conn.execute("SELECT * FROM players WHERE match_id = ?", [match_id])
  ```
* Keep all SQL in `storage/` (ingestion) or `data/features.py` (ml). No inline SQL in orchestrators, models, or routes.
* Commit explicitly after writes — don't rely on auto-commit:
  ```python
  conn.execute("INSERT INTO ...")
  conn.commit()
  ```
* Close connections when done. Use the `FrameWriter` context manager for bulk writes.

## PyTorch / ML
* Always move tensors and models to the same device before operations:
  ```python
  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
  model = model.to(device)
  graphs = [g.to(device) for g in graphs]
  ```
* Wrap inference in `torch.no_grad()` — never run a forward pass outside it during evaluation or serving.
* Use `weights_only=True` when loading checkpoints:
  ```python
  model.load_state_dict(torch.load(path, map_location=device, weights_only=True))
  ```
* `nn.Module` subclasses contain only model logic — no file I/O, no DuckDB, no config reading.
* Training state (optimizer, loss, epoch loop) lives in `training/train.py`, not in the model class.
* Annotate numpy arrays as `np.ndarray` with `# type: ignore[type-arg]` (numpy generic arrays aren't fully supported by ty yet).

## Ingestion pipeline modules
* `pipeline/` modules are **pure**: take typed inputs, return typed outputs. No file I/O, no DB calls, no global mutable state.
* Every public class in `pipeline/` follows the same lifecycle contract:
  - `__init__`: load weights / initialise state
  - Named methods: take data in, return data out
* The `NotImplementedError` stubs exist to define the interface before the implementation is ported. Keep the signature exactly — only fill in the body.
* When porting from CV-POC: copy logic, adapt to typed inputs/outputs, remove any global state or print statements.

## Project Structure
* Each package follows the **`src/` layout**: `packages/<name>/src/<name>/`.
* Config stays in `config.py` using `BaseSettings`.
* Avoid circular imports: `types` → no other internal imports; `pipeline/` → only `types`; `storage/` → only `types`.

## Naming
* Modules and packages: `snake_case`.
* Classes: `PascalCase`. Models are nouns: `Match`, `FrameState`, `ActionPredictor`.
* Functions and variables: `snake_case`. Prefix booleans with `is_`, `has_`, `should_`.
* Constants: `UPPER_SNAKE_CASE`.
* Private helpers: single leading underscore `_compute_velocities()`.

## Code Style
* Guard clauses / early returns to reduce nesting.
* One import per line for third-party; group: stdlib → third-party → first-party (ruff enforces).
* No mutable default arguments.
* Prefer list/dict/set comprehensions over `map()`/`filter()` with lambdas.
* Use f-strings for interpolation. `pathlib.Path` for filesystem operations.

## Error Handling
* Only catch exceptions you can meaningfully handle.
* Never use bare `except:` or `except Exception:` unless re-raising.
* Log the original exception with `from` when wrapping: `raise AppError(...) from e`.
* At API boundaries, catch domain exceptions and map to `HTTPException`.

## Testing
* Tests live in `tests/` at the package root.
* Use pytest markers: `@pytest.mark.integration`, `@pytest.mark.unit`.
  - `integration`: requires a GPU, a real video file, or a populated DuckDB. Excluded from CI.
  - `unit`: no external deps — runs anywhere, including CI.
* Test names: `test_<what>_<condition>_<expected>`.
* Ingestion unit tests use an in-memory DuckDB connection (`:memory:`), never the real database file.
* ML unit tests build graphs from synthetic frame dicts — never query DuckDB.
* Assert behavior, not implementation. Test public API, not private methods.

## Documentation
* Module-level docstring for files containing non-trivial logic.
* One-line docstrings for routes and public functions.
* Comments explain *why*, never *what*.
* Don't add docstrings or comments to code you didn't write or change.

## What NOT to Do
* Don't add `# type: ignore` without a specific error code and justification comment.
* Don't store secrets in code or config files — use environment variables.
* Don't import between packages (`ingestion` must not import `ml`, etc.).
* Don't write SQL outside `storage/` or `data/features.py`.
* Don't run torch operations outside `torch.no_grad()` during inference.
* Don't use mutable default arguments — ruff's `B006` catches this.
