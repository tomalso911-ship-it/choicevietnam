Get-ChildItem C:\gs-project -Recurse -Filter *.apk -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 12 FullName,@{n='MB';e={[math]::Round($_.Length/1MB)}},LastWriteTime |
  Format-Table -AutoSize | Out-File -Encoding utf8 C:\gs-project\android\apk.log
Get-Content C:\gs-project\android\apk.log | Write-Output
