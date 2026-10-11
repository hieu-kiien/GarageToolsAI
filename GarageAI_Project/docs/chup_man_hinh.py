# -*- coding: utf-8 -*-
"""Chụp ảnh màn hình thật của ứng dụng đang chạy.

Cách chạy:
    python -m uvicorn app.main:app --port 8010
    python docs/chup_man_hinh.py

Kết quả nằm ở thư mục screenshots/.
"""
import io
import os
import sys
import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, 'screenshots')
CO = 'http://127.0.0.1:8010'
MAT_KHAU = 'Garage@2026'

# (tên tệp, đường dẫn, tài khoản đăng nhập, mô tả)
TRANG = [
    ('01_dang_nhap',      '/accounts/login',        None,        'Trang đăng nhập'),
    ('02_dashboard',      '/dashboard',            'quan_ly',   'Tổng quan garage'),
    ('03_phieu_sua_chua', '/repair-orders',        'quan_ly',   'Danh sách phiếu sửa chữa'),
    ('04_chi_tiet_phieu', '/repair-orders/1',      'quan_ly',   'Chi tiết phiếu sửa chữa'),
    ('05_khach_hang',     '/customers',            'le_tan',    'Danh sách khách hàng'),
    ('06_phuong_tien',    '/vehicles',             'le_tan',    'Danh sách phương tiện'),
    ('07_lich_hen',       '/appointments',         'le_tan',    'Lịch hẹn'),
    ('08_danh_muc',       '/services',             'quan_ly',   'Danh mục dịch vụ'),
    ('09_tai_khoan',      '/users',                'quan_ly',   'Tài khoản nhân viên'),
    ('10_lich_su',        '/history?q=30A-1111',   'le_tan',    'Lịch sử sửa chữa'),
    ('11_bao_cao',        '/reports/doanh-thu',    'quan_ly',   'Báo cáo doanh thu'),
    ('12_ai',             '/ai',                   'quan_ly',   'Màn hình trợ lý AI'),
    ('13_duyet_ai',       '/ai/results',           'quan_ly',   'Duyệt kết quả AI'),
    ('14_cua_hang',       '/shop',                 'quan_ly',   'Cửa hàng dụng cụ (mở rộng)'),
    ('15_khong_co_quyen', '/users',                'ky_thuat_vien', 'Phân quyền: kỹ thuật viên bị chặn'),
]

# Ảnh trên màn hình hẹp để minh chứng tiêu chí CK-04 về giao diện responsive
# (tên tệp, đường dẫn, tài khoản)
HEP = [
    ('16_responsive_dashboard', '/dashboard',     'quan_ly'),
    ('17_responsive_phieu', '/repair-orders/1',  'quan_ly'),
]


def chay():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    ngay = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    dong = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel='chrome', headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)
        for ten, duong_danh, tk, mo_ta in TRANG:
            # Mỗi màn hình dùng một ngữ cảnh trình duyệt riêng để cookie
            # phiên không lẫn sang vai trò khác.
            ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
            page = ctx.new_page()
            if tk:
                page.goto(CO + '/accounts/login', wait_until='domcontentloaded')
                page.fill('input[name=username]', tk)
                page.fill('input[name=password]', MAT_KHAU)
                page.click('button[type=submit]')
                page.wait_for_load_state('networkidle')
            page.goto(CO + duong_danh, wait_until='networkidle')
            page.wait_for_timeout(250)
            tep = os.path.join(OUT, ten + '.png')
            page.screenshot(path=tep, full_page=True)
            dong.append((ten, duong_danh, tk or '-', mo_ta, page.title()))
            print('%-20s %-26s %s' % (ten, duong_danh, 'OK'))
            ctx.close()
        # Màn hình hẹp
        for ten, duong_danh, tk in HEP:
            ctx = browser.new_context(viewport={'width': 390, 'height': 844},
                                      device_scale_factor=2, is_mobile=True,
                                      has_touch=True)
            page = ctx.new_page()
            page.goto(CO + '/accounts/login', wait_until='domcontentloaded')
            page.fill('input[name=username]', tk)
            page.fill('input[name=password]', MAT_KHAU)
            page.click('button[type=submit]')
            page.wait_for_load_state('networkidle')
            page.goto(CO + duong_danh, wait_until='networkidle')
            page.wait_for_timeout(250)
            page.screenshot(path=os.path.join(OUT, ten + '.png'), full_page=True)
            dong.append((ten, duong_danh, tk, 'Giao diện trên màn hình hẹp 390px', ''))
            print('%-20s %-26s %s' % (ten, duong_danh, 'OK (hep)'))
            ctx.close()
        # Cảnh báo lỗi nghiệp vụ: thanh toán vượt số còn phải thu.
        # Bỏ thuộc tính max rồi nhập số tiền vượt để thật sự gửi biểu mẫu.
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = ctx.new_page()
        page.goto(CO + '/accounts/login', wait_until='domcontentloaded')
        page.fill('input[name=username]', 'quan_ly')
        page.fill('input[name=password]', MAT_KHAU)
        page.click('button[type=submit]')
        page.wait_for_load_state('networkidle')
        page.goto(CO + '/repair-orders/10', wait_until='networkidle')
        page.evaluate("document.querySelector('input[name=amount]')"
                      ".removeAttribute('max')")
        page.fill('input[name=amount]', '99999999')
        page.click('button:has-text("Ghi nhận")')
        page.wait_for_load_state('networkidle')
        page.screenshot(path=os.path.join(OUT, '18_loi_thanh_toan.png'), full_page=True)
        dong.append(('18_loi_thanh_toan', '/repair-orders/10', 'quan_ly',
                     'Cảnh báo khi thanh toán vượt số còn phải thu', ''))
        print('%-20s %-26s %s' % ('18_loi_thanh_toan', '/repair-orders/10', 'OK'))
        ctx.close()
        browser.close()
    return ngay, dong


def viet_bang(ngay, dong):
    L = ['| Ảnh | Đường dẫn | Vai trò | Nội dung |', '|---|---|---|---|']
    for ten, duong_danh, tk, mo_ta, _ in dong:
        L.append('| ![%s](screenshots/%s.png) | `%s` | %s | %s |'
                 % (mo_ta, ten, duong_danh, tk, mo_ta))
    with open(os.path.join(BASE, 'docs', 'BANG_ANH.md'), 'w', encoding='utf-8') as f:
        f.write('<!-- Sinh tu dong boi docs/chup_man_hinh.py -->\n')
        f.write('\n| Hình | Màn hình | Vai trò | Đường dẫn |\n|---|---|---|---|\n')
        for ten, duong_danh, tk, mo_ta, _ in dong:
            f.write('| ![%s](screenshots/%s.png) | %s | `%s` | %s |\n'
                    % (mo_ta, ten, mo_ta, tk, duong_danh))
        f.write('\n> Chụp ngày %s trên ứng dụng đang chạy, dữ liệu lấy từ `seed_data.sql`.\n' % ngay)
    return len(dong)


if __name__ == '__main__':
    ngay, ds = chay()
    viet_bang(ngay, ds)
    print('Da chup %d man hinh vao %s' % (len(ds), OUT))
    print('Da viet bang anh vao docs/BANG_ANH.md')