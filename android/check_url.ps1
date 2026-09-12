$curl = "$env:SystemRoot\System32\curl.exe"
$urls = @(
 "https://dl.google.com/android/repository/sys-img/android/x86_64-35_r02.zip",
 "https://dl.google.com/android/repository/x86_64-35_r02.zip",
 "https://dl.google.com/android/repository/sys-img/x86_64-35_r02.zip"
)
foreach ($u in $urls) {
  $code = & $curl -s -r 0-1024 -o $null -w "%{http_code}" --max-time 20 $u
  "$u -> HTTP $code" | Write-Output
}
