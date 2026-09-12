Select-String -Path C:\gs-project\android\sysimg.xml -Pattern "system-images;android-35;google_apis;x86_64" -Context 0,10 | ForEach-Object {
  $_.Line
  $_.Context.PostContext
} | Out-File C:\gs-project\android\g4.log
"===== also default android-35 x86_64 =====" | Add-Content C:\gs-project\android\g4.log
Select-String -Path C:\gs-project\android\sysimg.xml -Pattern "system-images;android-35;default;x86_64" -Context 0,10 | ForEach-Object {
  $_.Line
  $_.Context.PostContext
} | Add-Content C:\gs-project\android\g4.log
Get-Content C:\gs-project\android\g4.log | Write-Output
