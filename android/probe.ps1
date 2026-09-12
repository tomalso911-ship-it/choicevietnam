Get-ChildItem 'C:\Users\tomal\AppData\Local\Temp' -ErrorAction SilentlyContinue |
  Where-Object { $_.Length -gt 1MB } |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 10 Name,@{n='MB';e={[math]::Round($_.Length/1MB)}},LastWriteTime |
  Format-Table -AutoSize | Out-File -Encoding utf8 C:\gs-project\android\probe.log
Add-Content C:\gs-project\android\probe.log "`n--- SDK top ---"
Get-ChildItem 'C:\Users\tomal\AppData\Local\Android\Sdk' -ErrorAction SilentlyContinue |
  Format-Table -AutoSize | Out-String | Add-Content -Path C:\gs-project\android\probe.log
Add-Content C:\gs-project\android\probe.log "`n--- phase3 tail ---"
Get-Content C:\gs-project\android\emu_phase3.log -Tail 4 | Add-Content -Path C:\gs-project\android\probe.log
