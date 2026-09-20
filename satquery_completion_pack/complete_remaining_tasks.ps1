param(
    [Parameter(Mandatory=$false)]
    [string]$Root = (Get-Location).Path,
    [switch]$RunRealProxy,
    [switch]$RunBrowserQA
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path $Root).Path
Set-Location $Root

$Pack = Split-Path -Parent $MyInvocation.MyCommand.Path
$Tools = Join-Path $Pack "tools"
$Py = Join-Path $Root ".venv\Scripts\python.exe"

if (!(Test-Path $Py)) { throw "Python venv not found: $Py" }
if (!(Test-Path ".\evaluation")) { throw "This does not look like the SatQuery project root: $Root" }

New-Item -ItemType Directory -Force -Path ".\docs\evidence" | Out-Null

function Section([string]$t) {
    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host $t -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

Section "1. PROMOTE NEWEST VERIFIED BENCHMARK TO DASHBOARD"
$latest = Get-ChildItem ".\evaluation\results_full_*.json" -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (!$latest) { throw "No evaluation/results_full_*.json found. Run the 72-sample evaluation first." }

$bench = Get-Content $latest.FullName -Raw | ConvertFrom-Json
if (!$bench.datasets) { throw "Latest full result has no datasets object." }
$completed = 0
foreach ($p in $bench.datasets.PSObject.Properties) { $completed += [int]$p.Value.completed }
if ($completed -lt 1) { throw "Latest result contains no completed evaluations." }

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
if (Test-Path ".\evaluation\results.json") {
    Copy-Item ".\evaluation\results.json" ".\evaluation\results_before_promotion_$stamp.json"
}
Copy-Item $latest.FullName ".\evaluation\results.json" -Force
Write-Host "[PASS] Promoted $($latest.Name) -> evaluation/results.json" -ForegroundColor Green
Write-Host "Completed samples: $completed"
Write-Host "Status: $($bench.status)"
Write-Host "Scope:  $($bench.scope)"

Section "2. VERIFY LIVE BENCHMARK API NOW READS PROMOTED RESULT"
try {
    $api = Invoke-RestMethod "http://127.0.0.1:8000/api/benchmarks" -TimeoutSec 30
    Write-Host "[PASS] /api/benchmarks reachable" -ForegroundColor Green
    Write-Host "API evaluation_date: $($api.evaluation_date)"
    Write-Host "File evaluation_date: $($bench.evaluation_date)"
    if ($api.evaluation_date -ne $bench.evaluation_date) {
        Write-Warning "API and promoted file evaluation dates differ. Restart/rebuild gateway and recheck."
    }
} catch {
    Write-Warning "Benchmark API check failed: $($_.Exception.Message)"
}

Section "3. FINAL FOUR-DEMO E2E PROOF"
& $Py (Join-Path $Tools "run_demo_proof.py") --root $Root
if ($LASTEXITCODE -ne 0) { throw "Final demo proof failed." }

Section "4. FRESH GROUNDING PARAPHRASE / CONTRAST PROOF"
& $Py (Join-Path $Tools "grounding_paraphrase_proof.py") --root $Root
if ($LASTEXITCODE -ne 0) { Write-Warning "Grounding proof did not fully pass. Inspect docs/evidence/GROUNDING_PARAPHRASE_PROOF.md" }

Section "5. VQA ERROR ANALYSIS"
& $Py (Join-Path $Tools "vqa_error_analysis.py") --root $Root
if ($LASTEXITCODE -ne 0) { Write-Warning "VQA error analysis could not be generated." }

Section "6. WRITE MISSING JUDGE/EVIDENCE DOCUMENTATION"
& $Py (Join-Path $Tools "write_docs.py") --root $Root
if ($LASTEXITCODE -ne 0) { throw "Documentation generation failed." }

if ($RunRealProxy) {
    Section "7. REAL SENTINEL-1/SENTINEL-2 PROXY VALIDATION"
    & $Py -c "import datasets" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing Hugging Face datasets client for streamed one-sample proxy test..." -ForegroundColor Yellow
        & $Py -m pip install "datasets>=3,<5"
        if ($LASTEXITCODE -ne 0) { throw "Could not install datasets package." }
    }
    & $Py (Join-Path $Tools "real_proxy_sen12mscr.py") --root $Root
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Real proxy run did not complete. Keep REAL_WORLD_PROXY_TEST.md marked PARTIAL and inspect the error."
    }
} else {
    Write-Host "`n[SKIP] Real Sentinel proxy test. Re-run with -RunRealProxy to attempt it." -ForegroundColor Yellow
}

if ($RunBrowserQA) {
    Section "8. BROWSER SMOKE QA"
    Push-Location ".\frontend"
    if (!(Test-Path ".\node_modules\playwright")) {
        Write-Host "Installing Playwright dev dependency..." -ForegroundColor Yellow
        npm install -D playwright
        if ($LASTEXITCODE -ne 0) { Pop-Location; throw "Playwright npm install failed." }
    }
    npx playwright install chromium
    if ($LASTEXITCODE -ne 0) { Pop-Location; throw "Chromium install failed." }
    Pop-Location
    node (Join-Path $Tools "ui_smoke.mjs") $Root
    if ($LASTEXITCODE -ne 0) { Write-Warning "Browser smoke reported failures. Inspect docs/evidence/UI_SMOKE.json" }
} else {
    Write-Host "[SKIP] Browser smoke QA. Re-run with -RunBrowserQA to execute it." -ForegroundColor Yellow
}

Section "9. FINAL AUTOMATED PROJECT CHECKS"
Push-Location ".\frontend"
npx tsc --noEmit
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "TypeScript check failed." }
npm run build
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "Frontend production build failed." }
Pop-Location

& $Py -m pytest tests -q
if ($LASTEXITCODE -ne 0) { throw "Backend tests failed." }

$compose = @("-f","docker-compose.yml","-f","docker-compose.ml.yml")
& docker compose @compose config | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Compose config failed." }
& docker compose @compose ps

$paths = @("/api/health","/api/registry","/api/benchmarks","/api/history","/api/demos")
foreach ($path in $paths) {
    try {
        Invoke-RestMethod ("http://127.0.0.1:8000" + $path) -TimeoutSec 30 | Out-Null
        Write-Host "[PASS] $path" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] $path : $($_.Exception.Message)" -ForegroundColor Red
    }
}

Section "DONE"
Write-Host "Actionable completion tasks finished." -ForegroundColor Green
Write-Host "Evidence directory: $Root\docs\evidence"
Write-Host "External-only boundaries remain: full official benchmark reproduction and genuine Cartosat-2S/RISAT validation." -ForegroundColor Yellow
