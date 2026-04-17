# Make.ps1 — Windows-friendly alternative to Makefile
# Usage: .\Make.ps1 <target>
param(
    [Parameter(Position=0)]
    [string]$Target = "help"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$MOON_BIN      = "tools\moon.exe"
$MOON_PLATFORM = "x86_64-pc-windows-msvc"
$MOON_URL      = "https://github.com/moonrepo/moon/releases/latest/download/moon_cli-$MOON_PLATFORM.zip"

# ── Setup ─────────────────────────────────────────────────────────────────────

function Invoke-SetupBackend {
    Push-Location packages\backend
    try { uv sync --all-extras }
    finally { Pop-Location }
}

function Invoke-SetupFrontend {
    Invoke-SetupMoon
    & $MOON_BIN run frontend:setup
}

function Invoke-SetupMoon {
    if (Test-Path $MOON_BIN) { return }
    New-Item -ItemType Directory -Force -Path tools | Out-Null
    Write-Host "Downloading moon for $MOON_PLATFORM..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $tmp = Join-Path $env:TEMP "moon_cli.zip"
    if ($PSVersionTable.PSVersion.Major -lt 6) {
        Invoke-WebRequest -Uri $MOON_URL -OutFile $tmp -UseBasicParsing
    }
    else {
        Invoke-WebRequest -Uri $MOON_URL -OutFile $tmp
    }
    $extract = Join-Path $env:TEMP "moon_extract"
    Expand-Archive -Path $tmp -DestinationPath $extract -Force
    Copy-Item -Path (Join-Path $extract "moon.exe") -Destination $MOON_BIN -Force
    Remove-Item $tmp, $extract -Recurse -Force
    Write-Host "moon installed at $MOON_BIN"
}

function Invoke-SetupHooks {
    Push-Location packages\backend
    try { uv run pre-commit install }
    finally { Pop-Location }
}

function Invoke-Setup {
    Invoke-SetupBackend
    Invoke-SetupFrontend
    Invoke-SetupMoon
    Invoke-SetupHooks
}

# ── Development ───────────────────────────────────────────────────────────────

function Invoke-Dev {
    Invoke-SetupMoon
    Write-Host "Starting WELS platform..."
    Write-Host "  Backend  -> http://localhost:8000"
    Write-Host "  Frontend -> http://localhost:3000"
    Write-Host "  Docs     -> http://localhost:8080"
    Write-Host "  Press Ctrl+C to stop all services"

    $moonJob = Start-Process -FilePath $MOON_BIN `
        -ArgumentList "run", "backend:run", "frontend:run" `
        -PassThru -NoNewWindow

    Push-Location packages\backend
    $docsJob = Start-Process -FilePath "uv" `
        -ArgumentList "run", "mkdocs", "serve", "-f", "..\..\mkdocs.yml", "-a", "localhost:8080" `
        -PassThru -NoNewWindow
    Pop-Location

    try {
        Wait-Process -Id $moonJob.Id
    }
    finally {
        Stop-Process -Id $moonJob.Id  -ErrorAction SilentlyContinue
        Stop-Process -Id $docsJob.Id  -ErrorAction SilentlyContinue
    }
}

function Invoke-RunBackend {
    Push-Location packages\backend
    try { uv run uvicorn backend.app:app --reload --port 8000 }
    finally { Pop-Location }
}

function Invoke-RunFrontend {
    Invoke-SetupMoon
    & $MOON_BIN run frontend:run
}

function Invoke-BuildFrontend {
    Invoke-SetupMoon
    & $MOON_BIN run frontend:build
}

# ── Lint ──────────────────────────────────────────────────────────────────────

function Invoke-LintBackend {
    Push-Location packages\backend
    try { uv run ruff check src/ tests/ }
    finally { Pop-Location }
}

function Invoke-LintFrontend {
    Invoke-SetupMoon
    & $MOON_BIN run frontend:lint
}

function Invoke-Lint {
    Invoke-LintBackend
    Invoke-LintFrontend
}

# ── Type check ────────────────────────────────────────────────────────────────

function Invoke-TypecheckBackend {
    Push-Location packages\backend
    try { uv run ty check --config-file ../../ty.toml src/ }
    finally { Pop-Location }
}

function Invoke-TypecheckFrontend {
    Invoke-SetupMoon
    & $MOON_BIN run frontend:typecheck
}

function Invoke-Typecheck {
    Invoke-TypecheckBackend
    Invoke-TypecheckFrontend
}

# ── Format ────────────────────────────────────────────────────────────────────

function Invoke-FormatBackend {
    Push-Location packages\backend
    try { uv run ruff format src/ tests/ }
    finally { Pop-Location }
}

function Invoke-Format {
    Invoke-FormatBackend
}

# ── Tests ─────────────────────────────────────────────────────────────────────

function Invoke-TestBackend {
    Push-Location packages\backend
    try { uv run pytest }
    finally { Pop-Location }
}

function Invoke-Test {
    Invoke-TestBackend
}

function Invoke-TestIntegration {
    Push-Location packages\backend
    try { uv run pytest -m integration }
    finally { Pop-Location }
}

# ── Docs ──────────────────────────────────────────────────────────────────────

function Invoke-Docs {
    Push-Location packages\backend
    try { uv run mkdocs serve -f ../../mkdocs.yml -a localhost:8080 }
    finally { Pop-Location }
}

function Invoke-DocsBuild {
    Push-Location packages\backend
    try { uv run mkdocs build -f ../../mkdocs.yml }
    finally { Pop-Location }
}

# ── Clean ─────────────────────────────────────────────────────────────────────

function Invoke-Clean {
    foreach ($pkg in @("packages\backend")) {
        Write-Host "Cleaning $pkg..."
        Remove-Item -Recurse -Force "$pkg\.venv"  -ErrorAction SilentlyContinue
        Remove-Item -Force         "$pkg\uv.lock" -ErrorAction SilentlyContinue
    }
    foreach ($pkg in @("packages\frontend")) {
        Write-Host "Cleaning $pkg..."
        Remove-Item -Recurse -Force "$pkg\node_modules" -ErrorAction SilentlyContinue
        Remove-Item -Recurse -Force "$pkg\dist"         -ErrorAction SilentlyContinue
    }
}

# ── Help ──────────────────────────────────────────────────────────────────────

function Show-Help {
    Write-Host @"
Usage: .\Make.ps1 <target>

Setup:
  setup               Set up all packages (backend + frontend + moon + hooks)
  setup-backend       Install backend dependencies
  setup-frontend      Install frontend dependencies (pnpm install via moon)
  setup-moon          Download moon binary
  setup-hooks         Install pre-commit hooks

Development:
  dev                 Start all services (backend + frontend + docs)
  run-backend         Start backend only  (http://localhost:8000)
  run-frontend        Start frontend only (http://localhost:3000, Vite)
  build-frontend      Production build of the React frontend

Code Quality:
  lint                Lint all packages
  lint-backend        Lint backend
  lint-frontend       Lint frontend (eslint)
  typecheck           Type-check all packages
  typecheck-backend   Type-check backend (ty)
  typecheck-frontend  Type-check frontend (tsc)
  format              Format backend

Tests:
  test                Run all tests (backend)
  test-backend        Run backend tests
  test-integration    Run backend integration tests

Docs:
  docs                Live-reload docs server (http://localhost:8080)
  docs-build          Build static docs site

Misc:
  clean               Remove .venv, uv.lock, node_modules, dist
  help                Show this help (default)
"@
}

# ── Dispatch ──────────────────────────────────────────────────────────────────

switch ($Target) {
    "setup"              { Invoke-Setup }
    "setup-backend"      { Invoke-SetupBackend }
    "setup-frontend"     { Invoke-SetupFrontend }
    "setup-moon"         { Invoke-SetupMoon }
    "setup-hooks"        { Invoke-SetupHooks }
    "dev"                { Invoke-Dev }
    "run-backend"        { Invoke-RunBackend }
    "run-frontend"       { Invoke-RunFrontend }
    "build-frontend"     { Invoke-BuildFrontend }
    "lint"               { Invoke-Lint }
    "lint-backend"       { Invoke-LintBackend }
    "lint-frontend"      { Invoke-LintFrontend }
    "typecheck"          { Invoke-Typecheck }
    "typecheck-backend"  { Invoke-TypecheckBackend }
    "typecheck-frontend" { Invoke-TypecheckFrontend }
    "format"             { Invoke-Format }
    "format-backend"     { Invoke-FormatBackend }
    "test"               { Invoke-Test }
    "test-backend"       { Invoke-TestBackend }
    "test-integration"   { Invoke-TestIntegration }
    "docs"               { Invoke-Docs }
    "docs-build"         { Invoke-DocsBuild }
    "clean"              { Invoke-Clean }
    "help"               { Show-Help }
    default {
        Write-Error "Unknown target: '$Target'. Run '.\Make.ps1 help' for available targets."
        exit 1
    }
}
