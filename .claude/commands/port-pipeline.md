Port a pipeline stub from CV-POC into the ingestion package. The module to port: $ARGUMENTS

## Context

The ingestion pipeline has four stub modules under `packages/ingestion/src/ingestion/pipeline/`.
Each stub defines the correct interface (class, method signatures, typed inputs/outputs) but raises `NotImplementedError`.
The working implementation exists in `CV-POC-Wels/pipeline/`.

## Steps

1. **Read the stub** — `packages/ingestion/src/ingestion/pipeline/<module>.py`. Note the class name, method signatures, and the `# TODO: port from CV-POC` comments which point to the exact source file and method.

2. **Read the POC source** — the file referenced in the TODO comment (e.g. `CV-POC-Wels/pipeline/detector.py`). Understand what it does, then identify only the logic needed to implement the stub methods.

3. **Implement the stub** — fill in the `__init__` and method bodies. Rules:
   - Keep the existing method signatures exactly — only fill in the bodies
   - Adapt the POC logic to accept/return the typed dataclasses from `ingestion.types` (not raw dicts)
   - Remove any print statements, global variables, or file I/O from inside pipeline methods
   - Add imports at the top of the file (torch, cv2, ultralytics, etc.) only as needed
   - If the POC uses a pattern that doesn't fit the clean interface, adapt it — don't just copy it verbatim

4. **Run the tests** — `cd packages/ingestion && uv run pytest -m "not integration"`. All 7 existing tests must still pass. The pipeline module itself won't have tests at this point (those require a GPU and real video).

5. **Lint and typecheck** — `cd packages/ingestion && uv run ruff check src/ && uv run ty check --config-file ../../ty.toml src/`. Fix any issues before reporting done.

## What not to do

- Don't change method signatures — the orchestrator depends on them
- Don't add new public methods beyond what the stub defines
- Don't import ultralytics/torch/opencv at module level if you can import them inside the method or `__init__` — the `[cv]` optional group means these may not be installed
- Don't add logging inside pipeline methods — that belongs in the orchestrator
