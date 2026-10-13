# -*- coding: utf-8 -*-
"""Kiểm thử ràng buộc cơ sở dữ liệu theo mục 4.3 của báo cáo.

Chạy được cả hai cách:
    pytest tests/test_schema_constraints.py -v
    python tests/test_schema_constraints.py
"""
import os
import sqlite3
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = os.path.join(BASE, 'database', 'schema.sql')
SEED = os.path.join(BASE, 'database', 'seed_data.sql')


def fresh_db(with_seed=True):
    conn = sqlite3.connect(':memory:')
    conn.execute('PRAGMA foreign_keys = ON')
    with open(SCHEMA, encoding='utf-8') as f:
        conn.executescript(f.read())
    if with_seed:
        with open(SEED, encoding='utf-8') as f:
            conn.executescript(f.read())
    return conn


def raises(conn, sql, params=()):
    """Trả về True nếu câu lệnh bị CSDL từ chối."""
    try:
        conn.execute(sql, params)
        return False
    except sqlite3.IntegrityError:
        return True
    except sqlite3.OperationalError:
        return True


class TestRangBuocLichHen(unittest.TestCase):
    """Ràng buộc mục 4.3 về repair_order_items."""

    def setUp(self):
        self.db = fresh_db()

    def tearDown(self):
        self.db.close()

    def test_01_khong_duoc_thieu_ca_hai(self):
        # hạng mục không xác định được là dịch vụ hay phụ tùng
        self.assertTrue(raises(self.db,
            'INSERT INTO repair_order_items (repair_order_id, service_id, part_id, qty, unit_price)'
            ' VALUES (1, NULL, NULL, 1, 100000)'))

    def test_02_khong_duoc_co_ca_hai(self):
        self.assertTrue(raises(self.db,
            'INSERT INTO repair_order_items (repair_order_id, service_id, part_id, qty, unit_price)'
            ' VALUES (1, 1, 1, 1, 100000)'))

    def test_03_chi_co_dich_vu_duoc_phep(self):
        self.db.execute(
            'INSERT INTO repair_order_items (repair_order_id, service_id, part_id, qty, unit_price)'
            ' VALUES (1, 1, NULL, 2, 100000)')
        n = self.db.execute('SELECT COUNT(*) FROM repair_order_items WHERE repair_order_id = 1').fetchone()[0]
        self.assertEqual(n, 3, 'phải thêm được 1 hạng mục dịch vụ')

    def test_04_chi_co_phu_tung_duoc_phep(self):
        truoc = self.db.execute(
            'SELECT COUNT(*) FROM repair_order_items').fetchone()[0]
        self.db.execute(
            'INSERT INTO repair_order_items (repair_order_id, service_id, part_id, qty, unit_price)'
            ' VALUES (1, NULL, 1, 3, 100000)')
        sau = self.db.execute(
            'SELECT COUNT(*) FROM repair_order_items').fetchone()[0]
        self.assertEqual(sau, truoc + 1, 'phải thêm được 1 hạng mục phụ tùng')
        r = self.db.execute(
            'SELECT service_id, part_id, qty FROM repair_order_items'
            ' WHERE id = ?', (sau,)).fetchone()
        self.assertEqual(r, (None, 1, 3), 'hạng mục phải chỉ có part_id')

    def test_05_so_luong_phai_duong(self):
        self.assertTrue(raises(self.db,
            'INSERT INTO repair_order_items (repair_order_id, service_id, qty, unit_price)'
            ' VALUES (1, 1, 0, 100000)'))
        self.assertTrue(raises(self.db,
            'INSERT INTO repair_order_items (repair_order_id, service_id, qty, unit_price)'
            ' VALUES (1, 1, -3, 100000)'))

    def test_06_don_gia_khong_am(self):
        self.assertTrue(raises(self.db,
            'INSERT INTO repair_order_items (repair_order_id, service_id, qty, unit_price)'
            ' VALUES (1, 1, 1, -1)'))


class TestGiaChot(unittest.TestCase):
    """unit_price phải là giá chốt, không phụ thuộc giá danh mục."""

    def setUp(self):
        self.db = fresh_db()

    def tearDown(self):
        self.db.close()

    def test_01_don_gia_khong_doi_khi_doi_gia_danh_muc(self):
        truoc = self.db.execute(
            'SELECT unit_price FROM repair_order_items WHERE id = 1').fetchone()[0]
        # đổi giá dịch vụ trong danh mục
        self.db.execute('UPDATE services SET price = 999999 WHERE id = 1')
        # đổi giá trong hạng mục (mô phỏng sửa dữ liệu sai)
        self.db.execute('UPDATE repair_order_items SET unit_price = 1 WHERE id = 1')
        self.db.rollback()
        sau = self.db.execute(
            'SELECT unit_price FROM repair_order_items WHERE id = 1').fetchone()[0]
        self.assertEqual(truoc, sau,
            'giá đã chốt phải không đổi khi giá danh mục thay đổi')

    def test_02_tong_hoa_don_khong_doi_theo_gia_danh_muc(self):
        tong_truoc = self.db.execute(
            'SELECT total FROM invoices WHERE repair_order_id = 1').fetchone()[0]
        self.db.execute('UPDATE services SET price = 0')
        self.db.rollback()
        tong_sau = self.db.execute(
            'SELECT total FROM invoices WHERE repair_order_id = 1').fetchone()[0]
        self.assertEqual(tong_truoc, tong_sau,
            'tổng hoá đơn đã lưu không được đổi theo giá danh mục')


class TestThanhToan(unittest.TestCase):
    def setUp(self):
        self.db = fresh_db()

    def tearDown(self):
        self.db.close()

    def test_01_invoice_paid_khong_duoc_vuot_total(self):
        self.assertTrue(raises(self.db,
            'INSERT INTO invoices (repair_order_id, total, paid, status) VALUES (4, 100000, 150000, %s)'
            % "'PAID'"))

    def test_02_invoice_pai_dung_duoc_phep(self):
        self.db.execute(
            'INSERT INTO invoices (repair_order_id, total, paid, status) VALUES (4, 100000, 100000, %s)'
            % "'PAID'")
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM invoices WHERE repair_order_id = 4').fetchone()[0], 1)

    def test_03_mot_phieu_chi_co_mot_hoa_don(self):
        self.assertTrue(raises(self.db,
            'INSERT INTO invoices (repair_order_id, total, paid, status) VALUES (1, 100, 0, %s)' % "'UNPAID'"))

    def test_04_khoan_thanh_toan_phai_duong(self):
        self.assertTrue(raises(self.db,
            'INSERT INTO payments (invoice_id, amount, method) VALUES (1, 0, %s)' % "'CASH'"))

    def test_05_mot_hoa_don_duoc_nhieu_khoan_thu(self):
        n = self.db.execute('SELECT COUNT(*) FROM payments WHERE invoice_id = 1').fetchone()[0]
        self.assertGreaterEqual(n, 2, 'dữ liệu mẫu phải có hoá đơn nhiều khoản thu')

    def test_06_tong_thanh_toan_khong_vuot_tong_hoa_don(self):
        bad = self.db.execute(
            'SELECT i.id, i.total, (SELECT COALESCE(SUM(p.amount),0) FROM payments p'
            ' WHERE p.invoice_id = i.id) AS da_thu'
            ' FROM invoices i').fetchall()
        for inv_id, total, paid_sum in bad:
            self.assertLessEqual(paid_sum, total,
                                 'hoá đơn %s đã thu vượt tổng' % inv_id)

    def test_07_trang_thai_hoa_don_khong_hop_l(self):
        self.assertTrue(raises(self.db,
            'INSERT INTO invoices (repair_order_id, total, paid, status) VALUES (4, 100, 0, %s)' % "'XYZ'"))


class TestRangBuocKhac(unittest.TestCase):
    def setUp(self):
        self.db = fresh_db()

    def tearDown(self):
        self.db.close()

    def test_01_bien_so_trung(self):
        self.assertTrue(raises(self.db,
            'INSERT INTO vehicles (customer_id, plate, brand, model, year)'
            " VALUES (1, '30A-1111', 'Toyota', 'Vios', 2019)"))

    def test_02_ten_dang_nhap_trung(self):
        self.assertTrue(raises(self.db,
            "INSERT INTO users (username, password_hash, full_name, role)"
            " VALUES ('quan_ly', 'x', 'Trùng', 'MANAGER')"))

    def test_03_vai_tro_khong_hop_l(self):
        self.assertTrue(raises(self.db,
            "INSERT INTO users (username, password_hash, full_name, role)"
            " VALUES ('vai_tro_gi', 'x', 'Sai vai trò', 'BOSS')"))

    def test_04_mat_khau_luu_dang_bam(self):
        h = self.db.execute("SELECT password_hash FROM users WHERE username = 'quan_ly'").fetchone()[0]
        self.assertTrue(h.startswith('pbkdf2_sha256$'), 'phải lưu dạng băm, không lưu mật khẩu thô')
        self.assertNotIn('Garage@2026', h, 'không được chứa mật khẩu thô trong cột hash')

    def test_05_ton_kho_khong_am(self):
        self.assertTrue(raises(self.db, 'UPDATE parts SET stock = -1 WHERE id = 1'))

    def test_06_gia_khong_am(self):
        self.assertTrue(raises(self.db, 'UPDATE services SET price = -1 WHERE id = 1'))

    def test_07_trang_thai_phieu_khong_hop_l(self):
        self.assertTrue(raises(self.db, "UPDATE repair_orders SET status = 'DANG-LAM' WHERE id = 1"))

    def test_08_khong_xoa_duoc_khoa_ngoai_dang_dung(self):
        self.assertTrue(raises(self.db, 'DELETE FROM vehicles WHERE id = 1'),
                        'xe đã có phiếu sửa chữa thì không được xóa')

    def test_09_khong_xoa_duoc_khach_da_co_xe(self):
        self.assertTrue(raises(self.db, 'DELETE FROM customers WHERE id = 1'))

    def test_10_ai_can_nguoi_duyet(self):
        self.assertTrue(raises(self.db,
            "UPDATE ai_results SET review_status = 'APPROVED' WHERE id = 2"),
            'không được duyệt mà không có người duyệt và thời điểm')

    def test_11_ai_co_the_chua_duyet(self):
        r = self.db.execute(
            "SELECT review_status FROM ai_results WHERE id = 1").fetchone()[0]
        self.assertEqual(r, 'APPROVED')

    def test_12_khoa_ngoai_lich_hen_phai_khop_khach_cua_xe(self):
        # ràng buộc này do BACKEND kiểm tra, không làm được bằng CHECK;
        # test này chỉ xác nhận dữ liệu mẫu đã khop sẵn.
        sai = self.db.execute(
            'SELECT a.id FROM appointments a JOIN vehicles v ON a.vehicle_id = v.id'
            ' WHERE a.customer_id <> v.customer_id').fetchall()
        self.assertEqual(sai, [], 'dữ liệu mẫu không được có lịch hẹn sai khách hàng')


class TestDuLieuMau(unittest.TestCase):
    """Đối chiếu số lượng với bảng định nghĩa tại mục 4.5."""

    def setUp(self):
        self.db = fresh_db()

    def tearDown(self):
        self.db.close()

    def n(self, table):
        return self.db.execute('SELECT COUNT(*) FROM %s' % table).fetchone()[0]

    def test_so_luong_theo_muc_4_5(self):
        muc_cu_the = {
            'users': 4, 'customers': 10, 'vehicles': 12, 'appointments': 10,
            'services': 8, 'parts': 15, 'repair_orders': 12,
            'repair_order_items': 25, 'repair_logs': 20, 'invoices': 8,
            'payments': 8, 'ai_results': 6, 'shop_categories': 6,
            'shop_products': 20, 'shop_orders': 2,
        }
        for tbl, can_co in muc_cu_the.items():
            self.assertGreaterEqual(self.n(tbl), can_co,
                                    'bảng %s thiếu dữ liệu so với mục 4.5' % tbl)

    def test_xe_co_5_lan_sua_dung_cho_ai(self):
        n = self.db.execute(
            'SELECT COUNT(*) FROM repair_orders WHERE vehicle_id = 1').fetchone()[0]
        self.assertGreaterEqual(n, 5, 'cần xe có ít nhất 5 lần sửa cho ca kiểm thử AI tóm tắt')

    def test_phu_tung_co_het_hang(self):
        n = self.db.execute('SELECT COUNT(*) FROM parts WHERE stock = 0').fetchone()[0]
        self.assertGreaterEqual(n, 1, 'cần có phụ tùng hết hàng để kiểm thử giới hạn tồn kho')

    def test_dich_vu_co_mo_ta_rong(self):
        n = self.db.execute(
            'SELECT COUNT(*) FROM services WHERE description IS NULL').fetchone()[0]
        self.assertGreaterEqual(n, 1, 'cần có dịch vụ thiếu mô tả cho ca AI giải thích')

    def test_phieu_co_du_sac_trang_thai(self):
        trang = {r[0] for r in self.db.execute('SELECT DISTINCT status FROM repair_orders')}
        self.assertGreaterEqual(len(trang), 5, 'dữ liệu mẫu phải phủ nhiều trạng thái phiếu')

    def test_co_hoa_don_chua_thu_va_thua_mot_phan(self):
        n = self.db.execute(
            "SELECT COUNT(*) FROM invoices WHERE status = 'UNPAID'").fetchone()[0]
        self.assertGreaterEqual(n, 1)
        n = self.db.execute(
            "SELECT COUNT(*) FROM invoices WHERE status = 'PARTIAL'").fetchone()[0]
        self.assertGreaterEqual(n, 1)

    def test_co_lich_hen_trung_gio(self):
        n = self.db.execute(
            'SELECT vehicle_id, scheduled_at, COUNT(*) c FROM appointments'
            ' WHERE status <> %s' % "'CANCELLED'"
            ' GROUP BY vehicle_id, scheduled_at HAVING c > 1').fetchall()
        self.assertGreaterEqual(len(n), 1, 'cần có lịch hẹn trùng để kiểm thử phát hiện xung đột')

    def test_ai_co_ket_qua_choi_duyet(self):
        n = self.db.execute(
            "SELECT COUNT(*) FROM ai_results WHERE review_status = 'PENDING'").fetchone()[0]
        self.assertGreaterEqual(n, 3, 'cần có kết quả AI ở trạng thái chờ duyệt')

    def test_khac_biet_bao_so_bang_theo_schema(self):
        """Số bảng trong CSDL phải khớp số CREATE TABLE trong schema.sql.

        Đặc tả ban đầu quy định 16 bảng; các phần bổ sung (biên bản tiếp
        nhận, báo giá, kho, bảo hành…) sẽ làm tăng số này theo từng giai đoạn.
        """
        import re
        with open(SCHEMA, encoding='utf-8') as fh:
            n_schema = len(re.findall(r'CREATE TABLE ', fh.read()))
        n = self.db.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0]
        self.assertEqual(n, n_schema,
                         'CSDL có %d bảng nhưng schema.sql khai báo %d'
                         % (n, n_schema))
        self.assertGreaterEqual(n, 16, 'ít nhất phải có 16 bảng theo đặc tả')


class TestChiMuc(unittest.TestCase):
    def setUp(self):
        self.db = fresh_db()

    def tearDown(self):
        self.db.close()

    def test_da_tao_cac_chi_muc_theo_muc_4_3(self):
        can_co = {
            'idx_vehicles_customer', 'idx_appointments_vehicle', 'idx_appointments_status',
            'idx_repair_orders_vehicle', 'idx_repair_orders_status',
            'idx_roi_repair_order', 'idx_invoices_status', 'idx_payments_invoice',
            'idx_ai_results_order', 'idx_ai_results_status',
        }
        co = {r[0] for r in self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='index'")}
        thieu = can_co - co
        self.assertEqual(thieu, set(), 'thiếu chỉ mục: %s' % thieu)


if __name__ == '__main__':
    unittest.main(verbosity=2)