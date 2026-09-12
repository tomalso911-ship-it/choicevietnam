$log = "C:\gs-project\android\mon.log"
$tmp = "C:\Users\tomal\AppData\Local\Android\Sdk\.temp\sysimg35.zip"
$img = "C:\Users\tomal\AppData\Local\Android\Sdk\system-images\android-35\default\x86_64\system.img"
for ($i = 0; $i -lt 24; $i++) {
  $t = Get-Date -Format 'HH:mm:ss'
  if (Test-Path $tmp) { $mb = [math]::Round((Get-Item $tmp).Length/1MB) } else { $mb = 0 }
  $done = Test-Path $img
  "$t zip=${mb}MB system.img=$done" | Out-File -Append -Encoding utf8 $log
  if ($done) { "$t EXTRACT COMPLETE" | Out-File -Append -Encoding utf8 $log; break }
  Start-Sleep -Seconds 25
}
