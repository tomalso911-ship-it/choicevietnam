$log = "C:\gs-project\android\url.log"
"" | Set-Content $log
Select-String -Path C:\gs-project\android\sysimg.xml -Pattern "x86_64-35" | ForEach-Object { $_.Line.Trim() } | Add-Content $log
Add-Content $log "===== any google_apis x86_64 ====="
Select-String -Path C:\gs-project\android\sysimg.xml -Pattern "google_apis/x86_64" | ForEach-Object { $_.Line.Trim() } | Add-Content $log
Add-Content $log "===== count x86_64- ====="
(Select-String -Path C:\gs-project\android\sysimg.xml -Pattern "x86_64-").Count | Add-Content $log
Get-Content $log
