$out = "C:\gs-project\android\sysimg.xml"
& curl.exe -L -o $out "https://dl.google.com/android/repository/sys-img/android/sys-img2-3.xml"
Write-Host "xml size=$(Get-Item $out).Length"
Select-String -Path $out -Pattern "google_apis/x86_64-35" | ForEach-Object { $_.Line.Trim() } | Out-File -Encoding utf8 C:\gs-project\android\url.log
Write-Host "--- matched lines ---"
Get-Content C:\gs-project\android\url.log
