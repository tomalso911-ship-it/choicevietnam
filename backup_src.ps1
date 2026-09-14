# backup_src.ps1 - choice-project source snapshot (git-free rollback)
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\backup_src.ps1 "one-line description of this change"
# Example:
#   powershell -ExecutionPolicy Bypass -File .\backup_src.ps1 "replace CHOICE logo with new SVG"
#
# Effect: copies key sources into backups\<YYYYMMDD-HHMMSS>_<desc>\,
#         and appends one line to backups\MANIFEST.txt (time | desc | files)
#         so you can roll back "by time" or "by description".

$root = $PSScriptRoot
$bakDir = Join-Path $root 'backups'
if (-not (Test-Path $bakDir)) { New-Item -ItemType Directory -Path $bakDir | Out-Null }

# Description: first arg, or env BAK_DESC, or 'manual'
$desc = $args[0]
if ([string]::IsNullOrWhiteSpace($desc)) { $desc = $env:BAK_DESC }
if ([string]::IsNullOrWhiteSpace($desc)) { $desc = 'manual' }

$ts = (Get-Date).ToString('yyyyMMdd-HHmmss')

# Safe folder slug: keep a-z0-9 A-Z0-9 CJK dash underscore, others -> underscore
$slug = ($desc -replace '[^A-Za-z0-9\u4e00-\u9fff\-_]', '_')
if ($slug.Length -gt 60) { $slug = $slug.Substring(0, 60) }

$target = Join-Path $bakDir ($ts + '_' + $slug)
New-Item -ItemType Directory -Path $target | Out-Null

$files = @('index.html', 'crm_table.js', 'lost_table.js', 'app.py', 'manifest.json')
$copied = @()
foreach ($f in $files) {
    $src = Join-Path $root $f
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination (Join-Path $target $f) -Force
        $copied += $f
    }
}

$manifest = Join-Path $bakDir 'MANIFEST.txt'
$line = ($ts + ' | ' + $desc + ' | ' + ($copied -join ' '))
Add-Content -Path $manifest -Value $line -Encoding UTF8

# Also drop a UTF-8 NOTE.txt inside the snapshot folder (searchable by description)
Set-Content -Path (Join-Path $target 'NOTE.txt') -Value $line -Encoding UTF8

Write-Host ''
Write-Host ('==> Snapshot: ' + $target) -ForegroundColor Green
Write-Host ('==> Files: ' + ($copied -join ', ')) -ForegroundColor Cyan
Write-Host ('==> Logged: ' + $manifest) -ForegroundColor Cyan
Write-Host ''
Write-Host 'Restore: copy backups\<folder>\<file> back to project root.' -ForegroundColor Yellow
