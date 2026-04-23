Run the full quality check suite for the wels-monorepo. Execute each step and report results clearly.

Steps (run sequentially so failures are visible):
1. `make lint` — ruff check on all packages (backend, frontend, ingestion, ml)
2. `make typecheck` — ty type checking on all packages
3. `make test` — pytest on all packages, excluding integration tests (`-m "not integration"`)

After all three complete, summarise with a table:

| Check | Backend | Frontend | Ingestion | ML |
|-------|---------|----------|-----------|-----|
| Lint  | ✅ / ❌ | ✅ / ❌  | ✅ / ❌   | ✅ / ❌ |
| Types | ✅ / ❌ | ✅ / ❌  | ✅ / ❌   | ✅ / ❌ |
| Tests | ✅ / ❌ | ✅ / ❌  | ✅ / ❌   | ✅ / ❌ |

If anything failed, quote the relevant error lines and suggest the fix. Do not propose unrelated changes.

Note: integration tests (marked `@pytest.mark.integration`) require a GPU and real video/DuckDB data — they are intentionally excluded here. Run them manually with `make test-integration` on a machine with a GPU.
