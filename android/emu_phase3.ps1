$ErrorActionPreference = 'Continue'
$sdk = "C:\Users\tomal\AppData\Local\Android\Sdk"
$log = "C:\gs-project\android\emu_phase3.log"
$stamp = { "[$(Get-Date -Format 'HH:mm:ss')]" }
function Log($m){ "$($stamp.Invoke()) $m" | Out-File -Append -Encoding utf8 $log }
Log "=== PHASE3 START ==="
$android = "$sdk\cmdline-tools\latest\bin\android.exe"
$avd = "$sdk\cmdline-tools\latest\bin\avdmanager.bat"

$pkg = "system-images;android-35;google_apis;x86_64"
Log "installing system image via android CLI: $pkg"
$inst = "$env:TEMP\inst3.bat"
"@echo off`n(for /l %%i in (1,1,30) do @echo y) | `"$android`" sdk install `"$pkg`"" | Out-File -Encoding ascii $inst
& cmd /c "call $inst" 2>&1 | Out-File -Append -Encoding utf8 $log
Log "system image install done (exit ${LASTEXITCODE})"

Log "image present: $(Test-Path "$sdk\system-images\android-35\google_apis\x86_64\system.img")"

Log "creating AVD test35 ..."
& cmd /c "`"$avd`" create avd -n test35 -k `"$pkg`" -d `"pixel_6`"" 2>&1 | Out-File -Append -Encoding utf8 $log
Log "AVD create done (exit ${LASTEXITCODE})"

Log "=== PHASE3 DONE ==="
