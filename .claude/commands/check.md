Run the full quality check suite for the wels-monorepo. Execute each step and report results clearly.

Steps (run sequentially so failures are visible):
1. `make lint` — ruff check on both packages
2. `make typecheck` — ty type checking on both packages
3. `make test` — pytest on both packages (all markers)

After all three complete, summarize with a table:

| Check | Result |
|-------|--------|
| Lint  | ✅ / ❌ |
| Types | ✅ / ❌ |
| Tests | ✅ / ❌ |

If anything failed, quote the relevant error lines and suggest the fix. Do not propose unrelated changes.
