Add a dependency to a package in the wels-monorepo. The request: $ARGUMENTS

Determine from the request:
- **Which package**: `backend`, `frontend`, or another package under `packages/`
- **Runtime or dev**: dev deps (testing tools, linters, type checkers) use `--dev`

Run the appropriate uv command:

```bash
# Runtime dependency
cd packages/<package> && uv add <dep>

# Dev dependency
cd packages/<package> && uv add --dev <dep>
```

After running, verify the dep appears in the relevant section of `packages/<package>/pyproject.toml`.

If the dependency changes import paths or requires config (e.g. a new pytest plugin needing an ini key), make that change too. Otherwise stop — don't add boilerplate usage examples or demo code.
