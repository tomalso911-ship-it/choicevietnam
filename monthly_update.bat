@echo off
REM 每月价格自动更新（Windows 计划任务调用）
REM 由搬迁工具生成：2026-09-05，工作目录 C:\gs-project
cd /d "C:\gs-project"
"C:\Users\tomal\AppData\Local\Python\pythoncore-3.14-64\python.exe" cloudflare\build_price_snapshot.py >> cloudflare\snapshot_cron.log 2>&1
