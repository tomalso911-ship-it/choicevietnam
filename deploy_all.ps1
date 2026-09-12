# ============================================================
# AGI-PM one-command: web + cloud unified (desktop EXE dropped)
#
#   powershell -ExecutionPolicy Bypass -File .\deploy_all.ps1
#
# Steps:
#   1/3  regenerate web/PWA icons from android/logo_agi.svg
#   2/3  deploy web (Cloudflare Pages)
#   3/3  deploy Cloudflare Worker
#
# Mobile APK is built separately via _build_apk.ps1 (gradlew).
# ============================================================

$root = 'C:\gs-project'
Set-Location $root
$env:PYTHONIOENCODING = 'utf-8'

function Step($n, $msg) {
    Write-Host ''
    Write-Host ('=' * 60) -ForegroundColor DarkGray
    Write-Host "  $n  $msg" -ForegroundColor Cyan
    Write-Host ('=' * 60) -ForegroundColor DarkGray
}

# ---------- 1) icons ----------
Step '1/3' 'regenerate web/PWA icons from android/logo_agi.svg'
& python make_web_icons.py

# ---------- 2) deploy web ----------
Step '2/3' 'deploy web (Cloudflare Pages)'
& python (Join-Path $root 'cloudflare\build_pages.py')

# ---------- 3) deploy Worker ----------
Step '3/3' 'deploy Cloudflare Worker'
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'deploy_cloud.ps1')

# ---------- summary ----------
Step 'DONE' 'summary'
Write-Host "  web icons : favicon.svg / icon-192 / icon-512 / maskable / apple-touch-icon" -ForegroundColor Green
Write-Host "  web (Pages) + Worker deployed. Mobile APK built via gradlew separately." -ForegroundColor Green
