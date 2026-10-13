# -*- coding: utf-8 -*-
"""Sổ cái tồn kho (stock ledger).

Nguyên tắc bất di bất dịch: **mọi** thay đổi `parts.stock` đều phải đi qua
module này, và mỗi thay đổi đi kèm đúng một dòng trong `stock_transactions`.
Bất biến cần giữ sau mọi thao tác:

    parts.stock == SUM(stock_transactions.qty) WHERE part_id = parts.id

Cách làm:
* Số dư mở đầu (migration/seed) ghi một dòng `ADJUSTMENT` đúng bằng `stock`.
* Nhập kho, dùng phụ tùng, hoàn trả, điều chỉnh đều ghi thêm dòng rồi
  cập nhật `parts.stock` trong **cùng** một transaction.
* `kiem_tra_so_sach()` quét mọi phụ tùng và trả về danh sách lệch — dùng cho
  trang kho và cho kiểm thử, không bao giờ tự ý "sửa" số cho khớp.

Lý do tách riêng thay vì để `crud.sua('parts', ..., {'stock': ...})` chạy
tự do: khi stock đổi mà không có ledger, sổ cái mất dấu vết ai nhập/ai dùng,
và không còn cách nào đối chiếu báo cáo tồn kho với thực tế.
"""
from __future__ import annotations

import sqlite3

from ..core.db import fetch_all, fetch_value, transaction
from ..core.errors import KhongTimThay, SaiQuyTac
from ..core.pagination import Trang
from .. import crud

#: Lý do ghi sổ — khớp CHECK constraint trong schema.
LY_DO = {
    'RECEIPT': 'Nhập kho',
    'USAGE': 'Xuất dùng cho phiếu',
    'RETURN': 'Hoàn trả',
    'ADJUSTMENT': 'Điều chỉnh',
}

#: Cột được phép sắp xếp trên màn hình danh sách giao dịch.
SAP_XEP = ['id', 'created_at', 'part_id', 'qty', 'reason']


# ---------------------------------------------------------------------------
# Ghi sổ cái — mọi đường đi của tồn kho đều kết thúc ở đây
# ---------------------------------------------------------------------------
def ghi_giao_dich(conn: sqlite3.Connection, part_id: int, qty: int, reason: str,
                  *, repair_order_id: int | None = None, note: str = '',
                  created_by: int | None = None) -> int:
    """Ghi một dòng ledger và cập nhật `parts.stock` trong cùng transaction.

    `conn` là connection đang mở transaction của người gọi — hàm này không
    tự mở transaction riêng để tránh nested BEGIN (SQLite không hỗ trợ).

    `qty` mang dấu: dương = tăng kho, âm = giảm kho.
    """
    if reason not in LY_DO:
        raise ValueError('lý do giao dịch không hợp lệ: %s' % reason)
    if qty == 0:
        raise SaiQuyTac('Số lượng thay đổi phải khác 0.')
    # Cập nhật stock có điều kiện nguyên tử: không bao giờ cho stock âm.
    if qty < 0:
        da_tru = conn.execute(
            'UPDATE parts SET stock = stock + ? WHERE id = ? AND stock + ? >= 0',
            (qty, part_id, qty)).rowcount
        if da_tru != 1:
            con = conn.execute('SELECT stock FROM parts WHERE id = ?',
                               (part_id,)).fetchone()
            if con is None:
                raise KhongTimThay('Phụ tùng không tồn tại.')
            raise SaiQuyTac('Tồn kho không đủ. Hiện còn %d.'
                            % con['stock'], truong='qty')
    else:
        da_tru = conn.execute(
            'UPDATE parts SET stock = stock + ? WHERE id = ?',
            (qty, part_id)).rowcount
        if da_tru != 1:
            raise KhongTimThay('Phụ tùng không tồn tại.')

    cur = conn.execute(
        'INSERT INTO stock_transactions'
        ' (part_id, qty, reason, repair_order_id, note, created_by)'
        ' VALUES (?, ?, ?, ?, ?, ?)',
        (part_id, qty, reason, repair_order_id, note or None, created_by))
    return int(cur.lastrowid)


# ---------------------------------------------------------------------------
# Nghiệp vụ nhập / điều chỉnh
# ---------------------------------------------------------------------------
def nhap_kho(part_id: int, qty: int, note: str, user) -> int:
    """Nhập thêm phụ tùng vào kho (RECEIPT)."""
    if qty <= 0:
        raise SaiQuyTac('Số lượng nhập phải lớn hơn 0.', truong='qty')
    with transaction() as c:
        return ghi_giao_dich(c, part_id, qty, 'RECEIPT',
                             note=note, created_by=user['id'])


def dieu_chinh(part_id: int, moi: int, note: str, user) -> int:
    """Điều chỉnh tồn kho về một giá trị cụ thể (ADJUSTMENT).

    Dùng khi kiểm kê phát hiện lệch. `moi` là số lượng **mới** sau điều chỉnh,
    không phải số lượng chênh lệch.
    """
    if moi < 0:
        raise SaiQuyTac('Tồn kho không được âm.', truong='qty')
    with transaction() as c:
        hien_tai = c.execute('SELECT stock FROM parts WHERE id = ?',
                             (part_id,)).fetchone()
        if hien_tai is None:
            raise KhongTimThay('Phụ tùng không tồn tại.')
        lech = moi - int(hien_tai['stock'])
        if lech == 0:
            raise SaiQuyTac('Tồn kho hiện tại đã là %d, không cần điều chỉnh.'
                            % moi)
        return ghi_giao_dich(c, part_id, lech, 'ADJUSTMENT',
                             note=note or 'Điều chỉnh kiểm kê về %d.' % moi,
                             created_by=user['id'])


# ---------------------------------------------------------------------------
# Truy vấn
# ---------------------------------------------------------------------------
def danh_sach_giao_dich(trang: Trang, *, part_id: int | None = None,
                        reason: str = '') -> tuple[list[dict], int]:
    dieu_kien, tham_so = ['1=1'], []
    if part_id:
        dieu_kien.append('t.part_id = ?')
        tham_so.append(part_id)
    if reason in LY_DO:
        dieu_kien.append('t.reason = ?')
        tham_so.append(reason)
    return crud.truy_van_danh_sach(
        'stock_transactions',
        cot=('t.id', 't.part_id', 'p.name AS ten_phu_tung', 't.qty',
             't.reason', 't.repair_order_id', 't.note',
             'u.full_name AS nguoi_tao', 't.created_at'),
        dieu_kien=' AND '.join(dieu_kien), tham_so=tham_so, trang=trang,
        sap_xep='id', huong='desc',
        from_clause=('stock_transactions t'
                     ' JOIN parts p ON p.id = t.part_id'
                     ' LEFT JOIN users u ON u.id = t.created_by'))


def hang_can_bao_hang() -> list[dict]:
    """Phụ tùng tồn kho <= ngưỡng cảnh báo (min_stock > 0)."""
    return fetch_all(
        'SELECT id, name, sku, stock, min_stock FROM parts'
        ' WHERE is_active = 1 AND min_stock > 0 AND stock <= min_stock'
        ' ORDER BY stock - min_stock, name')


def kiem_tra_so_sach() -> list[dict]:
    """So sánh `parts.stock` với SUM(ledger). Trả về danh sách lệch.

    Mỗi dòng: {part_id, name, stock, tong_sach, lech}. Rỗng = sổ khớp.
    """
    return fetch_all(
        'SELECT * FROM ('
        '  SELECT p.id AS part_id, p.name, p.stock,'
        '         COALESCE(SUM(t.qty), 0) AS tong_sach,'
        '         p.stock - COALESCE(SUM(t.qty), 0) AS lech'
        '    FROM parts p'
        '    LEFT JOIN stock_transactions t ON t.part_id = p.id'
        '   GROUP BY p.id'
        ') WHERE stock <> tong_sach'
        ' ORDER BY part_id')


def ton_kho_theo_part(part_id: int) -> int:
    return int(fetch_value('SELECT stock FROM parts WHERE id = ?', (part_id,), 0)
               or 0)
