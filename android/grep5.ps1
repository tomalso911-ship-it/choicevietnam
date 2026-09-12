Select-String -Path C:\gs-project\android\sysimg.xml -Pattern "<url>.*\.zip" | Select-Object -First 25 | ForEach-Object { $_.Line.Trim() } | Out-File C:\gs-project\android\urls.log
Get-Content C:\gs-project\android\urls.log | Write-Output
