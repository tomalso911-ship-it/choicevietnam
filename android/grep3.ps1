"===== 1449-byte response =====" | Write-Output
Get-Content "C:\Users\tomal\AppData\Local\Android\Sdk\.temp\sysimg35.zip" | Write-Output
"===== XML context around x86_64-35_r02.zip =====" | Write-Output
Select-String -Path C:\gs-project\android\sysimg.xml -Pattern "x86_64-35_r02.zip" -Context 30,5 | ForEach-Object {
  $_.Context.PreContext | ForEach-Object { $_ }
  ">>> MATCH: $($_.Line)"
  $_.Context.PostContext | ForEach-Object { $_ }
} | Out-File C:\gs-project\android\ctx.log
Get-Content C:\gs-project\android\ctx.log | Write-Output
