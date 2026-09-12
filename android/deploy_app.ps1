$adb = "C:\Users\tomal\AppData\Local\Android\Sdk\platform-tools\adb.exe"
$apk = "c:\gs-project\android\apk\AGI-PM-V20260910.02-release.apk"
& $adb uninstall com.agipm.app 2>$null
$out = & $adb install -r $apk 2>&1 | Out-String
Write-Host ("INSTALL_RESULT:" + $out.Trim())
& $adb shell am start -n com.agipm.app/.MainActivity 2>$null
Write-Host "LAUNCHED"
