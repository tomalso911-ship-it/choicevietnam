$tmp = "C:\Users\tomal\AppData\Local\Android\Sdk\.temp\sysimg35.zip"
if (Test-Path $tmp) { "zip size=$([math]::Round((Get-Item $tmp).Length/1MB)) MB" | Write-Output } else { "zip not yet" | Write-Output }
"--- dl.log ---" | Write-Output
Get-Content C:\gs-project\android\dl.log -Tail 6 | Write-Output
