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
        # Xe 11 đang có phiếu 12 ở trạng thái RECEIVED.
        self.post('/repair-orders/create',
                  {'vehicle_id': '11', 'technician_id': '', 'technical_notes': 'x'})
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
                                    ('/ai/history', {'vehicle_id': '6'}),
                                    ('/ai/explain', {'service_id': '1'}),
                                    ('/ai/explain', {'service_id': '7'}),
                                    ('/ai/quote', {'repair_order_id': '10'})):
            with self.subTest(duong_danh=duong_danh, du_lieu=du_lieu):
                truoc = len(self.q('SELECT id FROM ai_results'))
                r = self.post(duong_danh, du_lieu)
                self.assertLess(r.status_code, 500)
                self.assertEqual(len(self.q('SELECT id FROM ai_results')), truoc + 1)
                kq = self.q1('SELECT * FROM ai_results ORDER BY id DESC LIMIT 1')
                self.assertEqual(kq['review_status'], 'PENDING')
                self.assertIsNone(kq['reviewed_by'])
                if du_lieu == {'service_id': '7'}:
                    self.assertIn('Danh mục chưa có mô tả cho dịch vụ này', kq['output_text'])

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
        # Tạo phụ tùng mới (stock 0, chưa có ledger) rồi xoá.
        self.post('/parts/save', {'name': 'PT tạm để xoá', 'price': '1000',
                                  'stock': '0', 'sku': 'TMP-DEL'})
        pid = self.q1("SELECT id FROM parts WHERE sku = 'TMP-DEL'")['id']
        truoc = len(self.q('SELECT id FROM parts'))
        r = self.post('/parts/%d/delete' % pid)
        self.assertEqual(r.status_code, 303)
        self.assertEqual(len(self.q('SELECT id FROM parts')), truoc - 1)

    def test_xoa_phu_tung_co_so_kho_bi_chan(self):
        """Phụ tùng có dòng ledger (số dư đầu kỳ) không xoá được."""
        r = self.post('/parts/10/delete')
        self.assertIn('giao dịch kho', self.flash(r) or '')
        self.assertTrue(self.q1('SELECT id FROM parts WHERE id = 10'))

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


# ===========================================================================
class TestXeMoiTruong(CoSoDichChung):
    """VIN / màu sơn / số km — thêm mới và kiểm tra hợp lệ."""

    def test_tao_xe_co_vin_mau_odo(self):
        r = self.post('/vehicles/save', {
            'plate': '29B-99999', 'brand': 'Toyota', 'model': 'Corolla',
            'year': '2022', 'vin': 'JTDBR32E120012345', 'color': 'Trắng',
            'odometer': '15000', 'customer_id': '1'})
        self.assertEqual(r.status_code, 303)
        xe = self.q1("SELECT * FROM vehicles WHERE plate = '29B-99999'")
        self.assertEqual(xe['vin'], 'JTDBR32E120012345')
        self.assertEqual(xe['color'], 'Trắng')
        self.assertEqual(xe['odometer'], 15000)

    def test_vin_trung_bi_chan(self):
        self.post('/vehicles/save', {
            'plate': '29B-88888', 'brand': 'Honda', 'model': 'City',
            'year': '2021', 'vin': 'MR0FR31E120012345', 'customer_id': '1'})
        r = self.post('/vehicles/save', {
            'plate': '29B-77777', 'brand': 'Mazda', 'model': '3',
            'year': '2020', 'vin': 'MR0FR31E120012345', 'customer_id': '1'})
        self.assertIn('VIN', self.flash(r) or '')

    def test_vin_sai_dinh_dang_bi_chan(self):
        r = self.post('/vehicles/save', {
            'plate': '29B-66666', 'brand': 'Ford', 'model': 'Ranger',
            'year': '2023', 'vin': 'AB', 'customer_id': '1'})
        self.assertIn('VIN', self.flash(r) or '')

    def test_odo_am_bi_chan(self):
        r = self.post('/vehicles/save', {
            'plate': '29B-55555', 'brand': 'Kia', 'model': 'Morning',
            'year': '2019', 'odometer': '-5', 'customer_id': '1'})
        self.assertIn('km', self.flash(r) or '')


# ===========================================================================
class TestTiepNhanNghiemThu(CoSoDichChung):
    """Biên bản tiếp nhận và nghiệm thu xe."""

    def _phieu_moi(self):
        """Tạo phiếu RECEIVED cho xe 1 (id=1 trong seed)."""
        self.post('/repair-orders/create', {'vehicle_id': '1'})
        return self.q1("SELECT id FROM repair_orders ORDER BY id DESC LIMIT 1")['id']

    def test_tiep_nhan_thanh_cong(self):
        oid = self._phieu_moi()
        r = self.post('/repair-orders/%d/intake' % oid, {
            'odometer_at_intake': '50000', 'fuel_level': 'HALF',
            'exterior_condition': 'Trầy nhẹ cản trước',
            'accessories': '2 chìa khoá, camera hành trình',
            'notes': 'Khách gửi xe qua đêm'})
        self.assertEqual(r.status_code, 303)
        self.assertIn('biên bản tiếp nhận', self.flash(r) or '')
        rec = self.q1('SELECT * FROM intake_records WHERE repair_order_id = ?', (oid,))
        self.assertIsNotNone(rec)
        self.assertEqual(rec['odometer_at_intake'], 50000)
        self.assertEqual(rec['fuel_level'], 'HALF')

    def test_tiep_nhan_cap_nhat_odo_xe(self):
        oid = self._phieu_moi()
        self.post('/repair-orders/%d/intake' % oid,
                  {'odometer_at_intake': '62000', 'fuel_level': 'FULL'})
        xe = self.q1('SELECT odometer FROM vehicles WHERE id = 1')
        self.assertEqual(xe['odometer'], 62000)

    def test_tiep_nhan_lan_hai_bi_chan(self):
        oid = self._phieu_moi()
        self.post('/repair-orders/%d/intake' % oid, {'odometer_at_intake': '1000'})
        r = self.post('/repair-orders/%d/intake' % oid, {'odometer_at_intake': '2000'})
        self.assertIn('đã có biên bản', self.flash(r) or '')

    def test_tiep_nhan_khi_da_sua_xong_bi_chan(self):
        oid = self._phieu_moi()
        c = sqlite3.connect(self.db)
        c.execute("UPDATE repair_orders SET status = 'COMPLETED' WHERE id = ?", (oid,))
        c.commit(); c.close()
        r = self.post('/repair-orders/%d/intake' % oid, {'odometer_at_intake': '1000'})
        self.assertIn('Chỉ ghi biên bản', self.flash(r) or '')

    def test_nghiem_thu_thanh_cong(self):
        oid = self._phieu_moi()
        c = sqlite3.connect(self.db)
        c.execute("UPDATE repair_orders SET status = 'COMPLETED' WHERE id = ?", (oid,))
        c.commit(); c.close()
        r = self.post('/repair-orders/%d/accept' % oid,
                      {'acceptance_note': 'Khách hài lòng'})
        self.assertEqual(r.status_code, 303)
        self.assertIn('nghiệm thu', self.flash(r) or '')
        p = self.q1('SELECT * FROM repair_orders WHERE id = ?', (oid,))
        self.assertIsNotNone(p['acceptance_at'])
        self.assertEqual(p['acceptance_note'], 'Khách hài lòng')

    def test_nghiem_thu_lan_hai_bi_chan(self):
        oid = self._phieu_moi()
        c = sqlite3.connect(self.db)
        c.execute("UPDATE repair_orders SET status = 'COMPLETED' WHERE id = ?", (oid,))
        c.commit(); c.close()
        self.post('/repair-orders/%d/accept' % oid, {'acceptance_note': 'OK'})
        r = self.post('/repair-orders/%d/accept' % oid, {'acceptance_note': 'OK nữa'})
        self.assertIn('đã được nghiệm thu', self.flash(r) or '')

    def test_nghiem_thu_khi_chua_hoan_thanh_bi_chan(self):
        oid = self._phieu_moi()
        r = self.post('/repair-orders/%d/accept' % oid, {'acceptance_note': 'x'})
        self.assertIn('Chỉ nghiệm thu', self.flash(r) or '')

    def test_le_tan_du_quyen_nghiem_thu(self):
        self.dang_nhap('le_tan')
        oid = self._phieu_moi()
        c = sqlite3.connect(self.db)
        c.execute("UPDATE repair_orders SET status = 'COMPLETED' WHERE id = ?", (oid,))
        c.commit(); c.close()
        r = self.post('/repair-orders/%d/accept' % oid, {'acceptance_note': 'OK'})
        self.assertEqual(r.status_code, 303)

    def test_thu_ngan_khong_nghiem_thu(self):
        self.dang_nhap('thu_ngan')
        oid = self._phieu_moi()
        c = sqlite3.connect(self.db)
        c.execute("UPDATE repair_orders SET status = 'COMPLETED' WHERE id = ?", (oid,))
        c.commit(); c.close()
        r = self.post('/repair-orders/%d/accept' % oid, {'acceptance_note': 'x'})
        self.assertEqual(r.status_code, 403)


# ===========================================================================
class TestBaoGia(CoSoDichChung):
    """Báo giá chính thức: tạo, hạng mục, gửi, duyệt, áp dụng."""

    def _bg_moi(self, phieu_id=10):
        """Phiếu 10 ở REPAIRING trong seed — phù hợp báo giá."""
        self.post('/quotations/create',
                  {'repair_order_id': str(phieu_id), 'note': 'Báo giá test'})
        bg = self.q1('SELECT id FROM quotations ORDER BY id DESC LIMIT 1')
        return bg['id']

    def test_tao_bao_gia_thanh_cong(self):
        qid = self._bg_moi()
        self.assertIsNotNone(qid)
        bg = self.q1('SELECT * FROM quotations WHERE id = ?', (qid,))
        self.assertEqual(bg['status'], 'DRAFT')
        self.assertEqual(bg['total'], 0)

    def test_tao_bao_gia_trung_bi_chan(self):
        self._bg_moi()
        truoc = len(self.q('SELECT id FROM quotations'))
        self.post('/quotations/create', {'repair_order_id': '10'})
        self.assertEqual(len(self.q('SELECT id FROM quotations')), truoc)

    def test_them_hang_muc_dich_vu(self):
        qid = self._bg_moi()
        self.post('/quotations/%d/items' % qid, {'loai': 'dich_vu', 'ma': '1', 'qty': '2'})
        item = self.q1('SELECT * FROM quotation_items WHERE quotation_id = ?', (qid,))
        self.assertIsNotNone(item)
        self.assertIsNotNone(item['service_id'])
        self.assertIsNone(item['part_id'])
        gia = self.q1('SELECT price FROM services WHERE id = 1')['price']
        self.assertEqual(item['unit_price'], gia)

    def test_tong_duoc_tinh_lai(self):
        qid = self._bg_moi()
        self.post('/quotations/%d/items' % qid, {'loai': 'dich_vu', 'ma': '1', 'qty': '2'})
        self.post('/quotations/%d/items' % qid, {'loai': 'phu_tung', 'ma': '3', 'qty': '1'})
        bg = self.q1('SELECT total FROM quotations WHERE id = ?', (qid,))
        expected = self.q1(
            'SELECT COALESCE(SUM(unit_price*qty),0) s FROM quotation_items'
            ' WHERE quotation_id = ?', (qid,))['s']
        self.assertEqual(bg['total'], expected)
        self.assertGreater(bg['total'], 0)

    def test_gui_bao_gia(self):
        qid = self._bg_moi()
        self.post('/quotations/%d/items' % qid, {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        r = self.post('/quotations/%d/send' % qid)
        self.assertEqual(r.status_code, 303)
        self.assertEqual(self.q1('SELECT status FROM quotations WHERE id=?', (qid,))['status'],
                         'SENT')

    def test_gui_khong_co_hang_muc_bi_chan(self):
        qid = self._bg_moi()
        r = self.post('/quotations/%d/send' % qid)
        self.assertIn('chưa có hạng mục', self.flash(r) or '')

    def test_duyet_bao_gia(self):
        qid = self._bg_moi()
        self.post('/quotations/%d/items' % qid, {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        self.post('/quotations/%d/send' % qid)
        r = self.post('/quotations/%d/review' % qid, {'quyet_dinh': 'APPROVED'})
        self.assertEqual(r.status_code, 303)
        bg = self.q1('SELECT * FROM quotations WHERE id=?', (qid,))
        self.assertEqual(bg['status'], 'APPROVED')
        self.assertIsNotNone(bg['approved_by'])
        self.assertIsNotNone(bg['approved_at'])

    def test_tu_choi_bao_gia(self):
        qid = self._bg_moi()
        self.post('/quotations/%d/items' % qid, {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        self.post('/quotations/%d/send' % qid)
        self.post('/quotations/%d/review' % qid, {'quyet_dinh': 'REJECTED'})
        self.assertEqual(self.q1('SELECT status FROM quotations WHERE id=?', (qid,))['status'],
                         'REJECTED')

    def test_sua_sau_khi_gui_bi_chan(self):
        qid = self._bg_moi()
        self.post('/quotations/%d/items' % qid, {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        self.post('/quotations/%d/send' % qid)
        r = self.post('/quotations/%d/items' % qid, {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        self.assertIn('bản nháp', self.flash(r) or '')

    def test_ap_dung_vao_phieu(self):
        # Phiếu 12 ở RECEIVED, chưa có hoá đơn.
        qid = self._bg_moi(phieu_id=12)
        self.post('/quotations/%d/items' % qid, {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        self.post('/quotations/%d/send' % qid)
        self.post('/quotations/%d/review' % qid, {'quyet_dinh': 'APPROVED'})
        truoc = len(self.q('SELECT id FROM repair_order_items WHERE repair_order_id=12'))
        r = self.post('/quotations/%d/apply' % qid)
        self.assertEqual(r.status_code, 303)
        self.assertIn('Đã áp dụng', self.flash(r) or '')
        self.assertEqual(
            len(self.q('SELECT id FROM repair_order_items WHERE repair_order_id=12')),
            truoc + 1)

    def test_khong_duyet_khi_chua_gui(self):
        qid = self._bg_moi()
        self.post('/quotations/%d/items' % qid, {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        r = self.post('/quotations/%d/review' % qid, {'quyet_dinh': 'APPROVED'})
        self.assertIn('DRAFT', self.flash(r) or '')

    def test_le_tan_khong_duyet(self):
        qid = self._bg_moi()
        self.post('/quotations/%d/items' % qid, {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        self.post('/quotations/%d/send' % qid)
        self.dang_nhap('le_tan')
        r = self.post('/quotations/%d/review' % qid, {'quyet_dinh': 'APPROVED'})
        self.assertEqual(r.status_code, 403)

    def test_thu_ngan_khong_quan_ly_bao_gia(self):
        self.dang_nhap('thu_ngan')
        r = self.client.get('/quotations')
        self.assertEqual(r.status_code, 403)

    def test_ky_thuat_vien_khong_quan_ly_bao_gia(self):
        self.dang_nhap('ky_thuat_vien')
        r = self.client.get('/quotations')
        self.assertEqual(r.status_code, 403)

    def test_chi_mot_bao_gia_duyet_cho_moi_phieu(self):
        # Báo giá 1 đã duyệt cho phiếu 10.
        qid1 = self._bg_moi(phieu_id=10)
        self.post('/quotations/%d/items' % qid1, {'loai': 'dich_vu', 'ma': '1', 'qty': '1'})
        self.post('/quotations/%d/send' % qid1)
        self.post('/quotations/%d/review' % qid1, {'quyet_dinh': 'APPROVED'})
        # Không tạo được báo giá thứ hai khi còn bản APPROVED.
        truoc = len(self.q('SELECT id FROM quotations'))
        self.post('/quotations/create', {'repair_order_id': '10'})
        self.assertEqual(len(self.q('SELECT id FROM quotations')), truoc)


# ===========================================================================
class TestKhoLedger(CoSoDichChung):
    """Sổ cái tồn kho: bất biến SUM(ledger) == stock, nhập, điều chỉnh."""

    def test_so_kho_khop_sau_seed(self):
        """Sau khi dựng CSDL mới, mọi phụ tùng phải khớp sổ cái."""
        lech = self.q('''
            SELECT * FROM (
              SELECT p.id, p.stock, COALESCE(SUM(t.qty), 0) AS tong
                FROM parts p LEFT JOIN stock_transactions t ON t.part_id = p.id
               GROUP BY p.id
            ) WHERE stock <> tong''')
        self.assertEqual(lech, [], 'sổ cái phải khớp tồn kho sau seed')

    def test_nhap_kho_tang_ton_va_ghi_so(self):
        self.dang_nhap('quan_ly')
        truoc = self.q1('SELECT stock FROM parts WHERE id = 1')['stock']
        r = self.post('/stock/receipt', {'part_id': '1', 'qty': '10',
                                         'note': 'Nhập lô mới'})
        self.assertEqual(r.status_code, 303)
        self.assertEqual(self.q1('SELECT stock FROM parts WHERE id = 1')['stock'],
                         truoc + 10)
        gd = self.q1('SELECT * FROM stock_transactions ORDER BY id DESC LIMIT 1')
        self.assertEqual(gd['qty'], 10)
        self.assertEqual(gd['reason'], 'RECEIPT')

    def test_nhap_kho_am_bi_chan(self):
        self.dang_nhap('quan_ly')
        r = self.post('/stock/receipt', {'part_id': '1', 'qty': '-5'})
        self.assertEqual(r.status_code, 303)
        msg = (self.flash(r) or '') + r.text
        self.assertTrue('greater than 0' in msg or 'lớn hơn 0' in msg,
                        'phải báo số lượng nhập phải > 0, got: %r' % msg)

    def test_them_hang_muc_ghi_ledger_usage(self):
        self.dang_nhap('ky_thuat_vien')
        truoc = self.q1('SELECT stock FROM parts WHERE id = 2')['stock']
        self.post('/repair-orders/12/items',
                  {'loai': 'phu_tung', 'ma': '2', 'qty': '3'})
        self.assertEqual(self.q1('SELECT stock FROM parts WHERE id = 2')['stock'],
                         truoc - 3)
        gd = self.q1('SELECT * FROM stock_transactions ORDER BY id DESC LIMIT 1')
        self.assertEqual(gd['qty'], -3)
        self.assertEqual(gd['reason'], 'USAGE')
        self.assertEqual(gd['repair_order_id'], 12)

    def test_huy_phieu_ghi_ledger_return(self):
        self.dang_nhap('ky_thuat_vien')
        truoc = self.q1('SELECT stock FROM parts WHERE id = 2')['stock']
        self.post('/repair-orders/12/items',
                  {'loai': 'phu_tung', 'ma': '2', 'qty': '4'})
        self.post('/repair-orders/12/status', {'status': 'CANCELLED'})
        self.assertEqual(self.q1('SELECT stock FROM parts WHERE id = 2')['stock'],
                         truoc)
        gd = self.q1("SELECT * FROM stock_transactions WHERE reason='RETURN'"
                     ' ORDER BY id DESC LIMIT 1')
        self.assertEqual(gd['qty'], 4)
        self.assertEqual(gd['repair_order_id'], 12)

    def test_dieu_chinh_ton_kho(self):
        self.dang_nhap('quan_ly')
        self.post('/stock/adjust', {'part_id': '3', 'moi': '50',
                                    'note': 'Kiểm kê'})
        self.assertEqual(self.q1('SELECT stock FROM parts WHERE id = 3')['stock'], 50)
        gd = self.q1("SELECT * FROM stock_transactions WHERE reason='ADJUSTMENT'"
                     ' ORDER BY id DESC LIMIT 1')
        # stock ban đầu của part 3 là 70 → delta = -20
        self.assertEqual(gd['qty'], -20)

    def test_dieu_chinh_khong_lech_so(self):
        """Sau mọi thao tác, SUM(ledger) vẫn == stock."""
        self.dang_nhap('quan_ly')
        self.post('/stock/receipt', {'part_id': '1', 'qty': '5'})
        self.post('/stock/adjust', {'part_id': '1', 'moi': '100'})
        self.dang_nhap('ky_thuat_vien')
        self.post('/repair-orders/12/items',
                  {'loai': 'phu_tung', 'ma': '1', 'qty': '2'})
        lech = self.q('''
            SELECT * FROM (
              SELECT p.id, p.stock, COALESCE(SUM(t.qty), 0) AS tong
                FROM parts p LEFT JOIN stock_transactions t ON t.part_id = p.id
               GROUP BY p.id
            ) WHERE stock <> tong''')
        self.assertEqual(lech, [], 'sổ cái phải khớp sau mọi thao tác')

    def test_le_tan_nhap_kho_duoc(self):
        self.dang_nhap('le_tan')
        r = self.post('/stock/receipt', {'part_id': '1', 'qty': '1'})
        self.assertEqual(r.status_code, 303)

    def test_thu_ngan_nhap_kho_bi_chan(self):
        self.dang_nhap('thu_ngan')
        r = self.post('/stock/receipt', {'part_id': '1', 'qty': '1'})
        self.assertEqual(r.status_code, 403)

    def test_ky_thuat_vien_nhap_kho_bi_chan(self):
        self.dang_nhap('ky_thuat_vien')
        r = self.post('/stock/receipt', {'part_id': '1', 'qty': '1'})
        self.assertEqual(r.status_code, 403)

    def test_chua_dang_nhap_kho_303(self):
        self.client.cookies.clear()
        r = self.client.get('/stock')
        self.assertEqual(r.status_code, 303)
        self.assertIn('/accounts/login', r.headers.get('location', ''))


# ===========================================================================
class TestBaoHanh(CoSoDichChung):
    """Bảo hành: XOR SERVICE/PART, chỉ phiếu COMPLETED, chặn trùng."""

    def _bh_moi(self, oid=1, service_id='1', part_id='', months='6',
                start='2026-02-15'):
        """Phiếu 1 (COMPLETED) có dịch vụ 1 (đã EXPIRED → tạo lại được)
        và phụ tùng 1 (chưa có bảo hành)."""
        self.post('/warranties/create', {
            'repair_order_id': str(oid), 'service_id': service_id,
            'part_id': part_id, 'months': months, 'start_date': start})
        bh = self.q1('SELECT id FROM warranties ORDER BY id DESC LIMIT 1')
        return bh['id'] if bh else None

    def test_tao_bao_hanh_dich_vu(self):
        wid = self._bh_moi()
        self.assertIsNotNone(wid)
        bh = self.q1('SELECT * FROM warranties WHERE id = ?', (wid,))
        self.assertEqual(bh['scope'], 'SERVICE')
        self.assertEqual(bh['status'], 'ACTIVE')
        self.assertEqual(bh['start_date'], '2026-02-15')
        self.assertEqual(bh['end_date'], '2026-08-15')  # +6 tháng

    def test_tao_bao_hanh_phu_tung(self):
        # Phiếu 1 có phụ tùng 1 (P1 dầu động cơ), chưa có bảo hành.
        wid = self._bh_moi(service_id='', part_id='1', months='12',
                           start='2026-02-15')
        bh = self.q1('SELECT * FROM warranties WHERE id = ?', (wid,))
        self.assertEqual(bh['scope'], 'PART')
        self.assertEqual(bh['part_id'], 1)
        self.assertIsNone(bh['service_id'])
        self.assertEqual(bh['end_date'], '2027-02-15')

    def test_xor_chon_ca_hai_bi_chan(self):
        truoc = len(self.q('SELECT id FROM warranties'))
        self.post('/warranties/create', {
            'repair_order_id': '1', 'service_id': '1', 'part_id': '1',
            'months': '6', 'start_date': '2026-02-15'})
        self.assertEqual(len(self.q('SELECT id FROM warranties')), truoc)

    def test_xor_chon_mot_cung_bi_chan(self):
        truoc = len(self.q('SELECT id FROM warranties'))
        self.post('/warranties/create', {
            'repair_order_id': '1', 'service_id': '', 'part_id': '',
            'months': '6', 'start_date': '2026-02-15'})
        self.assertEqual(len(self.q('SELECT id FROM warranties')), truoc)

    def test_khong_phai_hoan_thanh_bi_chan(self):
        # Phiếu 10 ở REPAIRING.
        truoc = len(self.q('SELECT id FROM warranties'))
        self.post('/warranties/create', {
            'repair_order_id': '10', 'service_id': '7',
            'months': '6', 'start_date': '2026-11-14'})
        self.assertEqual(len(self.q('SELECT id FROM warranties')), truoc)

    def test_hang_muc_khong_thuoc_phieu_bi_chan(self):
        # Phiếu 1 không có dịch vụ 8.
        truoc = len(self.q('SELECT id FROM warranties'))
        self.post('/warranties/create', {
            'repair_order_id': '1', 'service_id': '8',
            'months': '6', 'start_date': '2026-02-15'})
        self.assertEqual(len(self.q('SELECT id FROM warranties')), truoc)

    def test_trung_bao_hanh_active_bi_chan(self):
        # Seed: phiếu 2 có PARTACTIVE cho phụ tùng 5. Tạo thêm phải bị chặn.
        truoc = len(self.q('SELECT id FROM warranties'))
        self.post('/warranties/create', {
            'repair_order_id': '2', 'part_id': '5',
            'months': '3', 'start_date': '2026-04-04'})
        self.assertEqual(len(self.q('SELECT id FROM warranties')), truoc)

    def test_huy_bao_hanh(self):
        wid = self._bh_moi()
        r = self.post('/warranties/%d/cancel' % wid, {'note': 'Khách khiếu nại'})
        self.assertEqual(r.status_code, 303)
        self.assertEqual(self.q1('SELECT status FROM warranties WHERE id=?',
                                 (wid,))['status'], 'CANCELLED')

    def test_huy_bao_hanh_da_huy_bi_chan(self):
        wid = self._bh_moi()
        self.post('/warranties/%d/cancel' % wid, {})
        trang_thai = self.q1('SELECT status FROM warranties WHERE id=?',
                             (wid,))['status']
        self.assertEqual(trang_thai, 'CANCELLED')
        # Huỷ lần hai: backend phải từ chối, không đổi trạng thái gì thêm.
        r = self.post('/warranties/%d/cancel' % wid, {})
        self.assertEqual(r.status_code, 303)
        self.assertEqual(self.q1('SELECT status FROM warranties WHERE id=?',
                                 (wid,))['status'], 'CANCELLED')

    def test_sau_khi_huy_tao_lai_duoc(self):
        # Tạo bảo hành cho dịch vụ 1 (EXPIRED từ seed → ACTIVE mới OK).
        wid = self._bh_moi()
        self.assertIsNotNone(wid)
        self.post('/warranties/%d/cancel' % wid, {})
        # Sau khi huỷ ACTIVE, tạo lại được cho cùng hạng mục.
        wid2 = self._bh_moi()
        self.assertIsNotNone(wid2)
        self.assertNotEqual(wid, wid2)

    def test_le_tan_duoc_lap_bao_hanh(self):
        self.dang_nhap('le_tan')
        wid = self._bh_moi()
        self.assertIsNotNone(wid)

    def test_thu_ngan_khong_lap_bao_hanh(self):
        self.dang_nhap('thu_ngan')
        r = self.client.get('/warranties')
        self.assertEqual(r.status_code, 403)

    def test_ky_thuat_vien_khong_lap_bao_hanh(self):
        self.dang_nhap('ky_thuat_vien')
        r = self.client.get('/warranties')
        self.assertEqual(r.status_code, 403)

    def test_chua_dang_nhap_303(self):
        self.client.cookies.clear()
        r = self.client.get('/warranties')
        self.assertEqual(r.status_code, 303)
        self.assertIn('/accounts/login', r.headers.get('location', ''))

    def test_tinh_end_date_cuoi_thang(self):
        # 31/01 + 1 tháng = 28/02 (năm 2027 không nhuận).
        wid = self._bh_moi(oid=9, service_id='4', months='1',
                           start='2027-01-31')
        bh = self.q1('SELECT * FROM warranties WHERE id = ?', (wid,))
        self.assertEqual(bh['end_date'], '2027-02-28')


# ===========================================================================
class TestAiGateway(unittest.TestCase):
    """Kiểm thử lớp trung gian gọi AI (ai_gateway) — mock httpx, không cần
    khóa API thật."""

    def setUp(self):
        from app.core.config import get_settings
        s = get_settings()
        self._cu = (s.AI_PROVIDER, s.AI_API_KEY, s.AI_BASE_URL, s.AI_MODEL,
                    s.AI_TIMEOUT, s.OPENAI_API_KEY, s.OPENAI_MODEL,
                    s.OPENAI_BASE_URL)
        s.AI_PROVIDER = 'openai'
        s.AI_API_KEY = 'sk-test-khong-that'
        s.AI_BASE_URL = 'https://api.openai.com/v1/chat/completions'
        s.AI_MODEL = 'gpt-4o-mini'
        s.OPENAI_API_KEY = s.AI_API_KEY
        s.OPENAI_MODEL = s.AI_MODEL
        s.OPENAI_BASE_URL = s.AI_BASE_URL
        s.AI_TIMEOUT = 5

    def tearDown(self):
        from app.core.config import get_settings
        s = get_settings()
        (s.AI_PROVIDER, s.AI_API_KEY, s.AI_BASE_URL, s.AI_MODEL, s.AI_TIMEOUT,
         s.OPENAI_API_KEY, s.OPENAI_MODEL, s.OPENAI_BASE_URL) = self._cu

    def test_goimock_khong_goi_mang(self):
        """Chế độ mock: goi() trả None, không lỗi."""
        from app import ai_gateway
        from app.core.config import get_settings
        get_settings().AI_PROVIDER = 'mock'
        try:
            self.assertIsNone(ai_gateway.goi('sys', 'user'))
        finally:
            get_settings().AI_PROVIDER = 'openai'

    def test_base_url_cu_full_path_khong_nhan_doi(self):
        """AI_BASE_URL đã chứa /chat/completions thì không nối thêm."""
        from app import ai_gateway

        class FakeResp:
            status_code = 200
            def json(self):
                return {'choices': [{'message': {'content': 'xin chào'}}]}

        goi_den = []
        class FakeHttpx:
            @staticmethod
            def post(url, **kw):
                goi_den.append(url)
                return FakeResp()
            class TimeoutException(Exception):
                pass

        import sys
        sys.modules['httpx'] = FakeHttpx
        try:
            out = ai_gateway.goi('sys', 'user', cho_phep_mock=False)
        finally:
            del sys.modules['httpx']
        self.assertEqual(out, 'xin chào')
        self.assertEqual(goi_den, ['https://api.openai.com/v1/chat/completions'])

    def test_base_url_v1_duoc_noi_chat_completions(self):
        """AI_BASE_URL dạng /v1 thì tự nối /chat/completions."""
        from app.core.config import get_settings
        get_settings().AI_BASE_URL = 'https://api.openai.com/v1'
        from app import ai_gateway

        class FakeResp:
            status_code = 200
            def json(self):
                return {'choices': [{'message': {'content': 'ok'}}]}

        goi_den = []
        class FakeHttpx:
            @staticmethod
            def post(url, **kw):
                goi_den.append(url)
                return FakeResp()
            class TimeoutException(Exception):
                pass

        import sys
        sys.modules['httpx'] = FakeHttpx
        try:
            out = ai_gateway.goi('sys', 'user', cho_phep_mock=False)
        finally:
            del sys.modules['httpx']
        self.assertEqual(out, 'ok')
        self.assertEqual(goi_den, ['https://api.openai.com/v1/chat/completions'])

    def test_429_va_500_bi_chuyen_sang_mock(self):
        """Lỗi nhà cung cấp (429, 500, timeout, phản hồi sai định dạng):
        nếu cho_phep_mock thì trả None, không ném; tắt mock thì ném AiError."""
        from app import ai_gateway
        import sys

        class FakeTimeout(Exception):
            pass

        che_do = {'kieu': '429'}

        class FakeResp:
            def __init__(self, code, data):
                self.status_code = code
                self._data = data
            def json(self):
                return self._data

        class FakeHttpx:
            TimeoutException = FakeTimeout
            @staticmethod
            def post(url, **kw):
                k = che_do['kieu']
                if k == 'timeout':
                    raise FakeTimeout('quá hạn')
                if k == '429':
                    return FakeResp(429, {})
                if k == '500':
                    return FakeResp(500, {})
                if k == 'sai_dinh_dang':
                    return FakeResp(200, {'khong_co_choices': []})
                return FakeResp(200, {'choices': [{'message': {'content': ''}}]})

        sys.modules['httpx'] = FakeHttpx
        try:
            for k in ('429', '500', 'timeout', 'sai_dinh_dang'):
                che_do['kieu'] = k
                self.assertIsNone(
                    ai_gateway.goi('sys', 'user', cho_phep_mock=True), k)
                self.assertRaises(
                    ai_gateway.AiError, ai_gateway.goi,
                    'sys', 'user', cho_phep_mock=False)
        finally:
            del sys.modules['httpx']

    def test_thieu_api_key_khong_goimock(self):
        """Thiếu khóa API: _goi_openai ném AiError ngay (trước khi gọi mạng)."""
        from app.core.config import get_settings
        from app import ai_gateway
        get_settings().AI_API_KEY = ''
        get_settings().OPENAI_API_KEY = ''
        self.assertRaises(ai_gateway.AiError, ai_gateway._goi_openai, 's', 'u')

    def test_preset_groq_openrouter_gemini(self):
        """Preset free-tier phải trỏ đúng base URL + model."""
        from app.core.config import AI_PROVIDERS
        self.assertEqual(AI_PROVIDERS['groq']['base'],
                         'https://api.groq.com/openai/v1')
        self.assertIn('gpt-oss', AI_PROVIDERS['groq']['model'])
        self.assertEqual(AI_PROVIDERS['openrouter']['base'],
                         'https://openrouter.ai/api/v1')
        self.assertIn(':free', AI_PROVIDERS['openrouter']['model'])
        self.assertEqual(AI_PROVIDERS['gemini']['base'],
                         'https://generativelanguage.googleapis.com/v1beta/openai/')
        self.assertIn('gemini', AI_PROVIDERS['gemini']['model'])
        for p in ('groq', 'openrouter', 'gemini'):
            self.assertTrue(AI_PROVIDERS[p]['free'], p)
            self.assertTrue(AI_PROVIDERS[p]['key_env'], p)

    def test_preset_9router(self):
        from app.core.config import AI_PROVIDERS, Settings
        p = AI_PROVIDERS['9router']
        self.assertEqual(p['base'], 'http://localhost:20128/v1')
        self.assertTrue(p['free'])
        # 9router local: không key vẫn giữ provider (không hạ mock).
        s = Settings({'AI_PROVIDER': '9router', 'APP_ENV': 'development'})
        self.assertEqual(s.AI_PROVIDER, '9router')
        self.assertEqual(s.AI_BASE_URL, 'http://localhost:20128/v1')
        self.assertEqual(s.AI_MODEL, 'my9model-free')

    def test_9router_khong_gui_authorization_khi_thieu_key(self):
        from app.core.config import get_settings
        from app import ai_gateway
        s = get_settings()
        s.AI_PROVIDER = '9router'
        s.AI_BASE_URL = 'http://localhost:20128/v1'
        s.AI_MODEL = 'my9model-free'
        s.AI_API_KEY = ''
        s.OPENAI_API_KEY = ''

        class FakeResp:
            status_code = 200
            def json(self):
                return {'choices': [{'message': {'content': '9r-ok'}}]}

        hdrs = {}
        class FakeHttpx:
            @staticmethod
            def post(url, **kw):
                hdrs.update(kw.get('headers') or {})
                return FakeResp()
            class TimeoutException(Exception):
                pass

        import sys
        sys.modules['httpx'] = FakeHttpx
        try:
            out = ai_gateway.goi('sys', 'user', cho_phep_mock=False)
        finally:
            del sys.modules['httpx']
            s.AI_PROVIDER = 'openai'
        self.assertEqual(out, '9r-ok')
        self.assertNotIn('Authorization', hdrs)

    def test_goi_den_dung_url_groq(self):
        """Provider groq phải gọi đúng endpoint groq."""
        from app.core.config import get_settings
        from app import ai_gateway
        s = get_settings()
        s.AI_PROVIDER = 'groq'
        s.AI_BASE_URL = 'https://api.groq.com/openai/v1'
        s.AI_MODEL = 'llama-3.3-70b-versatile'

        class FakeResp:
            status_code = 200
            def json(self):
                return {'choices': [{'message': {'content': 'groq-ok'}}]}

        goi_den = []
        class FakeHttpx:
            @staticmethod
            def post(url, **kw):
                goi_den.append(url)
                return FakeResp()
            class TimeoutException(Exception):
                pass

        import sys
        sys.modules['httpx'] = FakeHttpx
        try:
            out = ai_gateway.goi('sys', 'user', cho_phep_mock=False)
        finally:
            del sys.modules['httpx']
            s.AI_PROVIDER = 'openai'
            s.AI_BASE_URL = 'https://api.openai.com/v1/chat/completions'
        self.assertEqual(out, 'groq-ok')
        self.assertEqual(goi_den,
                         ['https://api.groq.com/openai/v1/chat/completions'])

    def test_openrouter_gui_header_dac_biet(self):
        """OpenRouter cần HTTP-Referer + X-Title."""
        from app.core.config import get_settings
        from app import ai_gateway
        s = get_settings()
        s.AI_PROVIDER = 'openrouter'
        s.AI_BASE_URL = 'https://openrouter.ai/api/v1'
        s.AI_MODEL = 'meta-llama/llama-3.3-70b-instruct:free'

        class FakeResp:
            status_code = 200
            def json(self):
                return {'choices': [{'message': {'content': 'or-ok'}}]}

        hdrs = {}
        class FakeHttpx:
            @staticmethod
            def post(url, **kw):
                hdrs.update(kw.get('headers') or {})
                return FakeResp()
            class TimeoutException(Exception):
                pass

        import sys
        sys.modules['httpx'] = FakeHttpx
        try:
            out = ai_gateway.goi('sys', 'user', cho_phep_mock=False)
        finally:
            del sys.modules['httpx']
            s.AI_PROVIDER = 'openai'
        self.assertEqual(out, 'or-ok')
        self.assertIn('HTTP-Referer', hdrs)
        self.assertIn('X-Title', hdrs)
        self.assertTrue(hdrs['Authorization'].startswith('Bearer '))

    def test_ai_provider_khong_hop_le_bi_chan(self):
        from app.core.config import Settings
        self.assertRaises(ValueError, Settings, {'AI_PROVIDER': 'chatgpt'})

    def test_dev_thieu_khoa_tu_ha_ve_mock(self):
        from app.core.config import Settings
        s = Settings({'AI_PROVIDER': 'groq', 'APP_ENV': 'development'})
        self.assertEqual(s.AI_PROVIDER, 'mock')

    def test_phan_tich_json_boc_khoi(self):
        from app import ai_gateway
        self.assertEqual(ai_gateway._phan_tich_json('```json\n{"a":1}\n```'), {'a': 1})
        self.assertEqual(ai_gateway._phan_tich_json('nói gì đó {"a": 2} hết'), {'a': 2})
        self.assertIsNone(ai_gateway._phan_tich_json(''))

    def test_so_nguyen_chiu_duoc_chuoi(self):
        from app import ai_gateway
        self.assertEqual(ai_gateway._so_nguyen('1.500.000'), 1500000)
        self.assertEqual(ai_gateway._so_nguyen(42), 42)
        self.assertIsNone(ai_gateway._so_nguyen(True))   # bool là không tin
        self.assertIsNone(ai_gateway._so_nguyen('abc'))

    def test_cat_ngu_dung_vuot_gioi_han(self):
        from app.core.config import get_settings
        from app import ai_gateway
        get_settings().AI_MAX_CONTEXT = 500
        try:
            self.assertTrue(len(ai_gateway._cat_ngoi_dung('x' * 600)) < 600)
        finally:
            get_settings().AI_MAX_CONTEXT = 6000


if __name__ == '__main__':
    unittest.main(verbosity=2)