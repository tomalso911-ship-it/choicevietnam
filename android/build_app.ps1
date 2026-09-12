Set-Location c:\gs-project\android
$out = & .\gradlew.bat assembleRelease 2>&1 | Out-String
$out | Out-File build_log.txt -Encoding utf8
Copy-Item app\build\outputs\apk\release\app-release.apk apk\AGI-PM-V20260910.02-release.apk -Force
if ($out -match 'BUILD SUCCESSFUL') { Write-Host 'BUILD_SUCCESSFUL' } else { Write-Host 'BUILD_FAILED' }
