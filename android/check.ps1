$cut=(Get-Date).AddMinutes(-25)
Get-ChildItem $env:TEMP,$env:LOCALAPPDATA -Recurse -ErrorAction SilentlyContinue |
  Where-Object { $_.LastWriteTime -gt $cut -and $_.Length -gt 5MB } |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 20 FullName,@{n='MB';e={[math]::Round($_.Length/1MB)}},LastWriteTime |
  Format-Table -AutoSize | Out-File -Encoding utf8 C:\gs-project\android\chk.log
Add-Content -Path C:\gs-project\android\chk.log -Value "`n=== phase3 log tail ==="
Get-Content C:\gs-project\android\emu_phase3.log -Tail 5 | Out-File -Append -Encoding utf8 C:\gs-project\android\chk.log
Add-Content -Path C:\gs-project\android\chk.log -Value "=== image dir ==="
$p="C:\Users\tomal\AppData\Local\Android\Sdk\system-images\android-35\google_apis\x86_64"
if (Test-Path $p){ Add-Content -Path C:\gs-project\android\chk.log -Value "EXISTS size=$([math]::Round((Get-ChildItem $p -Recurse | Measure-Object -Property Length -Sum).Sum/1MB))MB" } else { Add-Content -Path C:\gs-project\android\chk.log -Value "not yet" }
