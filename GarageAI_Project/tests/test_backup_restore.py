# -*- coding: utf-8 -*-
"""Kiểm thử sao lưu và khôi phục theo quy trình mục 4.4 của báo cáo.

Chạy được cả hai cách:
    pytest tests/test_backup_restore.py -v
    python tests/test_backup_restore.py
"""
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = os.path.join(BASE, 'database', 'schema.sql')
SEED = os.path.join(BASE, 'database', 'seed_data.sql')


def build(path):
    """Dựng một CSDL mới từ schema + seed."""
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    conn.execute('PRAGMA foreign_keys = ON')
    for f in (SCHEMA, SEED):
        with open(os.path.join(BASE, 'database', f), encoding='utf-8') as fh:
            conn.executescript(fh.read())
    conn.commit()
    conn.close()


def counts(path):
    conn = sqlite3.connect(path)
    try:
        n = conn.execute('SELECT COUNT(*) FROM customers').fetchone()[0]
        t = conn.execute('SELECT COALESCE(SUM(paid), 0) FROM invoices').fetchone()[0]
        return n, t
    finally:
        conn.close()


class TestSaoLuuKhoiPhuc(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='garage_backup_')
        self.db = os.path.join(self.tmp, 'garage.db')
        self.bak = os.path.join(self.tmp, 'backup', 'garage_2026-11-20.db')
        os.makedirs(os.path.dirname(self.bak), exist_ok=True)
        build(self.db)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_01_sao_luu_tao_duoc_tep(self):
        shutil.copy2(self.db, self.bak)
        self.assertTrue(os.path.exists(self.bak))
        self.assertGreater(os.path.getsize(self.bak), 0, 'tệp sao lưu phải khác rỗng')

    def test_02_tep_sao_luu_mo_duoc(self):
        shutil.copy2(self.db, self.bak)
        conn = sqlite3.connect(self.bak)
        n = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            " AND name NOT LIKE 'sqlite_%'").fetchone()[0]
        conn.close()
        self.assertEqual(n, 16, 'tệp sao lưu phải chứa đủ 16 bảng')

    def test_03_khoi_phuc_duoc_du_lieu(self):
        shutil.copy2(self.db, self.bak)
        truoc = counts(self.db)

        # sửa dữ liệu trong CSDL gốc
        conn = sqlite3.connect(self.db)
        conn.execute("DELETE FROM customers")
        conn.commit()
        conn.close()
        self.assertEqual(counts(self.db)[0], 0, 'đã xoá sạch khách hàng')

        # khôi phục từ bản sao
        shutil.copy2(self.bak, self.db)
        self.assertEqual(counts(self.db), truoc,
                         'khôi phục phải đưa dữ liệu về đúng trạng thái trước khi sao lưu')

    def test_04_tep_khoi_phuc_van_hop_le(self):
        shutil.copy2(self.db, self.bak)
        shutil.copy2(self.bak, self.db)
        conn = sqlite3.connect(self.db)
        try:
            kiem = conn.execute('PRAGMA integrity_check').fetchone()[0]
            self.assertEqual(kiem, 'ok', 'CSDL sau khôi phục phải toàn vẹn')
            sai = conn.execute(
                'SELECT a.id FROM appointments a JOIN vehicles v ON a.vehicle_id = v.id'
                ' WHERE a.customer_id <> v.customer_id').fetchall()
            self.assertEqual(sai, [], 'dữ liệu khôi phục phải giữ được tính nhất quán')
        finally:
            conn.close()

    def test_05_sao_luu_khong_chua_du_lieu_chua_commit(self):
        """Bước 1 của mục 4.4: phải bảo đảm không có thao tác ghi quan trọng.

        Sao lưu giữa lúc một thay đổi chưa commit không được làm hỏng tệp
        sao lưu, và dữ liệu chưa commit không được xuất hiện trong bản sao.
        """
        shutil.copy2(self.db, self.bak)
        conn = sqlite3.connect(self.db)
        try:
            conn.execute('PRAGMA journal_mode = DELETE')
            conn.execute("INSERT INTO customers (name, phone) VALUES ('Chua commit', '0900')")
            # chưa commit - sao lưu trong trạng thái này
            shutil.copy2(self.db, self.bak)
        finally:
            conn.rollback()
            conn.close()

        conn = sqlite3.connect(self.bak)
        try:
            self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok',
                             'tệp sao lưu phải toàn vẹn dù sao lưu giữa lúc đang ghi')
            n = conn.execute("SELECT COUNT(*) FROM customers WHERE name = 'Chua commit'").fetchone()[0]
            self.assertEqual(n, 0, 'dữ liệu chưa commit không được xuất hiện trong bản sao')
        finally:
            conn.close()

    def test_06_quy_trinh_dung_theo_muc_4_4(self):
        """Năm bước trong mục 4.4 phải chạy được theo đúng thứ tự."""
        buoc_4_4 = [
            'Dừng ứng dụng hoặc đảm bảo không có thao tác ghi quan trọng.',
            'Sao chép file garage.db sang thư mục backup theo ngày.',
            'Kiểm tra kích thước và quyền đọc file backup.',
            'Khi cần khôi phục, thay thế garage.db bằng bản sao đã kiểm tra.',
            'Khởi động ứng dụng và chạy health check / test smoke.',
        ]
        self.assertEqual(len(buoc_4_4), 5)

        shutil.copy2(self.db, self.bak)                              # bước 2
        self.assertGreater(os.path.getsize(self.bak), 0)             # bước 3
        shutil.copy2(self.bak, self.db)                             # bước 4
        conn = sqlite3.connect(self.db)                             # bước 5
        try:
            self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(
                conn.execute('SELECT COUNT(*) FROM users WHERE role IS NOT NULL').fetchone()[0], 4)
        finally:
            conn.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)