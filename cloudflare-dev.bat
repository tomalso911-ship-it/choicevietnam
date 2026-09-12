@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title AGI-PM Cloudflare Dev

REM Set Node.js path
set "NODE_HOME=C:\Users\tomal\.workbuddy\binaries\node\versions\22.22.2"

REM Fallback to official Node install path
if not exist "%NODE_HOME%\node.exe" (
    if exist "C:\Program Files\nodejs\node.exe" (
        set "NODE_HOME=C:\Program Files\nodejs"
    )
)

set "PATH=%NODE_HOME%;%PATH%"

REM Enter cloudflare subdirectory where wrangler.toml lives
cd /d "%~dp0\cloudflare"

REM Load local API token if .env exists
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "key=%%a"
        set "val=%%b"
        REM skip comment lines starting with #
        if not "!key:~0,1!"=="#" (
            set "!key!=!val!"
        )
    )
)

echo ============================================
echo   AGI-PM Cloudflare Dev Environment
echo ============================================
echo.
echo   Current dir: %CD%
echo.
echo   Node:
node -v
echo   npm:
call npm -v
echo   Wrangler:
call wrangler -v 2>nul || echo   (not installed yet, see README)
echo.
echo --------------------------------------------
echo   Common commands:
echo     wrangler login     login Cloudflare
echo     wrangler dev       local preview
echo     wrangler deploy    deploy to Cloudflare
echo     wrangler tail      live logs
echo --------------------------------------------
echo.
cmd /k
