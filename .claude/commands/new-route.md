Scaffold a new route in the WELS monorepo. The request: $ARGUMENTS

First read the existing routes to understand current patterns:
- Backend: packages/backend/src/backend/routes/__init__.py
- Frontend: packages/frontend/src/frontend/routes/__init__.py

Determine from the request whether this is a **backend** or **frontend** route.

## Backend route (packages/backend)

- Add the handler to `packages/backend/src/backend/routes/__init__.py` using the existing APIRouter
- If request/response shape is non-trivial, add a Pydantic model to `packages/backend/src/backend/models.py`
- Add a test in `packages/backend/tests/test_<feature>.py` that uses the existing async HTTP client fixture from conftest.py
- Integration tests go in `packages/backend/tests/integration/` and must be marked `@pytest.mark.integration`

## Frontend route (packages/frontend)

- HTMX partials belong under the `/partials` prefix in `packages/frontend/src/frontend/routes/__init__.py`
- Return `TemplateResponse` with the appropriate Jinja2 template
- Create or update the template in `packages/frontend/src/frontend/templates/`
- Add tests in `packages/frontend/tests/`; HTML-structure tests using BeautifulSoup go in `tests/ui/`

## Conventions

- Type all parameters and return values
- Use double quotes, 100-char line length (ruff config)
- Snake_case for Python identifiers, kebab-case for URL paths
- No extra boilerplate beyond what the task requires
