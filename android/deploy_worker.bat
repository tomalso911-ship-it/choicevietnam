@echo off
cd /d c:\choice-project\cloudflare
set CLOUDFLARE_API_TOKEN=%CLOUDFLARE_API_TOKEN%
set PATH=C:\Users\tomal\.workbuddy\binaries\node\versions\22.22.2;%PATH%
call node_modules\.bin\wrangler.cmd deploy
