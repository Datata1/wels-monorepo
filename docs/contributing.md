# Contributing

## Development Workflow

1. Create a feature branch from `main`
2. Make changes and ensure checks pass:
   ```bash
   make lint && make typecheck && make test
   ```
3. Commit — pre-commit hooks run ruff (lint + format) and ty (typecheck) automatically
4. Open a pull request — GitHub Actions runs the full check suite

## Code Style

Code style is enforced automatically:

- **ruff** — linting and formatting (config in `ruff.toml`)
- **ty** — type checking (config in `ty.toml`, all rules as errors)
- **pre-commit** — runs both on every commit

See [python.instructions.md](https://github.com/your-org/wels-monorepo/blob/main/.github/instructions/python.instructions.md) for the full coding standard.

### Key Rules

- Annotate **every** function signature (parameters + return type)
- Use Pydantic `BaseModel` for all domain data — never raw dicts across boundaries
- Use `Literal` types for known string value sets
- All FastAPI routes are `async def` with a `response_model`
- Use `httpx.AsyncClient` as a context manager with explicit timeouts

## Testing

```bash
make test               # All tests
make test-integration   # Integration tests only
make test-ui            # UI tests only (frontend)
```

Tests use pytest with markers:

- `@pytest.mark.integration` — end-to-end API tests
- `@pytest.mark.ui` — HTML structure and content assertions
- `@pytest.mark.unit` — isolated unit tests (default)

### Test naming convention

```
test_<what>_<condition>_<expected>
```

Example: `test_get_match_not_found_returns_404`

## Adding Dependencies

```bash
cd packages/backend && uv add <package>           # Runtime dependency
cd packages/frontend && uv add --dev <package>     # Dev dependency
```

## Documentation

```bash
make docs        # Serve docs locally at http://localhost:8000
make docs-build  # Build static site to site/
```

Docs are written in Markdown under `docs/`. API reference is auto-generated from Python docstrings via mkdocstrings.
