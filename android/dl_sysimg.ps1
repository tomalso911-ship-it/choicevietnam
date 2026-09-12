$ErrorActionPreference = 'Continue'
$log = "C:\gs-project\android\dl.log"
$tmp = "C:\Users\tomal\AppData\Local\Android\Sdk\.temp\sysimg35.zip"
$url = "https://dl.google.com/android/repository/sys-img/android/x86_64-35_r02.zip"
$curl = "$env:SystemRoot\System32\curl.exe"
function Log($m){ "[$(Get-Date -Format 'HH:mm:ss')] $m" | Out-File -Append -Encoding utf8 $log }
# cleanup old failed artifacts
if (Test-Path "C:\Users\tomal\AppData\Local\Android\Sdk\system-images\android-35\google_apis") { Remove-Item "C:\Users\tomal\AppData\Local\Android\Sdk\system-images\android-35\google_apis" -Recurse -Force }
if (Test-Path $tmp) { Remove-Item $tmp -Force }
Log "=== START download $url ==="
& $curl -L -o $tmp $url
Log "curl done exit=$LASTEXITCODE size=$((Get-Item $tmp).Length)"

$dest = "C:\Users\tomal\AppData\Local\Android\Sdk\.temp\sysimg_extract"
if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Expand-Archive -Path $tmp -DestinationPath $dest -Force
Log "extracted"

$items = Get-ChildItem $dest
if (($items | Where-Object { $_.PSIsContainer }).Count -eq 1 -and $items.Count -eq 1) {
  $src = $items[0].FullName
  Log "inner folder: $($items[0].Name)"
} else { $src = $dest }

$target = "C:\Users\tomal\AppData\Local\Android\Sdk\system-images\android-35\default\x86_64"
New-Item -ItemType Directory -Force -Path $target | Out-Null
Copy-Item "$src\*" $target -Recurse -Force
Log "copied to $target"
Log "system.img exists: $(Test-Path "$target\system.img")"
Log "=== DONE ==="
