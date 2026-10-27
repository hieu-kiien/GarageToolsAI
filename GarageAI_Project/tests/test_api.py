# -*- coding: utf-8 -*-
"""Kiểm thử tầng API JSON `/api/*` mà giao diện React gọi.

Mỗi ca dựng một CSDL sạch từ schema + dữ liệu mẫu, y hệt `test_backend.py`.
Nguyên tắc kiểm tra: API phải **trả đúng mã trạng thái**, **đúng bóng dữ
liệu** (phân trang, lỗi từng trường) và **đúng quyền** với từng vai trò —
không ca nào được phép ghi thẳng dữ liệu giả.
"""
from __future__ import annotations

import io
import os
import sqlite3
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)
os.environ.setdefault('APP_ENV', 'test')
os.environ.setdefault('AI_PROVIDER', 'mock')

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import logging                                                    # noqa: E402
logging.disable(logging.CRITICAL)

from fastapi.testclient import TestClient                          # noqa: E402
from app.core.config import get_settings                            # noqa: E402

MAT_KHAU = 'Garage@2026'


def _dung(path):
    conn = sqlite3.connect(path)
    conn.execute('PRAGMA foreign_keys = ON')
    for f in ('schema.sql', 'seed_data.sql'):
        with open(os.path.join(BASE, 'database', f), encoding='utf-8') as fh:
            conn.executescript(fh.read())
    conn.commit()
    conn.close()


class CoSoApi(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='garage_api_')
        self.db = os.path.join(self.tmp, 't.db')
        _dung(self.db)
        self._db_cu = get_settings().DATABASE_PATH
        from app.core import db as core_db
        core_db.dat_lai_dich_vu(self.db)
        from app.core import ratelimit
        ratelimit.dat_lai()
        from app.main import create_app
        self.app = create_app()
        self.client = TestClient(self.app, follow_redirects=False)
        # Lấy mã CSRF đúng như giao diện React: gọi API trước rồi đọc cookie.
        self.client.get('/api/auth/session')
        self.dang_nhap('quan_ly')

    def tearDown(self):
        from app.core import db as core_db
        core_db.dat_lai_dich_vu(self._db_cu)
        for f in (self.db, self.db + '-wal', self.db + '-shm'):
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass
        os.rmdir(self.tmp)

    # ------------------------------------------------------------ tiện ích
    def csrf(self):
        return self.client.cookies.get('garage_csrf') or ''

    def api(self, method, url, data=None):
        """Gọi API JSON đúng thói quen của frontend: JSON + header CSRF."""
        hd = {'X-CSRF-Token': self.csrf()}
        if method == 'get':
            return self.client.get(url, headers=hd)
        if method in ('post', 'put', 'patch'):
            return getattr(self.client, method)(url, json=data, headers=hd)
        # DELETE/HEAD của httpx không nhận tham số `json`.
        return getattr(self.client, method)(url, headers=hd)

    def dang_nhap(self, tk='quan_ly'):
        self.client.cookies.clear()
        self.client.get('/api/auth/session')
        r = self.client.post('/api/auth/login',
                             json={'username': tk, 'password': MAT_KHAU},
                             headers={'X-CSRF-Token': self.csrf()})
        assert r.status_code == 200, r.text
        return r

    def q1(self, sql, p=()):
        c = sqlite3.connect(self.db)
        c.row_factory = sqlite3.Row
        try:
            r = c.execute(sql, p).fetchone()
            return dict(r) if r else None
        finally:
            c.close()


# ===========================================================================
class TestPhienVaCsrf(CoSoApi):
    """Đăng nhập, mã CSRF, mã trạng thái lỗi."""

    def test_phien_chua_dang_nhap_va_cookie_csrf(self):
        self.client.cookies.clear()
        r = self.client.get('/api/auth/session')
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.json()['user'])
        self.assertTrue(self.csrf(), 'API phải đặt cookie garage_csrf cho JS đọc')

    def test_login_thieu_header_csrf_bi_tu_choi(self):
        self.client.cookies.clear()
        self.client.get('/api/auth/session')
        r = self.client.post('/api/auth/login',
                             json={'username': 'quan_ly', 'password': MAT_KHAU})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()['loi'], 'csrf_khong_hop_le')

    def test_login_sai_mat_khau_tra_401_json(self):
        self.client.cookies.clear()
        self.client.get('/api/auth/session')
        r = self.client.post(
            '/api/auth/login',
            json={'username': 'quan_ly', 'password': 'sai_mat_khau_123'},
            headers={'X-CSRF-Token': self.csrf()})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()['loi'], 'chua_xac_thuc')

    def test_chua_dang_nhap_thi_401(self):
        self.client.cookies.clear()
        self.client.get('/api/auth/session')
        for url in ('/api/orders', '/api/dashboard', '/api/users'):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 401, url)
            self.assertEqual(r.json()['loi'], 'chua_xac_thuc')

    def test_phan_trang_du_bao(self):
        r = self.client.get('/api/orders?trang=1')
        self.assertEqual(r.status_code, 200)
        p = r.json()
        self.assertEqual(sorted(k for k in p if k != 'dong'),
                         ['moi_trang', 'tong', 'tong_trang', 'trang'])
        self.assertGreater(len(p['dong']), 0)
        self.assertGreaterEqual(p['tong'], len(p['dong']))


# ===========================================================================
class TestDauVaoJson(CoSoApi):
    """Lỗi đầu vào phải trả JSON kèm lỗi theo từng trường."""

    def test_thieu_truong_bat_buoc(self):
        r = self.api('post', '/api/customers', {'name': 'Thieu so dien thoai'})
        self.assertEqual(r.status_code, 400)
        self.assertIn('phone', r.json().get('truong', {}))

    def test_truong_thua_bi_tu_choi(self):
        r = self.api('post', '/api/customers',
                     {'name': 'Truong thua', 'phone': '0901000098',
                      'role': 'MANAGER'})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['loi'], 'dau_vao_khong_hop_le')

    def test_tao_sua_khach_hang(self):
        r = self.api('post', '/api/customers',
                     {'name': 'Nguyen Van Test', 'phone': '0901000097'})
        self.assertEqual(r.status_code, 201)
        cid = r.json()['id']
        self.assertEqual(self.q1('SELECT name FROM customers WHERE id = ?', (cid,))['name'],
                         'Nguyen Van Test')
        r = self.api('put', '/api/customers/%d' % cid,
                     {'name': 'Nguyen Van Test Sua', 'phone': '0901000097'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.q1('SELECT name FROM customers WHERE id = ?', (cid,))['name'],
                         'Nguyen Van Test Sua')

    def test_khong_tao_duoc_tai_khoan_thieu_mat_khau(self):
        r = self.api('post', '/api/users',
                     {'username': 'nhan_vien_moi', 'full_name': 'Nhan Vien Moi',
                      'role': 'CASHIER'})
        self.assertEqual(r.status_code, 400)
        self.assertIn('password', r.json().get('truong', {}))


# ===========================================================================
class TestPhieuSuaChua(CoSoApi):
    """Luồng phiếu: tạo -> tiếp nhận -> hạng mục -> chuyển trạng thái."""

    def _tao_phieu(self):
        r = self.api('post', '/api/orders',
                     {'vehicle_id': 12, 'technical_notes': 'Tao bang API'})
        self.assertEqual(r.status_code, 201, r.text)
        return r.json()['id']

    def test_day_du_qua_api(self):
        oid = self._tao_phieu()
        self.assertEqual(self.q1('SELECT status FROM repair_orders WHERE id = ?', (oid,))['status'],
                         'RECEIVED')

        r = self.api('post', '/api/orders/%d/intake' % oid,
                     {'odometer_at_intake': '12345', 'fuel_level': 'HALF',
                      'notes': 'Bien ban API'})
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(
            self.q1('SELECT odometer_at_intake FROM intake_records'
                    ' WHERE repair_order_id = ?', (oid,))['odometer_at_intake'], 12345)

        r = self.api('post', '/api/orders/%d/items' % oid,
                     {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(len(r.json()['hang_muc']), 1)

        r = self.api('post', '/api/orders/%d/status' % oid, {'status': 'INSPECTING'})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.q1('SELECT status FROM repair_orders WHERE id = ?', (oid,))['status'],
                         'INSPECTING')

        # Nhảy cóc bị chặn đúng quy tắc chuyển trạng thái.
        r = self.api('post', '/api/orders/%d/status' % oid, {'status': 'COMPLETED'})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()['loi'], 'sai_quy_tac')

    def test_chi_tiet_tra_du_lieu_ben(self):
        r = self.client.get('/api/orders/1')
        self.assertEqual(r.status_code, 200)
        body = r.json()
        for khoa in ('phieu', 'hang_muc', 'nhat_ky', 'hoa_don'):
            self.assertIn(khoa, body)
        self.assertEqual(body['phieu']['id'], 1)
        self.assertGreater(len(body['hang_muc']), 0)

    def test_phan_cong_ky_thuat_vien(self):
        r = self.api('post', '/api/orders/12/assign', {'technician_id': 3})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(
            self.q1('SELECT technician_id FROM repair_orders WHERE id = 12')['technician_id'], 3)


# ===========================================================================
class TestBaoGia(CoSoApi):
    """Báo giá: tạo, thêm dòng, gửi, duyệt, áp dụng — đúng trạng thái."""

    def test_luong_du_qua_api(self):
        # Phiếu 12 là RECEIVED, chưa có hoá đơn — đúng điều kiện lập báo giá.
        r = self.api('post', '/api/quotations',
                     {'repair_order_id': 12, 'note': 'Bao gia API'})
        self.assertEqual(r.status_code, 201, r.text)
        qid = r.json()['id']

        r = self.api('post', '/api/quotations/%d/items' % qid,
                     {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        self.assertEqual(r.status_code, 201, r.text)

        r = self.api('post', '/api/quotations/%d/send' % qid)
        self.assertEqual(r.json()['bao_gia']['status'], 'SENT')

        r = self.api('post', '/api/quotations/%d/review' % qid,
                     {'quyet_dinh': 'APPROVED'})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()['bao_gia']['status'], 'APPROVED')

        r = self.api('post', '/api/quotations/%d/apply' % qid)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()['phieu_id'], 12)
        # Dòng áp dụng phải vào đúng phiếu, đúng đơn giá danh mục.
        row = self.q1('SELECT COUNT(*) c FROM repair_order_items'
                      ' WHERE repair_order_id = 12 AND service_id = 1')
        self.assertEqual(row['c'], 1)

    def test_duyet_bao_gia_can_quyen(self):
        r = self.api('post', '/api/quotations',
                     {'repair_order_id': 12, 'note': 'Ban nhap'})
        qid = r.json()['id']
        self.api('post', '/api/quotations/%d/items' % qid,
                 {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        self.api('post', '/api/quotations/%d/send' % qid)
        # Lễ tân có quote.manage nhưng không có quote.approve.
        self.dang_nhap('le_tan')
        r = self.api('post', '/api/quotations/%d/review' % qid,
                     {'quyet_dinh': 'APPROVED'})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()['loi'], 'khong_co_quyen')


# ===========================================================================
class TestHoaDonVaThanhToan(CoSoApi):
    """Tiền: tổng do backend tính, không thu vượt, không thu bằng 0."""

    def _phieu_hoanh_thanh_co_hang_muc(self):
        r = self.api('post', '/api/orders',
                     {'vehicle_id': 12, 'technical_notes': 'Kiem tien'})
        oid = r.json()['id']
        self.api('post', '/api/orders/%d/items' % oid,
                 {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        for tt in ('INSPECTING', 'ESTIMATING', 'REPAIRING', 'COMPLETED'):
            r = self.api('post', '/api/orders/%d/status' % oid, {'status': tt})
            self.assertEqual(r.status_code, 200, r.text)
        return oid

    def test_lap_hoa_don_chua_hoan_thanh_bi_chan(self):
        r = self.api('post', '/api/invoices', {'repair_order_id': 12})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()['loi'], 'sai_quy_tac')

    def test_thanh_toan_mot_phan_roi_het(self):
        oid = self._phieu_hoanh_thanh_co_hang_muc()
        r = self.api('post', '/api/invoices', {'repair_order_id': oid})
        self.assertEqual(r.status_code, 201, r.text)
        iid, tong = r.json()['id'], r.json()['hoa_don']['total']
        self.assertEqual(tong, 450000)

        # Quá tổng phải bị chặn.
        r = self.api('post', '/api/invoices/%d/payments' % iid,
                     {'amount': str(tong + 1), 'method': 'CASH'})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()['loi'], 'sai_quy_tac')

        r = self.api('post', '/api/invoices/%d/payments' % iid,
                     {'amount': str(tong - 1), 'method': 'CASH'})
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()['hoa_don']['status'], 'PARTIAL')

        r = self.api('post', '/api/invoices/%d/payments' % iid,
                     {'amount': '1', 'method': 'CASH'})
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()['hoa_don']['status'], 'PAID')
        self.assertEqual(r.json()['hoa_don']['paid'], tong)

    def test_thanh_toan_sai_du_lieu(self):
        r = self.api('post', '/api/invoices/7/payments',
                     {'amount': 'khong phai tien', 'method': 'CASH'})
        self.assertEqual(r.status_code, 400)
        self.assertIn('amount', r.json().get('truong', {}))


# ===========================================================================
class TestKhoBaoHanh(CoSoApi):
    def test_nhap_va_dieu_chinh_ton_kho(self):
        r = self.api('post', '/api/stock/receipt',
                     {'part_id': 1, 'qty': 5, 'note': 'kiem thu'})
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()['ton_kho'], 125)
        self.assertEqual(self.q1('SELECT stock FROM parts WHERE id = 1')['stock'], 125)

        r = self.api('post', '/api/stock/adjust',
                     {'part_id': 1, 'moi': 100, 'note': 'so du doi chieu'})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.q1('SELECT stock FROM parts WHERE id = 1')['stock'], 100)
        # Giao dịch phải được ghi vào sổ kho.
        n = self.q1('SELECT COUNT(*) c FROM stock_transactions WHERE part_id = 1')
        self.assertGreaterEqual(n['c'], 3)

    def test_so_kho_va_canh_bao(self):
        r = self.client.get('/api/stock')
        self.assertEqual(r.status_code, 200)
        body = r.json()
        for khoa in ('dong', 'tong', 'lech', 'canh_bao', 'ly_do'):
            self.assertIn(khoa, body)
        self.assertIsInstance(body['lech'], list)

    def test_bao_hanh_chi_cho_phieu_hoan_thanh(self):
        r = self.api('post', '/api/warranties',
                     {'repair_order_id': 12, 'months': 6, 'service_id': 1,
                      'start_date': '2026-11-14'})
        self.assertEqual(r.status_code, 409)

        r = self.api('get', '/api/warranties/eligible?repair_order_id=6')
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(r.json()['dong'], list)

        r = self.api('post', '/api/warranties',
                     {'repair_order_id': 6, 'months': 6, 'service_id': 2,
                      'start_date': '2026-11-14', 'note': 'kiem thu'})
        self.assertEqual(r.status_code, 201, r.text)
        wid = r.json()['id']
        r = self.api('get', '/api/warranties/%d' % wid)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['bao_hanh']['status'], 'ACTIVE')
        self.assertTrue(r.json()['bao_hanh']['nguoi_lap'])


# ===========================================================================
class TestAiVaPheDuyet(CoSoApi):
    def test_chay_ai_va_duyet(self):
        r = self.api('post', '/api/ai/run', {'kind': 'history', 'vehicle_id': 1})
        self.assertEqual(r.status_code, 201, r.text)
        rid = r.json()['id']
        self.assertEqual(self.q1('SELECT review_status FROM ai_results WHERE id = ?',
                                 (rid,))['review_status'], 'PENDING')

        r = self.api('post', '/api/ai/results/%d/review' % rid,
                     {'quyet_dinh': 'APPROVED'})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()['review_status'], 'APPROVED')
        # Không duyệt lại được kết quả đã xử lý.
        r = self.api('post', '/api/ai/results/%d/review' % rid,
                     {'quyet_dinh': 'APPROVED'})
        self.assertEqual(r.status_code, 409)

    def test_loai_ai_sai_bi_tu_choi(self):
        r = self.api('post', '/api/ai/run', {'kind': 'hack', 'vehicle_id': 1})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()['loi'], 'dau_vao_khong_hop_le')

    def test_khong_duyet_duoc_ai_khong_co_quyen(self):
        r = self.api('post', '/api/ai/run', {'kind': 'history', 'vehicle_id': 1})
        rid = r.json()['id']
        self.dang_nhap('le_tan')
        r = self.api('post', '/api/ai/results/%d/review' % rid,
                     {'quyet_dinh': 'APPROVED'})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()['loi'], 'khong_co_quyen')


# ===========================================================================
class TestPhanQuyen(CoSoApi):
    def test_tai_khoan_va_khoa_mo(self):
        r = self.api('post', '/api/users',
                     {'username': 'thu_ngan_moi', 'full_name': 'Thu Ngan Moi',
                      'role': 'CASHIER', 'password': 'MatKhau@123'})
        self.assertEqual(r.status_code, 201, r.text)
        uid = r.json()['id']
        r = self.api('post', '/api/users/%d/toggle' % uid)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()['is_active'])
        self.assertFalse(self.q1('SELECT is_active FROM users WHERE id = ?', (uid,))['is_active'])

    def test_thu_ngan_khong_quan_ly_duoc(self):
        self.dang_nhap('thu_ngan')
        self.assertEqual(self.client.get('/api/users').status_code, 403)
        self.assertEqual(self.client.get('/api/reports/doanh-thu').status_code, 403)
        r = self.api('post', '/api/orders', {'vehicle_id': 1})
        self.assertEqual(r.status_code, 403)
        # Vẫn xem được phiếu, xem và ghi được thanh toán (đúng vai trò thu ngân).
        self.assertEqual(self.client.get('/api/orders').status_code, 200)
        self.assertEqual(self.client.get('/api/invoices/7').status_code, 200)
        # Nhưng không xem được báo cáo doanh thu (đã chặn ở trên) và
        # không quản lý được tài khoản.
        self.assertEqual(self.client.get('/api/users').status_code, 403)

    def test_ky_thuat_vien_khong_tao_duoc_phieu(self):
        self.dang_nhap('ky_thuat_vien')
        r = self.api('post', '/api/orders', {'vehicle_id': 1})
        self.assertEqual(r.status_code, 403)
        r = self.api('post', '/api/ai/run', {'kind': 'history', 'vehicle_id': 1})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.client.get('/api/orders').status_code, 200)

    def test_ky_thuat_vien_co_lap_quyen_xem_va_chay_ai03_theo_phan_cong(self):
        # Phân công phiếu 12 cho kỹ thuật viên khác / bỏ phân công.
        self.api('post', '/api/orders/12/assign', {'technician_id': None})
        self.dang_nhap('ky_thuat_vien')
        ds = self.client.get('/api/orders?moi_trang=50').json()['dong']
        self.assertNotIn(12, [d['id'] for d in ds])
        self.assertIn(10, [d['id'] for d in ds])
        self.assertEqual(self.client.get('/api/orders/12').status_code, 403)
        self.assertEqual(self.client.get('/api/orders/10').status_code, 200)
        self.assertEqual(
            self.api('post', '/api/ai/run',
                     {'kind': 'quote', 'repair_order_id': 12}).status_code, 409)
        self.assertEqual(
            self.api('post', '/api/ai/run',
                     {'kind': 'quote', 'repair_order_id': 10}).status_code, 201)


# ===========================================================================
class TestBaoCaoVaTraCuu(CoSoApi):
    def test_bao_cao(self):
        r = self.client.get('/api/reports/doanh-thu')
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body['kind'], 'doanh-thu')
        self.assertIn('doanh-thu', body['loai'])
        self.assertIsInstance(body['dong'], list)

        r = self.client.get('/api/reports/khong-ton-tai')
        self.assertEqual(r.status_code, 404)

    def test_lich_su(self):
        r = self.client.get('/api/history')
        self.assertEqual(r.status_code, 200)
        self.assertIn('dong', r.json())

    def test_lookups(self):
        r = self.client.get('/api/lookups')
        self.assertEqual(r.status_code, 200)
        body = r.json()
        for khoa in ('khach_hang', 'xe', 'dich_vu', 'phu_tung', 'ky_thuat_vien',
                     'phieu', 'vai_tro', 'trang_thai', 'chuyen_trang_thai'):
            self.assertIn(khoa, body)
        # Không được lòi mật khẩu hay email ra bảng tra cứu.
        self.assertNotIn('password_hash', str(body))

    def test_meta(self):
        r = self.client.get('/api/meta')
        self.assertEqual(r.status_code, 200)
        body = r.json()
        for khoa in ('vai_tro', 'quyen', 'trang_thai', 'chuyen_trang_thai',
                     'kinh_ai', 'hinh_thuc_thanh_toan'):
            self.assertIn(khoa, body)
        self.assertIn('order.create', body['quyen'])


# ===========================================================================
class TestChongTaiPhat(CoSoApi):
    """Chống tái phát cho các lỗi P0/P1 đã sửa (xem KEP_HOACH_HOAN_THIEN.md)."""

    # ------------------------------------------------------------ báo giá
    def test_ap_dung_bao_gia_chi_mot_lan_va_tru_kho(self):
        ton_truoc = self.q1('SELECT stock FROM parts WHERE id = 1')['stock']
        r = self.api('post', '/api/quotations',
                     {'repair_order_id': 12, 'note': 'ap dung 2 lan'})
        qid = r.json()['id']
        self.api('post', '/api/quotations/%d/items' % qid,
                 {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        self.api('post', '/api/quotations/%d/items' % qid,
                 {'loai': 'phu_tung', 'ma': '1', 'qty': '3'})
        self.api('post', '/api/quotations/%d/send' % qid)
        r = self.api('post', '/api/quotations/%d/review' % qid,
                     {'quyet_dinh': 'APPROVED'})
        self.assertEqual(r.status_code, 200, r.text)

        r = self.api('post', '/api/quotations/%d/apply' % qid)
        self.assertEqual(r.status_code, 200, r.text)
        # Trừ kho đúng 3 cái qua sổ cái USAGE (không phải ghi thẳng stock).
        self.assertEqual(
            self.q1('SELECT stock FROM parts WHERE id = 1')['stock'],
            ton_truoc - 3)
        n_usage = self.q1(
            "SELECT COUNT(*) c FROM stock_transactions"
            " WHERE part_id = 1 AND reason = 'USAGE'"
            " AND note LIKE '%Áp dụng báo giá%'")['c']
        self.assertEqual(n_usage, 1)
        # Sổ khớp tồn: không có dòng nào lệch.
        self.assertEqual(self.client.get('/api/stock').json()['lech'], [])

        # Áp dụng lần hai phải bị chặn và không nhân đôi hạng mục/kho.
        r = self.api('post', '/api/quotations/%d/apply' % qid)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()['loi'], 'trung_du_lieu')
        self.assertEqual(
            self.q1('SELECT stock FROM parts WHERE id = 1')['stock'],
            ton_truoc - 3)
        dong = self.q1('SELECT COUNT(*) c FROM repair_order_items'
                       ' WHERE repair_order_id = 12 AND part_id = 1')['c']
        self.assertEqual(dong, 1)
        # Nút "áp dụng" tắt sau khi đã áp dụng.
        chi_tiet = self.api('get', '/api/quotations/%d' % qid).json()
        self.assertFalse(chi_tiet['co_ap_dung'])
        # Báo giá đã áp dụng không còn chặn báo giá mới cho phiếu.
        r = self.api('post', '/api/quotations',
                     {'repair_order_id': 12, 'note': 'ban moi'})
        self.assertEqual(r.status_code, 201, r.text)

    def test_tao_bao_gia_thu_hai_bi_chan(self):
        r = self.api('post', '/api/quotations',
                     {'repair_order_id': 12, 'note': 'nhap 1'})
        self.assertEqual(r.status_code, 201)
        r = self.api('post', '/api/quotations',
                     {'repair_order_id': 12, 'note': 'nhap 2'})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()['loi'], 'trung_du_lieu')

    # ------------------------------------------------------------ phiếu
    def test_nghiem_thu_chi_mot_lan(self):
        r = self.api('post', '/api/orders', {'vehicle_id': 12})
        oid = r.json()['id']
        self.api('post', '/api/orders/%d/items' % oid,
                 {'loai': 'dich_vu', 'ma': '2', 'qty': '1'})
        for tt in ('INSPECTING', 'ESTIMATING', 'REPAIRING', 'COMPLETED'):
            r = self.api('post', '/api/orders/%d/status' % oid, {'status': tt})
            self.assertEqual(r.status_code, 200, r.text)

        r = self.api('post', '/api/orders/%d/accept' % oid,
                     {'acceptance_note': 'khach nhan xe'})
        self.assertEqual(r.status_code, 200, r.text)
        lan_dau = self.q1('SELECT acceptance_at FROM repair_orders WHERE id = ?',
                          (oid,))['acceptance_at']
        self.assertTrue(lan_dau)

        # Bấm nghiệm thu lần hai: không ghi đè, không tạo nhật ký trùng.
        n_log = self.q1('SELECT COUNT(*) c FROM repair_logs'
                        ' WHERE repair_order_id = ?', (oid,))['c']
        r = self.api('post', '/api/orders/%d/accept' % oid,
                     {'acceptance_note': 'nhan lan nua'})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()['loi'], 'trung_du_lieu')
        hien_tai = self.q1('SELECT acceptance_at, acceptance_note'
                           ' FROM repair_orders WHERE id = ?', (oid,))
        self.assertEqual(hien_tai['acceptance_at'], lan_dau)
        self.assertEqual(hien_tai['acceptance_note'], 'khach nhan xe')
        self.assertEqual(self.q1('SELECT COUNT(*) c FROM repair_logs'
                                 ' WHERE repair_order_id = ?', (oid,))['c'],
                         n_log)

    def test_khong_them_dich_vu_ngung_hoat_dong(self):
        # Ngừng hoạt động dịch vụ 1 qua API danh mục (đúng vai trò quản lý).
        r = self.api('put', '/api/services/1',
                     {'name': 'Thay dầu máy va loc gio', 'price': '450000',
                      'description': 'Ngung dung thu', 'is_active': False})
        self.assertEqual(r.status_code, 200, r.text)

        r = self.api('post', '/api/orders/12/items',
                     {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.json()['loi'], 'sai_quy_tac')
        self.assertEqual(
            self.q1('SELECT COUNT(*) c FROM repair_order_items'
                    " WHERE repair_order_id = 12 AND service_id = 1")['c'], 0)

    def test_xoa_phieu_trang_va_chan_phieu_co_hoat_dong(self):
        r = self.api('post', '/api/orders', {'vehicle_id': 12})
        oid = r.json()['id']
        r = self.api('delete', '/api/orders/%d' % oid)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertIsNone(self.q1('SELECT id FROM repair_orders WHERE id = ?',
                                  (oid,)))
        # Xoá lần hai: 404, không 500.
        r = self.api('delete', '/api/orders/%d' % oid)
        self.assertEqual(r.status_code, 404)

        r = self.api('post', '/api/orders', {'vehicle_id': 12})
        oid2 = r.json()['id']
        self.api('post', '/api/orders/%d/items' % oid2,
                 {'loai': 'dich_vu', 'ma': '3', 'qty': '1'})
        r = self.api('delete', '/api/orders/%d' % oid2)
        self.assertEqual(r.status_code, 409)
        self.assertTrue(self.q1('SELECT id FROM repair_orders WHERE id = ?',
                                (oid2,)), 'Phiếu có hạng mục không được xoá')

    def test_nhap_bien_ban_chi_mot_lan(self):
        r = self.api('post', '/api/orders', {'vehicle_id': 12})
        oid = r.json()['id']
        r = self.api('post', '/api/orders/%d/intake' % oid,
                     {'odometer_at_intake': '12345', 'fuel_level': 'HALF',
                      'notes': 'lan 1'})
        self.assertEqual(r.status_code, 201, r.text)
        r = self.api('post', '/api/orders/%d/intake' % oid,
                     {'odometer_at_intake': '99999', 'fuel_level': 'EMPTY',
                      'notes': 'lan 2'})
        self.assertEqual(r.status_code, 409)
        ban = self.api('get', '/api/orders/%d' % oid).json()['tiep_nhan']
        self.assertEqual(ban['notes'], 'lan 1')

    def test_huy_phieu_tra_kho_mot_lan(self):
        ton_truoc = self.q1('SELECT stock FROM parts WHERE id = 2')['stock']
        r = self.api('post', '/api/orders', {'vehicle_id': 12})
        oid = r.json()['id']
        self.api('post', '/api/orders/%d/items' % oid,
                 {'loai': 'phu_tung', 'ma': '2', 'qty': '4'})
        self.assertEqual(
            self.q1('SELECT stock FROM parts WHERE id = 2')['stock'],
            ton_truoc - 4)

        r = self.api('post', '/api/orders/%d/status' % oid,
                     {'status': 'CANCELLED'})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(
            self.q1('SELECT stock FROM parts WHERE id = 2')['stock'],
            ton_truoc, 'Huỷ phiếu phải trả đủ 4 cái về kho')
        n_return = self.q1(
            "SELECT COUNT(*) c FROM stock_transactions"
            " WHERE part_id = 2 AND reason = 'RETURN' AND repair_order_id = ?",
            (oid,))['c']
        self.assertEqual(n_return, 1, 'Chỉ trả kho đúng một lần qua sổ cái')

        # CANCELLED là trạng thái cuối: không chuyển tiếp được nữa → không
        # thể trả kho lần thứ hai.
        r = self.api('post', '/api/orders/%d/status' % oid,
                     {'status': 'RECEIVED'})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(
            self.q1('SELECT stock FROM parts WHERE id = 2')['stock'],
            ton_truoc)
        self.assertEqual(self.client.get('/api/stock').json()['lech'], [])

    # ------------------------------------------------------------ danh mục
    def test_het_kho_loc_dung(self):
        # Ép hai mức tồn: một phụ tùng hết (0) và một còn đúng 1 cái —
        # lỗi cũ bỏ sót cả hai trường hợp.
        self.api('post', '/api/stock/adjust', {'part_id': 3, 'moi': 0,
                                                'note': 'het hang'})
        self.api('post', '/api/stock/adjust', {'part_id': 4, 'moi': 1,
                                                'note': 'con 1 cai'})
        r = self.api('get', '/api/parts?het_kho=1&moi_trang=100')
        self.assertEqual(r.status_code, 200)
        id_het = {d['id'] for d in r.json()['dong']}
        du_kien_het = {row['id'] for row in self._tat_ca(
            'SELECT id FROM parts WHERE stock = 0')}
        self.assertEqual(id_het, du_kien_het)
        self.assertIn(3, id_het)
        self.assertTrue(all(d['stock'] == 0 for d in r.json()['dong']))

        r = self.api('get', '/api/parts?het_kho=0&moi_trang=100')
        id_con = {d['id'] for d in r.json()['dong']}
        du_kien_con = {row['id'] for row in self._tat_ca(
            'SELECT id FROM parts WHERE stock > 0')}
        self.assertEqual(id_con, du_kien_con)
        # Phụ tùng còn đúng 1 cái phải NẰM TRONG danh sách "còn hàng".
        self.assertIn(4, id_con)
        self.assertNotIn(3, id_con)

    def _tat_ca(self, sql, p=()):
        c = sqlite3.connect(self.db)
        c.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in c.execute(sql, p).fetchall()]
        finally:
            c.close()

    # ------------------------------------------------------------ tiền
    def test_huy_khoan_thu_cap_nhat_lai_da_thu(self):
        r = self.api('post', '/api/orders', {'vehicle_id': 12})
        oid = r.json()['id']
        self.api('post', '/api/orders/%d/items' % oid,
                 {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        for tt in ('INSPECTING', 'ESTIMATING', 'REPAIRING', 'COMPLETED'):
            self.api('post', '/api/orders/%d/status' % oid, {'status': tt})
        r = self.api('post', '/api/invoices', {'repair_order_id': oid})
        iid, tong = r.json()['id'], r.json()['hoa_don']['total']

        r = self.api('post', '/api/invoices/%d/payments' % iid,
                     {'amount': '100000', 'method': 'CASH'})
        self.assertEqual(r.status_code, 201, r.text)
        khoan_id = self.q1('SELECT id FROM payments WHERE invoice_id = ?',
                           (iid,))['id']
        self.assertEqual(
            self.q1('SELECT paid FROM invoices WHERE id = ?', (iid,))['paid'],
            100000)

        # Huỷ khoản thu: tổng đã thu và trạng thái phải tính lại.
        r = self.api('post', '/api/invoices/%d/payments/%d/cancel'
                     % (iid, khoan_id))
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()['hoa_don']['paid'], 0)
        self.assertEqual(r.json()['hoa_don']['status'], 'UNPAID')
        self.assertEqual(r.json()['khoan_thu'], [])
        # Huỷ lần hai: khoản đã xoá → 404, không 500.
        r = self.api('post', '/api/invoices/%d/payments/%d/cancel'
                     % (iid, khoan_id))
        self.assertEqual(r.status_code, 404)
        self.assertEqual(
            self.q1('SELECT paid FROM invoices WHERE id = ?', (iid,))['paid'], 0)
        self.assertGreaterEqual(tong, 0)

    # ------------------------------------------------------------ AI / đầu vào
    def test_ai_khong_tim_thay_tra_404(self):
        r = self.api('post', '/api/ai/run', {'kind': 'history',
                                             'vehicle_id': 99999})
        self.assertEqual(r.status_code, 404, r.text)
        self.assertEqual(r.json()['loi'], 'khong_tim_thay')

    def test_thien_dau_vao_sai_tra_400_khong_phai_422(self):
        r = self.api('post', '/api/ai/run', [])
        self.assertEqual(r.status_code, 400, r.text)
        self.assertEqual(r.json()['loi'], 'dau_vao_khong_hop_le')

        r = self.api('post', '/api/ai/run',
                     {'kind': 'history', 'vehicle_id': 'khong phai so'})
        self.assertEqual(r.status_code, 400, r.text)
        self.assertIn('vehicle_id', r.json().get('truong', {}))

    def test_trang_thai_khong_hop_le_tra_400(self):
        r = self.api('post', '/api/orders/12/status', {'status': 'XYZ'})
        self.assertEqual(r.status_code, 400, r.text)
        self.assertEqual(r.json()['loi'], 'dau_vao_khong_hop_le')
        self.assertEqual(
            self.q1('SELECT status FROM repair_orders WHERE id = 12')['status'],
            'RECEIVED')

    # ------------------------------------------------------------ tài khoản
    def test_khong_tu_sua_tai_khoan_chinh_minh(self):
        user = self.client.get('/api/auth/session').json()['user']
        r = self.api('post', '/api/users',
                     {'id': user['id'], 'username': 'quan_ly',
                      'full_name': 'Doi Vai Tro', 'email': 'huy.nguyen@garage.vn',
                      'role': 'TECHNICIAN', 'is_active': True})
        self.assertEqual(r.status_code, 403, r.text)
        self.assertEqual(r.json()['loi'], 'khong_co_quyen')
        self.assertEqual(
            self.q1('SELECT role FROM users WHERE id = ?', (user['id'],))['role'],
            'MANAGER')

    def test_doi_mat_khau_qua_quan_ly_co_hieu_luc(self):
        r = self.api('post', '/api/users',
                     {'id': 2, 'username': 'le_tan', 'full_name': 'Tran Thu Ha',
                      'email': 'ha.tran@garage.vn', 'role': 'RECEPTIONIST',
                      'is_active': True, 'password': 'Moi@2026x'})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(self.q1(
            "SELECT password_hash FROM users WHERE id = 2")['password_hash'])

        # Mật khẩu cũ hết hiệu lực, mật khẩu mới đăng nhập được.
        self.client.cookies.clear()
        self.client.get('/api/auth/session')
        r = self.client.post('/api/auth/login',
                             json={'username': 'le_tan', 'password': MAT_KHAU},
                             headers={'X-CSRF-Token': self.csrf()})
        self.assertEqual(r.status_code, 401)
        r = self.client.post('/api/auth/login',
                             json={'username': 'le_tan', 'password': 'Moi@2026x'},
                             headers={'X-CSRF-Token': self.csrf()})
        self.assertEqual(r.status_code, 200, r.text)

    def test_sua_khach_va_xe_khong_ton_tai_tra_404(self):
        r = self.api('put', '/api/customers/99999',
                     {'name': 'Khong Ton Tai', 'phone': '0911222333'})
        self.assertEqual(r.status_code, 404, r.text)
        self.assertEqual(r.json()['loi'], 'khong_tim_thay')

        r = self.api('put', '/api/vehicles/99999',
                     {'plate': '30Z-99999', 'brand': 'Toyota',
                      'model': 'Vios', 'customer_id': 1})
        self.assertEqual(r.status_code, 404, r.text)
        self.assertEqual(r.json()['loi'], 'khong_tim_thay')

    def test_trung_ten_dich_vu_tra_409_khong_phai_500(self):
        ten_co_san = self.q1('SELECT name FROM services WHERE id = 1')['name']
        r = self.api('post', '/api/services',
                     {'name': ten_co_san, 'price': 200000})
        self.assertEqual(r.status_code, 409, r.text)
        self.assertEqual(r.json()['loi'], 'trung_du_lieu')

    def test_xoa_dich_vu_phu_tung_dang_dung_trong_bao_gia_bi_chan(self):
        r = self.api('post', '/api/services',
                     {'name': 'Dich Vu Thu Bao Gia', 'price': 150000})
        sid = r.json()['id']
        r = self.api('post', '/api/parts',
                     {'name': 'Phu Tung Thu Bao Gia', 'sku': 'PT-BG-01',
                      'price': 250000, 'stock': 5})
        pid = r.json()['id']

        r = self.api('post', '/api/quotations', {'repair_order_id': 12})
        qid = r.json()['id']
        self.api('post', '/api/quotations/%d/items' % qid,
                 {'loai': 'dich_vu', 'ma': sid, 'qty': 1})
        self.api('post', '/api/quotations/%d/items' % qid,
                 {'loai': 'phu_tung', 'ma': pid, 'qty': 1})

        self.assertEqual(self.api('delete', '/api/services/%d' % sid).status_code, 409)
        self.assertEqual(self.api('delete', '/api/parts/%d' % pid).status_code, 409)

    def test_chan_tao_phieu_voi_xe_hoac_ktv_ngung_hoat_dong(self):
        xe = self.q1('SELECT * FROM vehicles WHERE id = 12')
        self.api('put', '/api/vehicles/12',
                 {'plate': xe['plate'], 'brand': xe['brand'],
                  'model': xe['model'], 'customer_id': xe['customer_id'],
                  'is_active': False})
        r = self.api('post', '/api/orders', {'vehicle_id': 12})
        self.assertEqual(r.status_code, 409, r.text)

        self.api('put', '/api/vehicles/12',
                 {'plate': xe['plate'], 'brand': xe['brand'],
                  'model': xe['model'], 'customer_id': xe['customer_id'],
                  'is_active': True})
        self.api('post', '/api/users/3/toggle')
        r = self.api('post', '/api/orders',
                     {'vehicle_id': 12, 'technician_id': 3})
        self.assertEqual(r.status_code, 409, r.text)

    def test_chan_tao_bao_gia_cho_phieu_da_hoan_thanh_va_bao_cao_dich_vu_tach_phu_tung(self):
        # Phiếu #1 trong seed đang ở trạng thái COMPLETED.
        r = self.api('post', '/api/quotations', {'repair_order_id': 1})
        self.assertEqual(r.status_code, 409, r.text)

        # Báo cáo dịch vụ chỉ chứa tên nằm trong bảng services, không lẫn parts.
        bc = self.client.get('/api/reports/dich-vu').json()['dong']
        ten_dich_vu = {r['name'] for r in self._tat_ca('SELECT name FROM services')}
        for d in bc:
            self.assertIn(d['ten'], ten_dich_vu)

    def test_gia_tien_boolean_bi_tu_choi_400(self):
        r = self.api('post', '/api/services',
                     {'name': 'Dich Vu Boolean', 'price': True})
        self.assertEqual(r.status_code, 400, r.text)
        self.assertEqual(r.json()['loi'], 'dau_vao_khong_hop_le')

    def test_chan_ap_dung_bao_gia_khi_phieu_da_co_hang_muc_trung(self):
        ton_truoc = self.q1('SELECT stock FROM parts WHERE id = 1')['stock']
        # Nhân viên đã thêm tay phụ tùng 1 vào phiếu 12 (trừ kho 2 cái).
        self.api('post', '/api/orders/12/items',
                 {'loai': 'phu_tung', 'ma': 1, 'qty': 2})
        self.assertEqual(
            self.q1('SELECT stock FROM parts WHERE id = 1')['stock'],
            ton_truoc - 2)
        # Lập báo giá cũng chứa phụ tùng 1 rồi duyệt và bấm áp dụng -> phải chặn 409.
        qid = self.api('post', '/api/quotations', {'repair_order_id': 12}).json()['id']
        self.api('post', '/api/quotations/%d/items' % qid,
                 {'loai': 'phu_tung', 'ma': 1, 'qty': 2})
        self.api('post', '/api/quotations/%d/send' % qid)
        self.api('post', '/api/quotations/%d/review' % qid,
                 {'quyet_dinh': 'APPROVED'})
        r = self.api('post', '/api/quotations/%d/apply' % qid)
        self.assertEqual(r.status_code, 409, r.text)
        self.assertEqual(r.json()['loi'], 'trung_du_lieu')
        # Kho không bị trừ thêm lần 2 và dòng hạng mục trên phiếu không bị nhân đôi.
        self.assertEqual(
            self.q1('SELECT stock FROM parts WHERE id = 1')['stock'],
            ton_truoc - 2)
        self.assertEqual(
            self.q1('SELECT COUNT(*) c FROM repair_order_items'
                    ' WHERE repair_order_id = 12 AND part_id = 1')['c'], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
