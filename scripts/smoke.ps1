$ErrorActionPreference = 'Stop'
$base = 'http://localhost:8080'
$results = @()

function Show($name, $ok, $info) {
  $script:results += [pscustomobject]@{ Test = $name; Result = $(if ($ok) { 'PASS' } else { 'FAIL' }); Detail = $info }
}

function New-Sess { New-Object Microsoft.PowerShell.Commands.WebRequestSession }

function Get-Csrf($sess) {
  $c = $sess.Cookies.GetCookies([uri]$base) | Where-Object { $_.Name -eq 'garage_csrf' }
  if ($c) { return [uri]::UnescapeDataString($c.Value) }
  return ''
}

function Api($method, $path, $body, $sess) {
  $h = @{ Accept = 'application/json' }
  $tok = Get-Csrf $sess
  if ($tok) { $h['X-CSRF-Token'] = $tok }
  $p = @{ Uri = "$base$path"; Method = $method; Headers = $h; WebSession = $sess; TimeoutSec = 15 }
  if ($body) {
    $h['Content-Type'] = 'application/json'
    $p.Body = ($body | ConvertTo-Json -Depth 6)
  }
  try {
    $r = Invoke-WebRequest @p -UseBasicParsing
    return @{ code = $r.StatusCode; json = $(if ($r.Content) { $r.Content | ConvertFrom-Json } else { $null }); err = $null }
  } catch {
    $resp = $_.Exception.Response
    $code = if ($resp) { [int]$resp.StatusCode } else { 0 }
    $txt = ''
    try {
      if ($resp) { $txt = (New-Object System.IO.StreamReader($resp.GetResponseStream())).ReadToEnd() }
    } catch {}
    return @{ code = $code; json = $(if ($txt) { try { $txt | ConvertFrom-Json } catch { $null } } else { $null }); err = $txt }
  }
}

# 1. session anonymous
$s1 = New-Sess
$r = Api GET '/api/auth/session' $null $s1
Show 'session anonymous 200 user=null' ($r.code -eq 200 -and -not $r.json.user) "code=$($r.code)"

# 2. login quan_ly
$r = Api POST '/api/auth/login' @{ username = 'quan_ly'; password = 'Garage@2026' } $s1
$loginOk = $r.code -eq 200 -and $r.json.user
Show 'login quan_ly' ([bool]$loginOk) "code=$($r.code) user=$($r.json.user.username) role=$($r.json.user.role)"

if ($loginOk) {
  # 3. main endpoints
  foreach ($p in @('/api/meta', '/api/lookups', '/api/dashboard', '/api/orders?moi_trang=5', '/api/invoices', '/api/stock', '/api/stock/warnings', '/api/ai/recent', '/api/users')) {
    $x = Api GET $p $null $s1
    Show "GET $p" ($x.code -eq 200) "code=$($x.code)"
  }
  $x = Api GET '/api/orders/1' $null $s1
  Show 'GET /api/orders/1' ($x.code -eq 200 -and $x.json.phieu) "code=$($x.code) status=$($x.json.phieu.status)"
  $x = Api GET '/api/invoices/7' $null $s1
  Show 'GET /api/invoices/7' ($x.code -eq 200 -and $x.json.hoa_don) "code=$($x.code) status=$($x.json.hoa_don.status) con=$($x.json.hoa_don.con_phai_thu)"

  # 4. CSRF protection: POST without header -> 403
  $sessNoCsrf = New-Sess
  $null = Api GET '/api/auth/session' $null $sessNoCsrf
  try {
    $p = @{ Uri = "$base/api/orders/1/logs"; Method = 'POST'; ContentType = 'application/json'; Body = '{"note":"khong co csrf"}'; WebSession = $sessNoCsrf; TimeoutSec = 10 }
    Invoke-WebRequest @p -UseBasicParsing | Out-Null
    Show 'POST khong CSRF bi tu choi' $false 'got 200 (unexpected)'
  } catch {
    $c = [int]$_.Exception.Response.StatusCode
    Show 'POST khong CSRF bi tu choi' ($c -eq 403) "code=$c"
  }

  # 5. mutation with CSRF: add log to order 1
  $x = Api POST '/api/orders/1/logs' @{ note = 'Smoke test: ghi nhat ky qua API' } $s1
  Show 'POST nhat ky (co CSRF)' ($x.code -in 200, 201) "code=$($x.code) msg=$($x.json.thong_bao)"

  # 6. invalid transition COMPLETED -> INSPECTING must be 409
  $x = Api POST '/api/orders/1/status' @{ status = 'INSPECTING' } $s1
  Show 'invalid transition blocked (409)' ($x.code -eq 409) "code=$($x.code) msg=$($x.json.thong_diep)"
}

# 7. thu_ngan (cashier)
$s2 = New-Sess
$null = Api GET '/api/auth/session' $null $s2
$r = Api POST '/api/auth/login' @{ username = 'thu_ngan'; password = 'Garage@2026' } $s2
$ok2 = $r.code -eq 200 -and $r.json.user
Show 'login thu_ngan' ([bool]$ok2) "code=$($r.code)"
if ($ok2) {
  $x = Api GET '/api/stock' $null $s2
  Show 'thu_ngan stock GET 200 (order.view)' ($x.code -eq 200) "code=$($x.code)"
  $x = Api POST '/api/stock/receipt' @{ part_id = 1; qty = 1; note = 'smoke' } $s2
  Show 'thu_ngan nhap kho 403 (stock.manage)' ($x.code -eq 403) "code=$($x.code)"
  $x = Api GET '/api/invoices' $null $s2
  Show 'thu_ngan invoices 403' ($x.code -eq 403) "code=$($x.code)"
  $x = Api POST '/api/invoices/7/payments' @{ amount = 100000; method = 'CASH' } $s2
  Show 'thu_ngan ghi thu tien (200/201)' ($x.code -in 200, 201) "code=$($x.code) msg=$($x.json.thong_diep)"
}

# 8. ky_thuat_vien (technician)
$s3 = New-Sess
$null = Api GET '/api/auth/session' $null $s3
$r = Api POST '/api/auth/login' @{ username = 'ky_thuat_vien'; password = 'Garage@2026' } $s3
$ok3 = $r.code -eq 200 -and $r.json.user
Show 'login ky_thuat_vien' ([bool]$ok3) "code=$($r.code)"
if ($ok3) {
  $x = Api GET '/api/ai/results' $null $s3
  Show 'ky_thuat_vien ai/results 403' ($x.code -eq 403) "code=$($x.code)"
  $x = Api GET '/api/users' $null $s3
  Show 'ky_thuat_vien users 403' ($x.code -eq 403) "code=$($x.code)"
}

$results | Format-Table -AutoSize
$pass = @($results | Where-Object { $_.Result -eq 'PASS' }).Count
$fail = @($results | Where-Object { $_.Result -eq 'FAIL' }).Count
Write-Output "TOTAL: $pass PASS / $fail FAIL"
