@echo off
chcp 65001 >nul
title Choice Viet Nam APK Builder
cd /d "%~dp0"
python build_apk.py
pause
