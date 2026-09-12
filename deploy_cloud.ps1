# One-command deploy of the Cloudflare Worker (adds /api/sync endpoints).
#
# Steps: install portable Node if missing -> npm install wrangler -> wrangler deploy
# using CLOUDFLARE_API_TOKEN from ..\.env (non-interactive, no browser login needed).
#
# ASCII-only on purpose: PowerShell 5.1 reads a BOM-less .ps1 as ANSI and a
# UTF-8 BOM breaks line 1 parsing on this machine.
#
# Run:  powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy_cloud.ps1

$ErrorActionPreference = 'Stop'

$root    = 'C:\gs-project'
$cfDir   = Join-Path $root 'cloudflare'
$nodeDir = Join-Path $env:LOCALAPPDATA 'nodejs\node-v22.11.0-win-x64'
$nodeExe = Join-Path $nodeDir 'node.exe'
$npmCmd  = Join-Path $nodeDir 'npm.cmd'

# ---------- 1) portable Node ----------
if (-not (Test-Path $nodeExe)) {
    Write-Host '==> Node not found, installing portable Node 22.11.0 ...' -ForegroundColor Yellow
    & (Join-Path $root '_install_node.ps1')
}
if (-not (Test-Path $nodeExe)) { throw "Node install failed: $nodeExe" }
Write-Host '==> Node: ' -NoNewline
& $nodeExe --version

# ---------- 2) Cloudflare API token ----------
$token = $env:CLOUDFLARE_API_TOKEN
if (-not $token) {
    $envFile = Join-Path $root '.env'
    if (Test-Path $envFile) {
        foreach ($line in Get-Content $envFile) {
            $l = $line.Trim()
            if ($l -like 'CLOUDFLARE_API_TOKEN=*') {
                $token = $l.Substring('CLOUDFLARE_API_TOKEN='.Length).Trim().Trim('"').Trim("'")
                break
            }
        }
    }
}
if (-not $token) { throw 'CLOUDFLARE_API_TOKEN not found (set env var or put it in ..\.env)' }
$env:CLOUDFLARE_API_TOKEN = $token
Write-Host '==> Using Cloudflare API token (length ' + $token.Length + ')'

# ---------- 3) wrangler ----------
Push-Location $cfDir
try {
    if (-not (Test-Path (Join-Path $cfDir 'node_modules\wrangler'))) {
        Write-Host '==> npm install (this may take a few minutes) ...' -ForegroundColor Yellow
        & $npmCmd install --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { throw "npm install failed ($LASTEXITCODE)" }
    } else {
        Write-Host '==> wrangler already installed'
    }

    # ---------- 4) deploy ----------
    Write-Host '==> Deploying Worker (agi-gs) ...' -ForegroundColor Cyan
    & $nodeExe (Join-Path $cfDir 'node_modules\wrangler\bin\wrangler.js') deploy
    $code = $LASTEXITCODE
}
finally {
    Pop-Location
}

if ($code -ne 0) {
    Write-Host "[FAIL] deploy exit code $code" -ForegroundColor Red
    exit $code
}
Write-Host ''
Write-Host '[OK] Worker deployed.' -ForegroundColor Green
Write-Host 'Verify:  https://agi-gs.tomalso911.workers.dev/api/health'
