$dirs = @(
  'C:\Users\tomal\AppData\Local\Android\Sdk\.sdk',
  'C:\Users\tomal\AppData\Local\Android\Sdk\.downloadIntermediates',
  'C:\Users\tomal\AppData\Local\Android\Sdk\.temp',
  'C:\Users\tomal\.android'
)
foreach ($d in $dirs) {
  Add-Content C:\gs-project\android\probe.log "=== $d ==="
  if (Test-Path $d) {
    Get-ChildItem $d -Recurse -ErrorAction SilentlyContinue |
      Where-Object { $_.Length -gt 100KB } |
      Sort-Object LastWriteTime -Descending |
      Select-Object -First 8 FullName,@{n='MB';e={[math]::Round($_.Length/1MB)}},LastWriteTime |
      Format-Table -AutoSize | Out-String | Add-Content -Path C:\gs-project\android\probe.log
  } else { Add-Content C:\gs-project\android\probe.log "(not exist)" }
}
Add-Content C:\gs-project\android\probe.log "`n=== phase3 tail ==="
Get-Content C:\gs-project\android\emu_phase3.log -Tail 4 | Add-Content -Path C:\gs-project\android\probe.log
