# E2E nghiệp vụ GarageToolsAI - chạy trên backend THẬT (van hanh).
# Quy trinh: tiep nhan -> bao gia (apply x2) -> sua chua -> nghiem thu (x2)
#            -> hoa don -> thu tien (x2 + huy) -> bao hanh -> kiem tra so.
#
#   Chay backend truoc:  uvicorn app.main:app --port 8000
#   Chay:                .\scripts\e2e.ps1  [-Base http://127.0.0.1:8000]
param(
  [string]$Base = 'http://127.0.0.1:8000'
)
$ErrorActionPreference = 'Stop'
$results = @()

function Show($name, $ok, $info) {
  $script:results += [pscustomobject]@{ Test = $name; Result = $(if ($ok) { 'PASS' } else { 'FAIL' }); Detail = $info }
  Write-Host ("  {0} {1} {2}" -f $(if ($ok) { '[OK]  ' } else { '[FAIL]' }), $name, $info)
}

function New-Sess { New-Object Microsoft.PowerShell.Commands.WebRequestSession }

function Get-Csrf($sess) {
  $c = $sess.Cookies.GetCookies([uri]$Base) | Where-Object { $_.Name -eq 'garage_csrf' }
  if ($c) { return [uri]::UnescapeDataString($c.Value) }
  return ''
}

function Api($method, $path, $body, $sess) {
  $h = @{ Accept = 'application/json' }
  $tok = Get-Csrf $sess
  if ($tok) { $h['X-CSRF-Token'] = $tok }
  $p = @{ Uri = "$Base$path"; Method = $method; Headers = $h; WebSession = $sess; TimeoutSec = 20 }
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
    try { if ($resp) { $txt = (New-Object System.IO.StreamReader($resp.GetResponseStream())).ReadToEnd() } } catch {}
    return @{ code = $code; json = $(if ($txt) { try { $txt | ConvertFrom-Json } catch { $null } } else { $null }); err = $txt }
  }
}

function Ok($r) { return $r.code -in 200, 201 }

Write-Host "=== E2E GarageToolsAI - $Base ==="

# --- Dang nhap quan ly ---
$s = New-Sess
$null = Api GET '/api/auth/session' $null $s
$login = Api POST '/api/auth/login' @{ username = 'quan_ly'; password = 'Garage@2026' } $s
Show 'dang nhap quan_ly' ((Ok $login) -and $login.json.user) "code=$($login.code)"
if (-not ((Ok $login) -and $login.json.user)) {
  $results | Format-Table -AutoSize
  exit 1
}

# --- 1. Tiep nhan: khach + xe + phieu + bien ban ---
$sdt = '0900' + (Get-Date -Format 'HHmmss')
$kh = Api POST '/api/customers' @{ name = 'Khach E2E'; phone = $sdt } $s
Show 'them khach hang' (Ok $kh) "code=$($kh.code) id=$($kh.json.id)"
$cid = $kh.json.id

$plate = '30A-' + (Get-Date -Format 'HHmmss')
$xe = Api POST '/api/vehicles' @{ plate = $plate; brand = 'Toyota'; model = 'Corolla'; year = 2020; customer_id = $cid } $s
Show 'them phuong tien' (Ok $xe) "code=$($xe.code) id=$($xe.json.id) bien=$plate"
$vid = $xe.json.id

$ph = Api POST '/api/orders' @{ vehicle_id = $vid; technical_notes = 'E2E: khieu noi' } $s
Show 'tao phieu sua chua' (Ok $ph) "code=$($ph.code) id=$($ph.json.id)"
$oid = $ph.json.id

$ib = Api POST "/api/orders/$oid/intake" @{ odometer_at_intake = 12345; fuel_level = 'HALF'; notes = 'E2E bien ban tiep nhan' } $s
Show 'nhap bien ban tiep nhan' (Ok $ib) "code=$($ib.code)"

# --- 2. Bao gia: tao, them dang, gui, duyet, ap dung x2 ---
$bg = Api POST '/api/quotations' @{ repair_order_id = $oid; note = 'E2E bao gia' } $s
Show 'tao bao gia' (Ok $bg) "code=$($bg.code) id=$($bg.json.id)"
$qid = $bg.json.id

$d1 = Api POST "/api/quotations/$qid/items" @{ loai = 'dich_vu'; ma = 1; qty = 1 } $s
Show 'them dich vu vao bao gia' (Ok $d1) "code=$($d1.code)"
$d2 = Api POST "/api/quotations/$qid/items" @{ loai = 'phu_tung'; ma = 1; qty = 2 } $s
Show 'them phu tung vao bao gia' (Ok $d2) "code=$($d2.code)"

$parts0 = Api GET '/api/parts?moi_trang=100' $null $s
$stock0 = 0
if ($parts0.code -eq 200) { $stock0 = [int](@($parts0.json.dong | Where-Object { $_.id -eq 1 })[0].stock) }

$send = Api POST "/api/quotations/$qid/send" @{} $s
Show 'gui bao gia (SENT)' ((Ok $send) -and ($send.json.bao_gia.status -eq 'SENT')) "code=$($send.code) status=$($send.json.bao_gia.status)"
$rev = Api POST "/api/quotations/$qid/review" @{ quyet_dinh = 'APPROVED' } $s
Show 'duyet bao gia (APPROVED)' ((Ok $rev) -and ($rev.json.bao_gia.status -eq 'APPROVED')) "code=$($rev.code) status=$($rev.json.bao_gia.status)"

$ap1 = Api POST "/api/quotations/$qid/apply" @{} $s
Show 'ap dung lan 1 (tru kho)' (Ok $ap1) "code=$($ap1.code) msg=$($ap1.json.thong_bao)"
$ap2 = Api POST "/api/quotations/$qid/apply" @{} $s
Show 'ap dung lan 2 bi chan (409)' ($ap2.code -eq 409) "code=$($ap2.code) msg=$($ap2.json.thong_diep)"

$parts1 = Api GET '/api/parts?moi_trang=100' $null $s
$stock1 = -1
if ($parts1.code -eq 200) { $stock1 = [int](@($parts1.json.dong | Where-Object { $_.id -eq 1 })[0].stock) }
Show 'kho phu tung giam 2 sau ap dung' ($stock1 -eq ($stock0 - 2)) "truoc=$stock0 sau=$stock1"

# --- 3. Sua chua -> COMPLETED -> nghiem thu x2 ---
foreach ($tt in @('INSPECTING', 'ESTIMATING', 'REPAIRING', 'COMPLETED')) {
  $st = Api POST "/api/orders/$oid/status" @{ status = $tt } $s
  if (-not (Ok $st)) { Show "chuyen trang thai $tt" $false "code=$($st.code) msg=$($st.json.thong_diep)"; break }
}
$pdetail = Api GET "/api/orders/$oid" $null $s
Show 'phieu da COMPLETED' ($pdetail.json.phieu.status -eq 'COMPLETED') "status=$($pdetail.json.phieu.status)"

$n1 = Api POST "/api/orders/$oid/accept" @{ acceptance_note = 'E2E: khach ky nhan' } $s
Show 'nghiem thu lan 1' (Ok $n1) "code=$($n1.code)"
$n2 = Api POST "/api/orders/$oid/accept" @{ acceptance_note = 'E2E: chay lai' } $s
Show 'nghiem thu lan 2 bi chan (409)' ($n2.code -eq 409) "code=$($n2.code)"

# --- 4. Hoa don + thu tien ---
$hd = Api POST '/api/invoices' @{ repair_order_id = $oid } $s
Show 'lap hoa don' (Ok $hd) "code=$($hd.code) id=$($hd.json.id)"
$hdid = $hd.json.id
$total = [int]$hd.json.hoa_don.total
Show 'tong hoa don > 0' ($total -gt 0) "total=$total"

$t1 = Api POST "/api/invoices/$hdid/payments" @{ amount = [int]($total / 2); method = 'CASH' } $s
Show 'thu 50% (PARTIAL)' ((Ok $t1) -and ($t1.json.hoa_don.status -eq 'PARTIAL')) "code=$($t1.code) status=$($t1.json.hoa_don.status)"

$khoan = $null
$ct = Api GET "/api/invoices/$hdid" $null $s
if ($ct.code -eq 200) { $khoan = @($ct.json.khoan_thu)[0] }
Show 'co khoan thu trong chi tiet' ([bool]$khoan) "khoan_id=$($khoan.id)"

$t2 = Api POST "/api/invoices/$hdid/payments" @{ amount = $total; method = 'CASH' } $s
Show 'thu vuot qua no bi chan (409)' ($t2.code -eq 409) "code=$($t2.code) msg=$($t2.json.thong_diep)"

$tt2 = Api POST "/api/invoices/$hdid/payments" @{ amount = [int]($total / 2); method = 'CASH' } $s
Show 'thu no du (PAID)' ((Ok $tt2) -and ($tt2.json.hoa_don.status -eq 'PAID')) "code=$($tt2.code) status=$($tt2.json.hoa_don.status)"

if ($khoan) {
  $huy = Api POST "/api/invoices/$hdid/payments/$($khoan.id)/cancel" @{} $s
  Show 'huy khoan thu dau' ((Ok $huy) -and ($huy.json.hoa_don.status -eq 'PARTIAL')) "code=$($huy.code) status=$($huy.json.hoa_don.status)"
}

# --- 5. Bao hanh ---
$el = Api GET "/api/warranties/eligible?repair_order_id=$oid" $null $s
$muc = $null
if ($el.code -eq 200) { $muc = @($el.json.dong | Where-Object { $_.service_id })[0] }
Show 'hang muc co the bao hanh' ([bool]$muc) "service_id=$($muc.service_id)"
if ($muc) {
  $ngay = Get-Date -Format 'yyyy-MM-dd'
  $bh = Api POST '/api/warranties' @{ repair_order_id = $oid; months = 6; service_id = [int]$muc.service_id; start_date = $ngay; note = 'E2E bao hanh' } $s
  Show 'tao bao hanh' (Ok $bh) "code=$($bh.code) id=$($bh.json.id)"
  $bh2 = Api POST '/api/warranties' @{ repair_order_id = $oid; months = 6; service_id = [int]$muc.service_id; start_date = $ngay } $s
  Show 'bao hanh lap bi chan (409/400)' ($bh2.code -in 400, 409) "code=$($bh2.code)"
}

# --- 6. Kiem tra toan ven so sach + bao cao ---
$audit = Api GET '/api/stock/audit' $null $s
Show 'so sach kho khong lech' ((Ok $audit) -and (@($audit.json.lech).Count -eq 0)) "lech=$(@($audit.json.lech).Count)"

$bc = Api GET '/api/reports/doanh-thu' $null $s
Show 'bao cao doanh thu (200)' (Ok $bc) "code=$($bc.code)"
$ls = Api GET '/api/history?moi_trang=5' $null $s
Show 'lich su phieu (200)' (Ok $ls) "code=$($ls.code)"
$db = Api GET '/api/dashboard' $null $s
Show 'dashboard (200)' (Ok $db) "code=$($db.code)"

# --- 7. Dang xuat ---
$lo = Api POST '/api/auth/logout' @{} $s
Show 'dang xuat' (Ok $lo) "code=$($lo.code)"
$se = Api GET '/api/auth/session' $null $s
Show 'phien da dong sau dang xuat' ((Ok $se) -and (-not $se.json.user)) "user=$($se.json.user)"

Write-Host ''
$results | Format-Table -AutoSize
$pass = @($results | Where-Object { $_.Result -eq 'PASS' }).Count
$fail = @($results | Where-Object { $_.Result -eq 'FAIL' }).Count
Write-Output "TOTAL: $pass PASS / $fail FAIL"
if ($fail -gt 0) { exit 1 } else { exit 0 }
