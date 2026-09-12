# ============================================================
# AGI-PM - one-command deploy (WEB + CLOUD only)
# Desktop EXE has been dropped, so this script no longer builds it.
#
#   powershell -ExecutionPolicy Bypass -File .\run_all.ps1
#
# Steps:
#   1/2  deploy Cloudflare Worker  (removes the users-sync hazard)
#   2/2  deploy web (Cloudflare Pages)
#
# Mobile APK is built separately:
#   cd android ; .\gradlew.bat assembleRelease   (needs JDK + SDK)
# ============================================================

$root = 'C:\gs-project'
Set-Location $root
$env:PYTHONIOENCODING = 'utf-8'

function Banner($msg) {
    Write-Host ''
    Write-Host ('=' * 62) -ForegroundColor DarkGray
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host ('=' * 62) -ForegroundColor DarkGray
}

# ---------------- Step 1: deploy Worker ----------------
Banner 'STEP 1/2   deploy Cloudflare Worker (removes the users-sync hazard)'
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'deploy_cloud.ps1')
$deployOk = ($LASTEXITCODE -eq 0)

if ($deployOk) {
    Write-Host ''
    Write-Host '  [OK] Worker deployed - users table is now excluded from sync.' -ForegroundColor Green
} else {
    Write-Host ''
    Write-Host '  ==========================================================' -ForegroundColor Red
    Write-Host '  [WARN] Worker deploy FAILED.' -ForegroundColor Red
    Write-Host '         DO NOT click "sync" in the app until this succeeds,' -ForegroundColor Red
    Write-Host '         otherwise the cloud password may be overwritten.' -ForegroundColor Red
    Write-Host '         Retry later with:' -ForegroundColor Yellow
    Write-Host '         powershell -ExecutionPolicy Bypass -File .\deploy_cloud.ps1' -ForegroundColor Yellow
    Write-Host '  ==========================================================' -ForegroundColor Red
}

# ---------------- Step 2: deploy web (Pages) ----------------
Banner 'STEP 2/2   deploy web (Cloudflare Pages)'
& python (Join-Path $root 'cloudflare\build_pages.py')
$webOk = ($LASTEXITCODE -eq 0)

# ---------------- Summary ----------------
Banner 'SUMMARY'
if ($deployOk) {
    Write-Host '  Cloud Worker : DEPLOYED  (users excluded - sync is safe now)' -ForegroundColor Green
} else {
    Write-Host '  Cloud Worker : NOT DEPLOYED - sync is still UNSAFE, fix this first' -ForegroundColor Red
}
if ($webOk) {
    Write-Host '  Web (Pages)  : DEPLOYED' -ForegroundColor Green
} else {
    Write-Host '  Web (Pages)  : DEPLOY FAILED - check output above' -ForegroundColor Red
}
Write-Host ''
Write-Host '  Mobile APK is built separately via gradlew assembleRelease (android/).' -ForegroundColor Cyan
Write-Host ''

if (-not $deployOk -or -not $webOk) { exit 1 }
exit 0
