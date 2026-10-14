# Phuc hoi garage.db tu ban sao luu cua backup.ps1.
# TRUOC khi phuc hoi, dung phien backend dang chay va file hien tai se duoc
# luu thanh *.bak-before-restore (khong mat du lieu).
#
#   .\scripts\restore.ps1 -Source .\backups\garage-20261013-120000.db
param(
  [Parameter(Mandatory = $true)][string]$Source,
  [string]$DbPath = (Join-Path $PSScriptRoot "..\GarageAI_Project\garage.db")
)
$ErrorActionPreference = 'Stop'

$Source = (Resolve-Path -LiteralPath $Source).Path
$DbPath = [System.IO.Path]::GetFullPath($DbPath)

# Kiem tra ban sao truoc khi ghi de.
$check = & python -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); c.execute('PRAGMA integrity_check').fetchone(); c.close(); print('OK')" $Source
if ($LASTEXITCODE -ne 0 -or "$check" -notmatch "OK") {
  throw "Ban sao loi hoac khong doc duoc: $Source"
}

if (Test-Path -LiteralPath $DbPath) {
  $bak = "$DbPath.bak-before-restore"
  Copy-Item -LiteralPath $DbPath -Destination $bak -Force
  Write-Output "Da luu CSDL hien tai thanh: $bak"
}

Copy-Item -LiteralPath $Source -Destination $DbPath -Force
foreach ($side in @("-wal", "-shm")) {
  $f = "$DbPath$side"
  if (Test-Path -LiteralPath $f) { Remove-Item -LiteralPath $f -Force }
}
Write-Output "Da phuc hoi: $DbPath"
Write-Output "Luu y: neu backend dang chay, restart de nhan CSDL moi. Chay migrations bang: python database/migrations/run_missing.py"
