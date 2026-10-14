# Sao luu nhat quan garage.db bang sqlite backup API (chup duoc khi server
# dang chay, bat kep WAL — khac voi viec copy file thuong).
#
#   .\scripts\backup.ps1                          # luu vao .\backups\
#   .\scripts\backup.ps1 -DbPath .\GarageAI_Project\garage.db -Keep 30
param(
  [string]$DbPath = (Join-Path $PSScriptRoot "..\GarageAI_Project\garage.db"),
  [string]$OutDir = (Join-Path $PSScriptRoot "..\backups"),
  [int]$Keep = 14
)
$ErrorActionPreference = 'Stop'

$DbPath = (Resolve-Path -LiteralPath $DbPath).Path
if (-not (Test-Path -LiteralPath $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
$OutDir = (Resolve-Path -LiteralPath $OutDir).Path

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$dest = Join-Path $OutDir "garage-$stamp.db"

# sqlite3 Connection.backup chup an toan voi WAL va khong chan writer.
$py = @"
import sqlite3, sys
src = sqlite3.connect(sys.argv[1])
dst = sqlite3.connect(sys.argv[2])
with dst:
    src.backup(dst)
dst.close(); src.close()
print('OK')
"@
$out = & python -c $py $DbPath $dest
if ($LASTEXITCODE -ne 0 -or "$out" -notmatch "OK") {
  throw "Sao luu that bai (exit=$LASTEXITCODE): $out"
}

$len = (Get-Item -LiteralPath $dest).Length
Write-Output "Da sao luu: $dest ($len bytes)"

# Giu Keep ban moi nhat, xoa ban cu hon.
$cu = Get-ChildItem -LiteralPath $OutDir -Filter "garage-*.db" |
  Sort-Object Name -Descending | Select-Object -Skip ([Math]::Max(0, $Keep))
foreach ($f in $cu) {
  Remove-Item -LiteralPath $f.FullName
  Write-Output "Da xoa ban cu: $($f.Name)"
}
