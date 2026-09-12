$ErrorActionPreference = 'Continue'
$sdk = "C:\Users\tomal\AppData\Local\Android\Sdk"
$log = "C:\gs-project\android\emu_phase2.log"
$stamp = { "[$(Get-Date -Format 'HH:mm:ss')]" }
function Log($m){ "$($stamp.Invoke()) $m" | Out-File -Append -Encoding utf8 $log }
Log "=== PHASE2 START ==="
$sm = "$sdk\cmdline-tools\latest\bin\sdkmanager.bat"
$avd = "$sdk\cmdline-tools\latest\bin\avdmanager.bat"

Log "accepting licenses ..."
$lic = "$env:TEMP\lic2.bat"
"@echo off`n(for /l %%i in (1,1,40) do @echo y) | `"$sm`" --licenses" | Out-File -Encoding ascii $lic
& cmd /c "call $lic" 2>&1 | Out-File -Append -Encoding utf8 $log
Log "licenses done (exit ${LASTEXITCODE})"

Log "installing system image (android-35 google_apis x86_64) ..."
$inst = "$env:TEMP\inst2.bat"
"@echo off`n(for /l %%i in (1,1,40) do @echo y) | `"$sm`" `"system-images;android-35;google_apis;x86_64`"" | Out-File -Encoding ascii $inst
& cmd /c "call $inst" 2>&1 | Out-File -Append -Encoding utf8 $log
Log "system image install done (exit ${LASTEXITCODE})"

Log "creating AVD test35 ..."
& cmd /c "`"$avd`" create avd -n test35 -k `"system-images;android-35;google_apis;x86_64`" -d `"pixel_6`"" 2>&1 | Out-File -Append -Encoding utf8 $log
Log "AVD create done (exit ${LASTEXITCODE})"

Log "image present: $(Test-Path "$sdk\system-images\android-35\google_apis\x86_64\system.img")"
Log "=== PHASE2 DONE ==="
