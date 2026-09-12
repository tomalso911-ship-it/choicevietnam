$ErrorActionPreference = 'Continue'
$sdk = "C:\Users\tomal\AppData\Local\Android\Sdk"
$log = "C:\gs-project\android\phase4.log"
$img = "$sdk\system-images\android-35\default\x86_64\system.img"
$apk = "C:\gs-project\android\apk\AGI-PM-V20260909.01-release.apk"
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$env:ANDROID_HOME = $sdk
$env:ANDROID_SDK_ROOT = $sdk
function Log($m){ "[$(Get-Date -Format 'HH:mm:ss')] $m" | Out-File -Append -Encoding utf8 $log }

Log "=== PHASE4 waiting for system.img ==="
$wait = 0
while (-not (Test-Path $img)) {
  Start-Sleep -Seconds 15; $wait += 15
  if ($wait -gt 1200) { Log "TIMEOUT waiting for image"; exit 1 }
}
Log "system.img ready after ${wait}s"

Log "creating AVD test35 ..."
& "$sdk\cmdline-tools\latest\bin\avdmanager.bat" create avd -n test35 -k "system-images;android-35;default;x86_64" -d "pixel_6" 2>&1 | Out-File -Append -Encoding utf8 $log
Log "avd create exit=$LASTEXITCODE"

Log "launching emulator (windowed) ..."
Start-Process -FilePath "$sdk\emulator\emulator.exe" -ArgumentList "-avd","test35","-netdelay","none","-netspeed","full" -WindowStyle Normal
Log "emulator launched"

Log "waiting for device (adb wait-for-device) ..."
& "$sdk\platform-tools\adb.exe" wait-for-device 2>&1 | Out-File -Append -Encoding utf8 $log
Log "device online"

$boot = ""
for ($i = 0; $i -lt 48; $i++) {
  $boot = & "$sdk\platform-tools\adb.exe" shell getprop sys.boot_completed 2>$null
  if ($boot -eq "1") { break }
  Start-Sleep -Seconds 5
}
Log "boot_completed=$boot"

Log "installing APK: $apk"
& "$sdk\platform-tools\adb.exe" install -r $apk 2>&1 | Out-File -Append -Encoding utf8 $log
Log "install exit=$LASTEXITCODE"

Log "starting app ..."
& "$sdk\platform-tools\adb.exe" shell am start -n com.agipm.app/.MainActivity 2>&1 | Out-File -Append -Encoding utf8 $log
Log "=== PHASE4 DONE ==="
