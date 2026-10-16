# -*- coding: utf-8 -*-
"""Khởi tạo cơ sở dữ liệu garage.db từ schema.sql và seed_data.sql."""
import os
import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, 'garage.db')

for _f in (DB, DB + '-wal', DB + '-shm'):
    if os.path.exists(_f):
        os.remove(_f)

conn = sqlite3.connect(DB)
conn.execute('PRAGMA foreign_keys = ON')
for f in ('schema.sql', 'seed_data.sql'):
    p = os.path.join(BASE, 'database', f)
    with open(p, encoding='utf-8') as fh:
        conn.executescript(fh.read())
conn.commit()

print('Đã tạo %s' % DB)
print()
print('%-22s %8s %12s' % ('BẢNG', 'SỐ DÒNG', 'DUNG LƯỢNG'))
print('-' * 44)
total = 0
for (name,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY rowid"):
    n = conn.execute('SELECT COUNT(*) FROM %s' % name).fetchone()[0]
    total += n
    print('%-22s %8d' % (name, n))
print('-' * 44)
print('%-22s %8d' % ('TỔNG', total))
print()
print('Phiếu sửa chữa theo trạng thái:')
for st, n in conn.execute(
        'SELECT status, COUNT(*) FROM repair_orders GROUP BY status ORDER BY status'):
    print('   %-12s %d' % (st, n))
print()
print('Hoá đơn theo trạng thái thanh toán:')
for st, n in conn.execute(
        'SELECT status, COUNT(*) FROM invoices GROUP BY status ORDER BY status'):
    print('   %-12s %d' % (st, n))
print()
print('Doanh thu đã thu: %s đồng' % format(
    conn.execute("SELECT COALESCE(SUM(paid),0) FROM invoices").fetchone()[0], ',').replace(',', '.'))
print('Tổng giá trị tồn kho phụ tùng: %s đồng' % format(
    conn.execute('SELECT COALESCE(SUM(stock*price),0) FROM parts').fetchone()[0], ',').replace(',', '.'))
conn.close()