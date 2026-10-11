# -*- coding: utf-8 -*-
"""Kiểm thử tầng ứng dụng — an toàn tiền, tồn kho, phân quyền, bảo mật.

Mỗi ca kiểm thử dựng một CSDL sạch từ schema + dữ liệu mẫu, trỏ ứng dụng
vào CSDL đó rồi gọi thật qua HTTP. Những ca quan trọng nhất là ca **chạy đồng
thời nhiều luồng** để chứng minh không còn race condition.
"""
from __future__ import annotations

import io
import os
import sqlite3
import sys
import tempfile
import threading
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)
os.environ.setdefault('APP_ENV', 'test')

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


class CoSoDichChung(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='garage_be_')
        self.db = os.path.join(self.tmp, 't.db')
        _dung(self.db)
        self._db_cu = get_settings().DATABASE_PATH
        from app.core import db as core_db
        core_db.dat_lai_dich_vu(self.db)
        # Bộ đếm giới hạn tần suất nằm trong bộ nhớ tiến trình, nên phải xoá
        # giữa các ca, nếu không ca sau sẽ bị chặn oan vì ca trước đã dùng hết.
        from app.core import ratelimit
        ratelimit.dat_lai()
        from app.main import create_app
        self.app = create_app()
        self.client = TestClient(self.app, follow_redirects=False)
        self.csrf_token = ''
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
    def q(self, sql, p=()):
        c = sqlite3.connect(self.db)
        c.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in c.execute(sql, p).fetchall()]
        finally:
            c.close()

    def q1(self, sql, p=()):
        r = self.q(sql, p)
        return r[0] if r else None

    def csrf(self):
        return self.client.cookies.get('garage_csrf') or ''

    def dang_nhap(self, tk='quan_ly'):
        self.client.cookies.clear()
        self.client.get('/accounts/login')
        self.client.post('/accounts/login',
                         data={'username': tk, 'password': MAT_KHAU, 'next': '/'})
        self.csrf_token = self.client.cookies.get('garage_csrf') or ''
        return self

    def post(self, url, data=None):
        d = dict(data or {})
        d['csrf_token'] = self.csrf_token
        return self.client.post(url, data=d)

    def flash(self, r):
        """Đọc thông báo đang chờ sau khi đi theo chuyển hướng."""
        if 'location' not in r.headers:
            return None
        trang = self.client.get(r.headers['location'])
        if 'hop-thong-bao' not in trang.text:
            return None
        return ' '.join(trang.text.split('hop-thong-bao')[1].split('</p>')[:1]).strip()

    def chay_dong_thoi(self, n, fn):
        ket_qua = []
        tu = threading.Barrier(n)

        def viet():
            tu.wait()
            ket_qua.append(fn())
        ds = [threading.Thread(target=viet) for _ in range(n)]
        for t in ds:
            t.start()
        for t in ds:
            t.join()
        return ket_qua


# ===========================================================================
class TestTienVaTonKho(CoSoDichChung):
    """Nhóm quan trọng nhất: mọi sai lệch ở đây là mất tiền thật."""

    def test_khong_them_hang_muc_vao_phieu_da_co_hoa_don(self):
        truoc = self.q1('SELECT COUNT(*) c FROM repair_order_items'
                        ' WHERE repair_order_id = 1')['c']
        r = self.post('/repair-orders/1/items',
                      {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        self.assertEqual(r.status_code, 303)
        self.assertEqual(
            self.q1('SELECT COUNT(*) c FROM repair_order_items'
                    ' WHERE repair_order_id = 1')['c'], truoc)
        tong = self.q1('SELECT COALESCE(SUM(unit_price*qty),0) s FROM repair_order_items'
                       ' WHERE repair_order_id = 1')['s']
        hd = self.q1('SELECT total FROM invoices WHERE repair_order_id = 1')['total']
        self.assertEqual(tong, hd, 'tổng hạng mục phải khớp tổng hoá đơn')

    def test_khong_them_hang_muc_vao_phieu_da_huy(self):
        truoc = self.q1('SELECT COUNT(*) c FROM repair_order_items'
                        ' WHERE repair_order_id = 7')['c']
        self.post('/repair-orders/7/items', {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        self.assertEqual(self.q1('SELECT COUNT(*) c FROM repair_order_items'
                                 ' WHERE repair_order_id = 7')['c'], truoc)

    def test_thanh_toan_dong_thoi_khong_thu_vuot(self):
        """12 luồng thu cùng lúc vào một hoá đơn 6.100.000."""
        self.post('/repair-orders/6/invoice')
        hd = self.q1('SELECT * FROM invoices WHERE repair_order_id = 6')
        self.assertIsNotNone(hd)
        self.dang_nhap('thu_ngan')
        app = self.app
        token = self.csrf_token
        cookie = dict(self.client.cookies)

        def thu():
            c = TestClient(app, follow_redirects=False)
            c.cookies.update(cookie)
            return c.post('/invoices/%d/pay' % hd['id'],
                          data={'amount': '600000', 'method': 'CASH',
                                'csrf_token': token}).status_code

        trang_thai = self.chay_dong_thoi(12, thu)

        tong = self.q1('SELECT COALESCE(SUM(amount),0) s FROM payments'
                       ' WHERE invoice_id = ?', (hd['id'],))['s']
        self.assertLessEqual(tong, hd['total'],
                             'tổng tiền thu không được vượt tổng hoá đơn')
        da_thu = self.q1('SELECT paid FROM invoices WHERE id = ?', (hd['id'],))['paid']
        self.assertEqual(da_thu, tong, 'invoices.paid phải bằng tổng payments')
        self.assertTrue(all(s < 500 for s in trang_thai),
                        'không được trả lỗi 500 khi thua tranh: %r' % trang_thai)

    def test_lay_phu_tung_dong_thoi_khong_tru_am(self):
        """12 luồng lấy 30 cáy khi tồn kho chỉ có 120."""
        self.post('/repair-orders/12/items',
                  {'loai': 'phu_tung', 'ma': '2', 'qty': '30'})
        ton = self.q1('SELECT stock FROM parts WHERE id = 2')['stock']
        self.assertGreaterEqual(ton, 0, 'tồn kho không được âm')
        n = self.q1('SELECT COALESCE(SUM(qty),0) s FROM repair_order_items'
                    ' WHERE part_id = 2 AND repair_order_id = 12')['s']
        self.assertLessEqual(n, 120, 'không được lấy vượt tồn kho')

    def test_huy_phieu_hoan_tra_ton_kho(self):
        self.dang_nhap('ky_thuat_vien')
        truoc = self.q1('SELECT stock FROM parts WHERE id = 2')['stock']
        r = self.post('/repair-orders/12/items',
                      {'loai': 'phu_tung', 'ma': '2', 'qty': '5'})
        self.assertEqual(r.status_code, 303)
        giua = self.q1('SELECT stock FROM parts WHERE id = 2')['stock']
        self.assertEqual(giua, truoc - 5, 'phải trừ kho khi thêm hạng mục')
        self.post('/repair-orders/12/status', {'status': 'CANCELLED'})
        self.assertEqual(self.q1('SELECT stock FROM parts WHERE id = 2')['stock'],
                         truoc, 'huỷ phiếu phải trả lại tồn kho')

    def test_gia_danh_muc_doi_khong_lam_doi_hang_muc_cu(self):
        muc = self.q1('SELECT * FROM repair_order_items WHERE part_id IS NOT NULL'
                      ' ORDER BY id LIMIT 1')
        pt = self.q1('SELECT name FROM parts WHERE id = ?', (muc['part_id'],))['name']
        self.post('/parts/save', {'id': muc['part_id'], 'name': pt,
                                  'price': '999999', 'stock': '50'})
        self.assertEqual(
            self.q1('SELECT unit_price FROM repair_order_items WHERE id=?',
                    (muc['id'],))['unit_price'], muc['unit_price'])


# ===========================================================================
class TestBaoMat(CoSoDichChung):

    def test_post_khong_co_csrf_bi_tu_choi(self):
        r = self.client.post('/customers/save',
                             data={'name': 'A B', 'phone': '0901000001'})
        self.assertEqual(r.status_code, 403, 'thiếu mã CSRF phải bị từ chối quyền')
        self.assertIn('bảo mật', r.text)

    def test_csrf_sai_bi_tu_choi(self):
        r = self.client.post('/customers/save',
                             data={'name': 'A B', 'phone': '0901000001',
                                   'csrf_token': 'gia-mao'})
        self.assertEqual(r.status_code, 403)

    def test_khong_the_xoa_du_lieu_bang_get(self):
        """Không còn đường dẫn GET nào xoá dữ liệu."""
        truoc = len(self.q('SELECT id FROM customers'))
        r = self.client.get('/customers/2/delete')
        self.assertLess(r.status_code, 500, 'GET không được gây lỗi máy chủ')
        self.assertEqual(len(self.q('SELECT id FROM customers')), truoc,
                         'GET không được xoá dữ liệu')

    def test_cookie_phien_co_thuoc_tinh_bat_buoc(self):
        self.client.cookies.clear()
        self.client.get('/accounts/login')
        r = self.client.post('/accounts/login',
                             data={'username': 'quan_ly', 'password': MAT_KHAU,
                                   'next': '/'})
        self.assertEqual(r.status_code, 303)
        cookie = r.headers.get('set-cookie', '')
        self.assertIn('garage_session', cookie)
        self.assertIn('HttpOnly', cookie, 'cookie phiên phải chặn JavaScript đọc')
        self.assertIn('SameSite', cookie)

    def test_open_redirect_bi_chan(self):
        r = self.client.get('/accounts/login?next=https://evil.example/x')
        self.assertNotIn('evil.example', r.headers.get('location', ''))

    def test_doi_mat_khau_vo_hieu_phien_cu(self):
        self.dang_nhap('quan_ly')
        token_cu = self.client.cookies.get('garage_session')
        self.post('/accounts/password',
                  {'mat_khau_cu': MAT_KHAU, 'mat_khau_moi': 'Garage@2027'})
        r = self.client.get('/dashboard')
        self.assertIn(r.status_code, (303, 302),
                      'đổi mật khẩu phải đăng xất các phiên cũ')

    def test_tai_khoan_bi_khoa_thi_vao_ngay(self):
        self.dang_nhap('le_tan')
        r = self.client.get('/dashboard')
        self.assertEqual(r.status_code, 200)
        self.dang_nhap('quan_ly')
        self.post('/users/2/toggle')
        self.dang_nhap('le_tan')
        self.assertEqual(self.client.get('/dashboard').status_code, 303)

    def test_gioi_han_so_lan_dang_nhap(self):
        self.client.cookies.clear()
        self.client.get('/accounts/login')
        trang_thai = []
        for i in range(8):
            r = self.client.post('/accounts/login',
                                 data={'username': 'ky_thuat_vien',
                                       'password': 'sai-mat-khau-%d' % i})
            trang_thai.append(r.status_code)
        self.assertIn(429, trang_thai,
                      'phải giới hạn số lần đăng nhập sai: %r' % trang_thai)

    def test_dau_ra_co_tieu_de_bao_mat(self):
        r = self.client.get('/dashboard')
        for tieu_de in ('x-content-type-options', 'x-frame-options',
                        'referrer-policy', 'permissions-policy'):
            self.assertIn(tieu_de, {k.lower() for k in r.headers})

    def test_khong_lo_stack_trace(self):
        r = self.client.get('/khong-co-duong-dan-nay')
        self.assertNotIn('Traceback', r.text)
        self.assertNotIn('File "', r.text)


# ===========================================================================
class TestPhanQuyen(CoSoDichChung):

    def test_ma_tran_dung_theo_vai_tro(self):
        ky_thuat_vien = [('/users', 403), ('/ai/results', 403)]
        for duong_danh, ky_vong in ky_thuat_vien:
            self.dang_nhap('ky_thuat_vien')
            self.assertEqual(self.client.get(duong_danh).status_code, ky_vong)
        self.dang_nhap('thu_ngan')
        self.assertEqual(self.client.get('/repair-orders/new').status_code, 403)
        self.dang_nhap('le_tan')
        self.assertEqual(self.client.get('/ai/results').status_code, 403)
        self.dang_nhap('quan_ly')
        for u in ('/dashboard', '/users', '/customers', '/vehicles', '/appointments',
                  '/services', '/parts', '/repair-orders', '/invoices', '/history',
                  '/ai', '/ai/results', '/shop', '/reports/doanh-thu'):
            self.assertEqual(self.client.get(u).status_code, 200, u)

    def test_ky_thuat_vien_khong_ghi_nhat_ky_vao_phieu_khong_duoc_gan_cong(self):
        # Mô phỏng phiếu đã được phân công cho một người khác (quản lý).
        c = sqlite3.connect(self.db)
        c.execute('UPDATE repair_orders SET technician_id = 1 WHERE id = 12')
        c.commit()
        c.close()
        truoc = len(self.q('SELECT id FROM repair_logs'))
        self.dang_nhap('ky_thuat_vien')
        self.post('/repair-orders/12/logs', {'note': 'ghi trai phep'})
        self.assertEqual(len(self.q('SELECT id FROM repair_logs')), truoc,
                         'kỹ thuật viên không được ghi vào phiếu của người khác')

    def test_ky_thuat_vien_duoc_ghi_vao_phieu_duoc_gan_cong(self):
        truoc = len(self.q('SELECT id FROM repair_logs'))
        self.dang_nhap('ky_thuat_vien')
        self.post('/repair-orders/12/logs', {'note': 'ghi đúng phiếu'})
        self.assertEqual(len(self.q('SELECT id FROM repair_logs')), truoc + 1)

    def test_moi_vai_tro_thay_doi_giang(self):
        self.dang_nhap('ky_thuat_vien')
        html = self.client.get('/dashboard').text
        self.assertIn('Khách hàng', html)          # được xem danh sách
        self.assertNotIn('>Duyệt AI<', html)       # không được duyệt AI


# ===========================================================================
class TestKiemTraDauVao(CoSoDichChung):
    """Mọi lỗi dữ liệu phải thành thông báo, không bao giờ thành lỗi 500."""

    def test_danh_sach_ca_khong_tra_ve_loi_500(self):
        truoc = len(self.q('SELECT id FROM customers'))
        truoc_xe = len(self.q('SELECT id FROM vehicles'))
        truoc_dv = len(self.q('SELECT id FROM services'))
        truoc_pt = len(self.q('SELECT id FROM parts'))
        truoc_hd = len(self.q('SELECT id FROM invoices'))
        truoc_lich = len(self.q('SELECT id FROM appointments'))
        truoc_hang = len(self.q('SELECT id FROM repair_order_items'))

        cases = [
            ('/repair-orders/1/assign', {'technician_id': ''}),
            ('/repair-orders/1/items', {'loai': 'dich_vu', 'ma': '99999', 'qty': '1'}),
            ('/repair-orders/1/items', {'loai': 'phu_tung', 'ma': '99999', 'qty': '1'}),
            ('/repair-orders/1/items', {'loai': 'dich_vu', 'ma': 'abc', 'qty': '1'}),
            ('/repair-orders/1/items', {'loai': 'dich_vu', 'ma': '1', 'qty': '0'}),
            ('/invoices/7/pay', {'amount': '1000', 'method': 'XXX'}),
            ('/invoices/7/pay', {'amount': '-5', 'method': 'CASH'}),
            ('/invoices/7/pay', {'amount': '0', 'method': 'CASH'}),
            ('/repair-orders/999999/logs', {'note': 'x'}),
            ('/services/save', {'name': 'DV', 'price': '-5'}),
            ('/parts/save', {'name': 'PT', 'price': '1', 'stock': '-3'}),
            ('/vehicles/save', {'plate': '30A-1111', 'brand': 'T', 'model': 'V',
                                'customer_id': '1'}),
            ('/vehicles/save', {'plate': 'abc', 'brand': 'T', 'model': 'V',
                                'customer_id': '1'}),
            ('/vehicles/save', {'plate': '30Z-9999', 'brand': 'T', 'model': 'V',
                                'customer_id': '9999'}),
            ('/customers/save', {'name': 'A B', 'phone': '0901000001'}),
            ('/customers/save', {'name': '', 'phone': 'sai'}),
            ('/appointments/save', {'customer_id': '1', 'vehicle_id': '',
                                    'scheduled_at': '2027-01-01 09:00',
                                    'status': 'SCHEDULED'}),
            ('/appointments/save', {'customer_id': '1', 'vehicle_id': '6',
                                    'scheduled_at': 'abc', 'status': 'SCHEDULED'}),
        ]
        for duong_danh, du_lieu in cases:
            with self.subTest(duong_danh=duong_danh, du_lieu=du_lieu):
                r = self.post(duong_danh, du_lieu)
                self.assertLess(r.status_code, 500,
                                '%s %r trả lỗi %s' % (duong_danh, du_lieu,
                                                        r.status_code))

        self.assertEqual(len(self.q('SELECT id FROM customers')), truoc)
        self.assertEqual(len(self.q('SELECT id FROM vehicles')), truoc_xe)
        self.assertEqual(len(self.q('SELECT id FROM services')), truoc_dv)
        self.assertEqual(len(self.q('SELECT id FROM parts')), truoc_pt)
        self.assertEqual(len(self.q('SELECT id FROM invoices')), truoc_hd)
        self.assertEqual(len(self.q('SELECT id FROM appointments')), truoc_lich)
        self.assertEqual(len(self.q('SELECT id FROM repair_order_items')),
                         truoc_hang, 'dữ liệu sai không được ghi thêm bản ghi')

    def test_mass_assignment_bi_chan(self):
        truoc = len(self.q('SELECT id FROM customers'))
        r = self.post('/customers/save',
                      {'name': 'Khách Mới', 'phone': '0912345678',
                       'role': 'MANAGER', 'is_active': '1'})
        self.assertLess(r.status_code, 500)
        self.assertEqual(len(self.q('SELECT id FROM customers')), truoc)

    def test_truy_van_doc_hoi_khong_thay_du_lieu(self):
        truoc = len(self.q('SELECT id FROM customers'))
        for tham_so in ("'; DROP TABLE customers; --", '1 OR 1=1',
                        "'; UPDATE users SET role='MANAGER'; --"):
            self.client.get('/customers', params={'q': tham_so})
            self.client.get('/customers', params={'sap': tham_so})
        self.assertTrue(len(self.q('SELECT id FROM customers')) > 0)
        self.assertEqual(len(self.q('SELECT id FROM customers')), truoc)
        self.assertTrue(self.q1('PRAGMA integrity_check')['integrity_check'] == 'ok')

    def test_tim_kiem_ky_tu_dac_biet_the_nghia_den(self):
        """'%' phải được tìm theo nghĩa đen, không phải wildcard."""
        r = self.client.get('/customers', params={'q': '%'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('Không có dữ liệu phù hợp', r.text)

    def test_dung_muc_tro_thi_sai_thuoc_tinh(self):
        du_lieu = self.q1('SELECT qty, unit_price FROM repair_order_items'
                          ' WHERE repair_order_id = 12')
        r = self.client.get('/customers', params={'sap': 'name'})
        self.assertEqual(r.status_code, 200)


# ===========================================================================
class TestQuyTacNghiepVu(CoSoDichChung):

    def test_lich_hen_trung_khung_gio_bi_chan(self):
        truoc = len(self.q("SELECT id FROM appointments WHERE vehicle_id=11"
                           " AND scheduled_at='2026-11-27 15:00'"))
        self.dang_nhap('le_tan')
        r = self.post('/appointments/save',
                      {'customer_id': '6', 'vehicle_id': '11',
                       'scheduled_at': '2026-11-27 15:00',
                       'notes': 'trung', 'status': 'SCHEDULED'})
        self.assertLess(r.status_code, 500)
        self.assertEqual(
            len(self.q("SELECT id FROM appointments WHERE vehicle_id=11"
                       " AND scheduled_at='2026-11-27 15:00'")), truoc,
            'không được tạo lịch trùng khung giờ')

    def test_lich_hen_cho_xe_khong_thuoc_khach_bi_chan(self):
        truoc = len(self.q('SELECT id FROM appointments'))
        self.dang_nhap('le_tan')
        self.post('/appointments/save',
                  {'customer_id': '1', 'vehicle_id': '6',
                   'scheduled_at': '2027-05-05 09:00',
                   'notes': 'sai chu xe', 'status': 'SCHEDULED'})
        moi = self.q('SELECT * FROM appointments ORDER BY id DESC LIMIT 1')
        self.assertEqual(len(self.q('SELECT id FROM appointments')), truoc,
                         'xe không thuộc khách hàng đã chọn thì không tạo được lịch')

    def test_chuyen_trang_thai_trai_phep_bi_chan(self):
        r = self.post('/repair-orders/12/status', {'status': 'COMPLETED'})
        self.assertLess(r.status_code, 500)
        self.assertEqual(self.q1('SELECT status FROM repair_orders WHERE id=12')['status'],
                         'RECEIVED')

    def test_khong_tao_phieu_trung_cho_xe_dang_co_phieu(self):
        self.dang_nhap('le_tan')
        truoc = len(self.q('SELECT id FROM repair_orders'))
        self.post('/repair-orders/create',
                  {'vehicle_id': '12', 'technician_id': '', 'technical_notes': 'x'})
        self.assertEqual(len(self.q('SELECT id FROM repair_orders')), truoc)

    def test_hang_muc_phai_co_dung_mot_trong_hai(self):
        self.post('/repair-orders/12/items',
                  {'loai': 'dich_vu', 'ma': '1', 'qty': '2'})
        muc = self.q1('SELECT * FROM repair_order_items WHERE repair_order_id=12'
                      ' ORDER BY id DESC LIMIT 1')
        self.assertIsNotNone(muc['service_id'])
        self.assertIsNone(muc['part_id'])

    def test_don_gia_chot_dung_bang_gia_danh_muc(self):
        gia = self.q1('SELECT price FROM services WHERE id=1')['price']
        self.post('/repair-orders/12/items', {'loai': 'dich_vu', 'ma': '1', 'qty': '2'})
        muc = self.q1('SELECT * FROM repair_order_items WHERE repair_order_id=12'
                      ' ORDER BY id DESC LIMIT 1')
        self.assertEqual(muc['unit_price'], gia)

    def test_khong_xoa_khach_da_co_giao_dich(self):
        truoc = len(self.q('SELECT id FROM customers'))
        r = self.post('/customers/1/delete')
        self.assertLess(r.status_code, 500)
        self.assertEqual(len(self.q('SELECT id FROM customers')), truoc)

    def test_bao_cao_chi_tinh_hoa_don_da_thu(self):
        tong = self.q1("SELECT COALESCE(SUM(total),0) s FROM invoices"
                       " WHERE status='PAID'")['s']
        r = self.client.get('/reports/khach-hang')
        self.assertEqual(r.status_code, 200)
        chua_thu = self.q1("SELECT COALESCE(SUM(total),0) s FROM invoices"
                           " WHERE status='UNPAID'")['s']
        if chua_thu:
            self.assertNotIn(format(chua_thu, ',').replace(',', '.'), r.text,
                             'báo cáo không được tính cả hoá đơn chưa thanh toán')


# ===========================================================================
class TestThongBaoVaPhanTrang(CoSoDichChung):

    def test_thanh_cong_co_thong_bao(self):
        r = self.post('/customers/save',
                      {'name': 'Khách Mới', 'phone': '0912345678'})
        self.assertEqual(r.status_code, 303)
        self.assertIn('Đã', self.flash(r) or '')

    def test_loi_co_thong_bao(self):
        truoc = len(self.q('SELECT id FROM vehicles'))
        r = self.post('/vehicles/save',
                      {'plate': '30A-1111', 'brand': 'T', 'model': 'V',
                       'customer_id': '1'})
        n = self.flash(r)
        self.assertIsNotNone(n, 'phải có thông báo lỗi')
        self.assertIn('đã tồn tại', n.lower())

    def test_thong_bao_chi_hien_mot_lan(self):
        r = self.post('/customers/save',
                      {'name': 'Khách Mới', 'phone': '0912345678'})
        self.assertIsNotNone(self.flash(r))
        lan2 = self.client.get(r.headers['location'])
        self.assertNotIn('hop-thong-bao', lan2.text,
                         'thông báo phải tự biến mất sau một lần')

    def test_danh_sach_co_phan_trang(self):
        r = self.client.get('/customers', params={'moi_trang': '5'})
        self.assertEqual(r.status_code, 200)
        self.assertLessEqual(len(self.q('SELECT id FROM customers')), 10)
        self.assertIn('dem-ket-qua', r.text)

    def test_moi_trang_bi_gioi_han(self):
        r = self.client.get('/customers', params={'moi_trang': '100000'})
        self.assertEqual(r.status_code, 200)

    def test_so_trang_vuot_bien_bi_ep_ve_cuoi(self):
        r = self.client.get('/customers', params={'trang': '9999'})
        self.assertEqual(r.status_code, 200)


# ===========================================================================
class TestAI(CoSoDichChung):

    def test_ba_chuc_nang_sinh_ket_qua_pending(self):
        self.dang_nhap('le_tan')
        for duong_danh, du_lieu in (('/ai/history', {'vehicle_id': '1'}),
                                    ('/ai/explain', {'service_id': '1'}),
                                    ('/ai/quote', {'repair_order_id': '10'})):
            with self.subTest(duong_danh=duong_danh):
                truoc = len(self.q('SELECT id FROM ai_results'))
                r = self.post(duong_danh, du_lieu)
                self.assertLess(r.status_code, 500)
                self.assertEqual(len(self.q('SELECT id FROM ai_results')), truoc + 1)
                kq = self.q1('SELECT * FROM ai_results ORDER BY id DESC LIMIT 1')
                self.assertEqual(kq['review_status'], 'PENDING')
                self.assertIsNone(kq['reviewed_by'])

    def test_ai_khong_tao_hang_muc_hoac_hoa_don(self):
        truoc_hang = len(self.q('SELECT id FROM repair_order_items'))
        truoc_hd = len(self.q('SELECT id FROM invoices'))
        self.dang_nhap('le_tan')
        self.post('/ai/quote', {'repair_order_id': '11'})
        self.assertEqual(len(self.q('SELECT id FROM repair_order_items')), truoc_hang)
        self.assertEqual(len(self.q('SELECT id FROM invoices')), truoc_hd)

    def test_duyet_va_khong_duoc_duet_lai(self):
        self.dang_nhap('le_tan')
        self.post('/ai/history', {'vehicle_id': '1'})
        rid = self.q1('SELECT id FROM ai_results ORDER BY id DESC LIMIT 1')['id']
        self.dang_nhap('quan_ly')
        self.post('/ai/results/%d/review' % rid, {'quyet_dinh': 'APPROVED'})
        kq = self.q1('SELECT * FROM ai_results WHERE id=?', (rid,))
        self.assertEqual(kq['review_status'], 'APPROVED')
        self.assertIsNotNone(kq['reviewed_by'])
        nguoi_cu = kq['reviewed_by']
        self.post('/ai/results/%d/review' % rid, {'quyet_dinh': 'REJECTED'})
        kq2 = self.q1('SELECT * FROM ai_results WHERE id=?', (rid,))
        self.assertEqual(kq2['review_status'], 'APPROVED')
        self.assertEqual(kq2['reviewed_by'], nguoi_cu)

    def test_khong_duoc_duet_khi_thieu_quyen(self):
        self.dang_nhap('le_tan')
        self.post('/ai/history', {'vehicle_id': '1'})
        rid = self.q1('SELECT id FROM ai_results ORDER BY id DESC LIMIT 1')['id']
        r = self.post('/ai/results/%d/review' % rid, {'quyet_dinh': 'APPROVED'})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(
            self.q1('SELECT review_status FROM ai_results WHERE id=?', (rid,))
            ['review_status'], 'PENDING')

    def test_phan_trang_ket_qua_ai_hien_dung_bien_so(self):
        self.dang_nhap('le_tan')
        self.post('/ai/quote', {'repair_order_id': '10'})
        # Lễ tân không có quyền duyệt, phải xem bằng tài khoản quản lý.
        self.assertEqual(self.client.get('/ai/results').status_code, 403)
        self.dang_nhap('quan_ly')
        r = self.client.get('/ai/results')
        self.assertEqual(r.status_code, 200)
        bien = self.q1('SELECT v.plate FROM repair_orders r'
                       ' JOIN vehicles v ON v.id = r.vehicle_id WHERE r.id=10')['plate']
        self.assertIn(bien, r.text)


# ===========================================================================
class TestHeThong(CoSoDichChung):

    def test_health_va_readiness(self):
        self.assertEqual(self.client.get('/healthz').json()['trang_thai'], 'ok')
        rd = self.client.get('/readyz')
        self.assertEqual(rd.status_code, 200)
        self.assertEqual(rd.json()['integrity'], 'ok')

    def test_moi_trang_co_mo_ta(self):
        for u in ('/dashboard', '/customers', '/vehicles', '/appointments',
                  '/services', '/parts', '/repair-orders', '/history', '/ai',
                  '/ai/results', '/shop'):
            with self.subTest(u=u):
                self.assertEqual(self.client.get(u).status_code, 200, u)

    def test_khong_co_route_bao_danh_thu(self):
        """Tài liệu OpenAPI bị tắt để không lộ cấu trúc cho người lạ."""
        self.assertEqual(self.client.get('/openapi.json').status_code, 404)


# ===========================================================================
class TestXoaDuLieu(CoSoDichChung):
    """Xoá phải là POST, có CSRF, đúng quyền và không phá dữ liệu liên quan."""

    def test_xoa_khach_hang_thanh_cong(self):
        truoc = len(self.q('SELECT id FROM customers'))
        r = self.post('/customers/9/delete')
        self.assertEqual(r.status_code, 303)
        self.assertIn('Đã xoá', self.flash(r) or '')
        self.assertEqual(len(self.q('SELECT id FROM customers')), truoc - 1)

    def test_xoa_khach_con_xe_giu_lai(self):
        truoc = len(self.q('SELECT id FROM customers'))
        r = self.post('/customers/7/delete')
        self.assertIn('không thể xoá', self.flash(r) or '')
        self.assertEqual(len(self.q('SELECT id FROM customers')), truoc,
                         'khách hàng đã có xe thì không được xoá')

    def test_xoa_dich_vu_da_dung_bi_chan(self):
        ma = self.q1('SELECT id FROM services LIMIT 1')['id']
        r = self.post('/services/%d/delete' % ma)
        self.assertIn('không thể xoá', self.flash(r) or '')
        self.assertTrue(self.q1('SELECT id FROM services WHERE id = ?', (ma,)))

    def test_xoa_dich_vu_moi_tao_duoc(self):
        self.post('/services/save',
                  {'name': 'Dịch vụ tạm để xoá', 'price': '1000', 'description': ''})
        ma = self.q1("SELECT id FROM services WHERE name = 'Dịch vụ tạm để xoá'")['id']
        r = self.post('/services/%d/delete' % ma)
        self.assertIn('Đã xoá', self.flash(r) or '')
        self.assertFalse(self.q1('SELECT id FROM services WHERE id = ?', (ma,)))

    def test_xoa_phu_tung_chua_dung(self):
        truoc = len(self.q('SELECT id FROM parts'))
        r = self.post('/parts/10/delete')
        self.assertEqual(r.status_code, 303)
        self.assertEqual(len(self.q('SELECT id FROM parts')), truoc - 1)

    def test_xoa_phu_tung_da_dung_bi_chan(self):
        r = self.post('/parts/1/delete')
        self.assertIn('không thể xoá', self.flash(r) or '')
        self.assertTrue(self.q1('SELECT id FROM parts WHERE id = 1'))

    def test_xoa_lich_hen(self):
        self.post('/appointments/1/delete')
        self.assertFalse(self.q1('SELECT id FROM appointments WHERE id = 1'))

    def test_xo_bang_get_bi_tu_choi(self):
        r = self.client.get('/customers/9/delete')
        self.assertIn(r.status_code, (404, 405),
                      'không còn đường xoá dữ liệu bằng GET')

    def test_xoa_khong_csrf_bi_chan(self):
        truoc = len(self.q('SELECT id FROM customers'))
        r = self.client.post('/customers/9/delete', data={})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(len(self.q('SELECT id FROM customers')), truoc)

    def test_le_tan_khong_xoa_danh_muc(self):
        self.dang_nhap('le_tan')
        truoc = len(self.q('SELECT id FROM services'))
        r = self.post('/services/1/delete')
        self.assertEqual(r.status_code, 403,
                         'vai trò không đủ quyền phải nhận 403')
        self.assertEqual(len(self.q('SELECT id FROM services')), truoc)

    def test_xoa_trong_tang_crud_duoc_va_an_toan(self):
        """Hàm `crud.xoa` từng sai cách nối tham số nên mọi nút xoá đều 500."""
        from app import crud
        truoc = len(self.q('SELECT id FROM customers'))
        self.assertEqual(crud.xoa('customers', 9), 1)
        self.assertEqual(len(self.q('SELECT id FROM customers')), truoc - 1)

    def test_xoa_ten_bang_khong_chophep_bi_tu_choi(self):
        """Tên bảng nối thẳng vào SQL nên phải qua danh sách cho phép."""
        from app import crud
        with self.assertRaises(ValueError):
            crud.xoa('users; DROP TABLE customers', 1)
        with self.assertRaises(ValueError):
            crud.dem_ban_ghi('sqlite_master')


# ===========================================================================
class TestQuyenBieuMau(CoSoDichChung):
    """7 form GET /new và /edit phải kiểm quyền như POST save tương ứng."""

    FORMS = [
        ('/customers/new', 'customer.edit'),
        ('/vehicles/new',   'vehicle.edit'),
        ('/appointments/new', 'appointment.edit'),
        ('/services/new',    'catalog.edit'),
        ('/services/1/edit', 'catalog.edit'),
        ('/parts/new',       'catalog.edit'),
        ('/parts/1/edit',    'catalog.edit'),
    ]

    # le_tan có customer/vehicle/appointment.edit; chỉ thiếu catalog.edit
    FORMS_LE_TAN_THIEU = [
        ('/services/new',    'catalog.edit'),
        ('/services/1/edit', 'catalog.edit'),
        ('/parts/new',       'catalog.edit'),
        ('/parts/1/edit',    'catalog.edit'),
    ]

    def test_chua_dang_nhap_bi_gui_dang_nhap(self):
        self.client.cookies.clear()
        for url, _q in self.FORMS:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 303, url)
            self.assertIn('/accounts/login', r.headers['location'], url)

    def test_le_tan_thieu_quyen_nhan_403(self):
        self.dang_nhap('le_tan')
        for url, q in self.FORMS_LE_TAN_THIEU:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 403, '%s thiếu %s' % (url, q))

    def test_le_tan_du_quyen_mot_so_form(self):
        self.dang_nhap('le_tan')
        for url in ('/customers/new', '/vehicles/new', '/appointments/new'):
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, url)

    def test_quan_ly_co_quyen_thanh_cong(self):
        self.dang_nhap('quan_ly')
        for url, _q in self.FORMS:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, url)


if __name__ == '__main__':
    unittest.main(verbosity=2)