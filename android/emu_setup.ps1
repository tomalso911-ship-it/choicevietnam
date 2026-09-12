$ErrorActionPreference = 'Continue'
$sdk = "C:\Users\tomal\AppData\Local\Android\Sdk"
$log = "C:\gs-project\android\emu_setup.log"
$stamp = { "[$(Get-Date -Format 'HH:mm:ss')]" }
function Log($m){ "$($stamp.Invoke()) $m" | Out-File -Append -Encoding utf8 $log }
Log "=== START emu setup ==="

$zip = "$env:TEMP\cmdtools.zip"
if (-not (Test-Path "$sdk\cmdline-tools\latest\bin\sdkmanager.bat")) {
    Log "downloading cmdline-tools ..."
    Invoke-WebRequest -Uri "https://dl.google.com/android/repository/commandlinetools-win-16111833_latest.zip" -OutFile $zip -TimeoutSec 900
    Log "cmdline-tools downloaded: $((Get-Item $zip).Length) bytes"
    New-Item -ItemType Directory -Force -Path "$sdk\cmdline-tools" | Out-Null
    Expand-Archive -Path $zip -DestinationPath "$env:TEMP\cmdtools" -Force
    if (Test-Path "$sdk\cmdline-tools\latest") { Remove-Item "$sdk\cmdline-tools\latest" -Recurse -Force }
    Move-Item "$env:TEMP\cmdtools\cmdline-tools" "$sdk\cmdline-tools\latest" -Force
    Log "cmdline-tools placed"
} else { Log "cmdline-tools already present" }

$sm = "$sdk\cmdline-tools\latest\bin\sdkmanager.bat"
$avd = "$sdk\cmdline-tools\latest\bin\avdmanager.bat"

# accept licenses
Log "accepting licenses ..."
$lic = "$env:TEMP\lic.bat"
"@echo off`n(for /l %%i in (1,1,40) do @echo y) | `"$sm`" --licenses" | Out-File -Encoding ascii $lic
& cmd /c "call $lic" | Out-Null
Log "licenses done (exit ${LASTEXITCODE})"

# install system image
Log "installing system image (big ~1.2GB download) ..."
$inst = "$env:TEMP\inst.bat"
"@echo off`n(for /l %%i in (1,1,40) do @echo y) | `"$sm`" `"system-images;android-35;google_apis;x86_64`"" | Out-File -Encoding ascii $inst
& cmd /c "call $inst" | Out-Null
Log "system image install done (exit ${LASTEXITCODE})"

# create AVD
Log "creating AVD test35 ..."
& cmd /c "`"$avd`" create avd -n test35 -k `"system-images;android-35;google_apis;x86_64`" -d `"pixel_6`"" 2>&1 | Out-File -Append -Encoding utf8 $log
Log "AVD create done (exit ${LASTEXITCODE})"

Log "=== AVD READY ==="
