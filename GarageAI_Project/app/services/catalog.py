# -*- coding: utf-8 -*-
"""Nghiệp vụ danh mục (dịch vụ, phụ tùng) và cửa hàng mở rộng."""
from __future__ import annotations

import sqlite3

from .. import crud
from ..core.db import fetch_one, transaction
from ..core.errors import AppError, LoiKhongMoDuoc, SaiQuyTac, XungDdot
from ..models import DichVuInput, PhuTungInput, SanPhamInput


def _loi_integrity(e: sqlite3.IntegrityError) -> AppError:
    n = str(e)
    if 'CHECK' in n and 'price' in n:
        return SaiQuyTac('Đơn giá phải lớn hơn hoặc bằng 0.')
    if 'CHECK' in n and 'stock' in n:
        return SaiQuyTac('Tồn kho phải lớn hơn hoặc bằng 0.')
    if 'sku' in n:
        return XungDdot('Mã sản phẩm đã tồn tại.', truong='sku')
    if 'FOREIGN KEY' in n:
        return SaiQuyTac('Danh mục tham chiếu không tồn tại.')
    return LoiKhongMoDuoc()


# ---------------------------------------------------------------------------
# Dịch vụ
# ---------------------------------------------------------------------------
def danh_sach_dich_vu(trang, *, q: str = '', dang_dung: str = '') -> tuple[list[dict], int]:
    dieu_kien, tham_so = ['1=1'], []
    if q:
        like = '%%%s%%' % q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        dieu_kien.append("(name LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\')")
        tham_so += [like, like]
    if dang_dung in ('0', '1'):
        dieu_kien.append('is_active = ?')
        tham_so.append(int(dang_dung))
    return crud.truy_van_danh_sach(
        'services', cot=('id', 'name', 'price', 'description', 'is_active'),
        dieu_kien=' AND '.join(dieu_kien), tham_so=tham_so, trang=trang,
        sap_xep='name', huong='asc')


def luu_dich_vu(du_lieu: DichVuInput) -> int:
    du = {'name': du_lieu.name, 'price': du_lieu.price,
          'description': du_lieu.description,
          'is_active': 1 if du_lieu.is_active else 0}
    if du_lieu.id:
        crud.yeu_cau_co('services', du_lieu.id, 'dịch vụ')
        crud.sua('services', du_lieu.id, du)
        return du_lieu.id
    try:
        return crud.them('services', du)
    except sqlite3.IntegrityError as e:
        raise _loi_integrity(e)


def xoa_dich_vu(khoa: int) -> None:
    crud.yeu_cau_co('services', khoa, 'dịch vụ')
    if crud.co_ban_ghi('repair_order_items', 'service_id = ?', (khoa,)):
        raise SaiQuyTac('Dịch vụ đã dùng trong hạng mục của phiếu nên không thể xoá.'
                        ' Hãy chuyển sang trạng thái ngừng dùng.')
    crud.xoa('services', khoa)


# ---------------------------------------------------------------------------
# Phụ tùng
# ---------------------------------------------------------------------------
def danh_sach_phu_tung(trang, *, q: str = '', dang_dung: str = '',
                       het_kho: str = '') -> tuple[list[dict], int]:
    dieu_kien, tham_so = ['1=1'], []
    if q:
        like = '%%%s%%' % q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        dieu_kien.append('name LIKE ? ESCAPE \'\\\'')
        tham_so.append(like)
    if dang_dung in ('0', '1'):
        dieu_kien.append('is_active = ?')
        tham_so.append(int(dang_dung))
    if het_kho in ('0', '1'):
        dieu_kien.append('stock %s ?' % ('=' if het_kho == '0' else '>'))
        tham_so.append(int(het_kho))
    return crud.truy_van_danh_sach(
        'parts', cot=('id', 'name', 'sku', 'price', 'stock', 'description', 'is_active'),
        dieu_kien=' AND '.join(dieu_kien), tham_so=tham_so, trang=trang,
        sap_xep='name', huong='asc')


def luu_phu_tung(du_lieu: PhuTungInput) -> int:
    du = {'name': du_lieu.name, 'sku': du_lieu.sku, 'price': du_lieu.price,
          'stock': du_lieu.stock, 'description': du_lieu.description,
          'is_active': 1 if du_lieu.is_active else 0}
    if du_lieu.id:
        crud.yeu_cau_co('parts', du_lieu.id, 'phụ tùng')
        crud.sua('parts', du_lieu.id, du)
        return du_lieu.id
    try:
        return crud.them('parts', du)
    except sqlite3.IntegrityError as e:
        raise _loi_integrity(e)


def xoa_phu_tung(khoa: int) -> None:
    crud.yeu_cau_co('parts', khoa, 'phụ tùng')
    if crud.co_ban_ghi('repair_order_items', 'part_id = ?', (khoa,)):
        raise SaiQuyTac('Phụ tùng đã dùng trong hạng mục của phiếu nên không thể xoá.'
                        ' Hãy chuyển sang trạng thái ngừng dùng.')
    crud.xoa('parts', khoa)


# ---------------------------------------------------------------------------
# Cửa hàng — mở rộng, ngoài phạm vi đề tài
# ---------------------------------------------------------------------------
def danh_sach_san_pham(trang, *, q: str = '') -> tuple[list[dict], int]:
    dieu_kien, tham_so = ['1=1'], []
    if q:
        like = '%%%s%%' % q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        dieu_kien.append("(p.name LIKE ? ESCAPE '\\' OR c.name LIKE ? ESCAPE '\\')")
        tham_so += [like, like]
    # Luôn ẩn sản phẩm đã ngừng bán, kể cả khi tìm theo tên danh mục.
    dieu_kien.append('p.is_active = 1')
    return crud.truy_van_danh_sach(
        'shop_products',
        cot=('p.id', 'p.sku', 'p.name', 'c.name AS danh_muc', 'p.price',
             'p.stock', 'p.description', 'p.is_active'),
        dieu_kien=' AND '.join(dieu_kien), tham_so=tham_so, trang=trang,
        sap_xep='name', huong='asc')


def luu_san_pham(du_lieu: SanPhamInput) -> int:
    du = {'name': du_lieu.name, 'sku': du_lieu.sku, 'category_id': du_lieu.category_id,
          'price': du_lieu.price, 'stock': du_lieu.stock,
          'description': du_lieu.description,
          'is_active': 1 if du_lieu.is_active else 0}
    if du_lieu.id:
        crud.sua('shop_products', du_lieu.id, du)
        return du_lieu.id
    try:
        return crud.them('shop_products', du)
    except sqlite3.IntegrityError as e:
        raise _loi_integrity(e)