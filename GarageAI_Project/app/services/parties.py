# -*- coding: utf-8 -*-
"""Nghiệp vụ khách hàng, phương tiện và lịch hẹn."""
from __future__ import annotations

import sqlite3

from .. import crud
from ..core.db import fetch_one
from ..core.errors import (AppError, LoiKhongMoDuoc, SaiQuyTac,
                           XungDdot)
from ..models import KhachHangInput, LichHenInput, PhuongTienInput


def _loi_integrity(e: sqlite3.IntegrityError) -> AppError:
    n = str(e)
    if 'plate' in n:
        return XungDdot('Biển số đã tồn tại trong hệ thống.', truong='plate')
    if 'phone' in n:
        return XungDdot('Số điện thoại đã tồn tại.', truong='phone')
    if 'FOREIGN KEY' in n:
        return SaiQuyTac('Dữ liệu tham chiếu không tồn tại.')
    if 'CHECK' in n:
        return SaiQuyTac('Dữ liệu không hợp lệ so với ràng buộc của hệ thống.')
    return LoiKhongMoDuoc()


# ---------------------------------------------------------------------------
# Khách hàng
# ---------------------------------------------------------------------------
def danh_sach_khach(trang, *, q: str = '') -> tuple[list[dict], int]:
    dieu_kien, tham_so = ['1=1'], []
    if q:
        like = '%%%s%%' % q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        dieu_kien.append("(name LIKE ? ESCAPE '\\' OR phone LIKE ? ESCAPE '\\'"
                         " OR email LIKE ? ESCAPE '\\')")
        tham_so += [like, like, like]
    return crud.truy_van_danh_sach(
        'customers', cot=('id', 'name', 'phone', 'email', 'address', 'created_at'),
        dieu_kien=' AND '.join(dieu_kien), tham_so=tham_so, trang=trang,
        sap_xep='name', huong='asc')


def luu_khach(du_lieu: KhachHangInput) -> int:
    du_lieu_dict = {'name': du_lieu.name, 'phone': du_lieu.phone,
                    'email': du_lieu.email, 'address': du_lieu.address}
    if du_lieu.id:
        crud.yeu_cau_co('customers', du_lieu.id, 'khách hàng')
    if crud.co_ban_ghi('customers', 'phone = ? AND id <> ?',
                       (du_lieu.phone, du_lieu.id or 0)):
        raise XungDdot('Số điện thoại đã được khách hàng khác sử dụng.',
                       truong='phone')
    try:
        if du_lieu.id:
            crud.sua('customers', du_lieu.id, du_lieu_dict)
            return du_lieu.id
        return crud.them('customers', du_lieu_dict)
    except sqlite3.IntegrityError as e:
        raise _loi_integrity(e)


def xoa_khach(khoa: int) -> None:
    crud.yeu_cau_co('customers', khoa, 'khách hàng')
    try:
        crud.xoa('customers', khoa)
    except sqlite3.IntegrityError as e:
        raise SaiQuyTac(
            'Khách hàng đã phát sinh giao dịch nên không thể xoá.'
            ' Hãy ẩn hoặc ghi chú thay vì xoá.') from e


# ---------------------------------------------------------------------------
# Phương tiện
# ---------------------------------------------------------------------------
def danh_sach_xe(trang, *, q: str = '', khach: int | None = None) -> tuple[list[dict], int]:
    dieu_kien, tham_so = ['1=1'], []
    if q:
        like = '%%%s%%' % q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        dieu_kien.append("(plate LIKE ? ESCAPE '\\' OR brand LIKE ? ESCAPE '\\'"
                         " OR model LIKE ? ESCAPE '\\')")
        tham_so += [like, like, like]
    if khach:
        dieu_kien.append('v.customer_id = ?')
        tham_so.append(khach)
    return crud.truy_van_danh_sach(
        'vehicles', cot=('v.id', 'v.plate', 'v.brand', 'v.model', 'v.year',
                         'v.vin', 'v.color', 'v.odometer',
                         'v.customer_id', 'c.name AS khach', 'v.is_active'),
        dieu_kien=' AND '.join(dieu_kien), tham_so=tham_so, trang=trang)


def luu_xe(du_lieu: PhuongTienInput) -> int:
    if du_lieu.id:
        crud.yeu_cau_co('vehicles', du_lieu.id, 'phương tiện')
    if crud.khach_hang_theo_id(du_lieu.customer_id) is None:
        raise SaiQuyTac('Khách hàng không tồn tại.', truong='customer_id')
    if crud.co_ban_ghi('vehicles', 'plate = ? AND id <> ?',
                       (du_lieu.plate, du_lieu.id or 0)):
        raise XungDdot('Biển số %s đã tồn tại trong hệ thống.' % du_lieu.plate,
                       truong='plate')
    if du_lieu.vin and crud.co_ban_ghi('vehicles', 'vin = ? AND id <> ?',
                                       (du_lieu.vin, du_lieu.id or 0)):
        raise XungDdot('VIN %s đã tồn tại trong hệ thống.' % du_lieu.vin,
                       truong='vin')
    du = {'plate': du_lieu.plate, 'brand': du_lieu.brand, 'model': du_lieu.model,
          'year': du_lieu.year, 'vin': du_lieu.vin, 'color': du_lieu.color,
          'odometer': du_lieu.odometer,
          'customer_id': du_lieu.customer_id,
          'is_active': 1 if du_lieu.is_active else 0}
    try:
        if du_lieu.id:
            crud.sua('vehicles', du_lieu.id, du)
            return du_lieu.id
        return crud.them('vehicles', du)
    except sqlite3.IntegrityError as e:
        raise _loi_integrity(e)


def xoa_xe(khoa: int) -> None:
    crud.yeu_cau_co('vehicles', khoa, 'phương tiện')
    try:
        crud.xoa('vehicles', khoa)
    except sqlite3.IntegrityError as e:
        raise SaiQuyTac(
            'Xe đã có lịch hẹn hoặc phiếu sửa chữa nên không thể xoá.') from e


# ---------------------------------------------------------------------------
# Lịch hẹn
# ---------------------------------------------------------------------------
def danh_sach_lich(trang, *, trang_thai: str = '', q: str = '') -> tuple[list[dict], int]:
    dieu_kien, tham_so = ['1=1'], []
    if trang_thai:
        dieu_kien.append('a.status = ?')
        tham_so.append(trang_thai)
    if q:
        like = '%%%s%%' % q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        dieu_kien.append("(v.plate LIKE ? ESCAPE '\\' OR c.name LIKE ? ESCAPE '\\')")
        tham_so += [like, like]
    return crud.truy_van_danh_sach(
        'appointments',
        cot=('a.id', 'a.customer_id', 'c.name AS khach', 'a.vehicle_id',
             'v.plate', 'a.scheduled_at', 'a.notes', 'a.status', 'a.created_at'),
        dieu_kien=' AND '.join(dieu_kien), tham_so=tham_so, trang=trang,
        sap_xep='scheduled_at', huong='asc')


def _kiem_tra_lich(du_lieu: LichHenInput) -> None:
    khach = crud.khach_hang_theo_id(du_lieu.customer_id)
    if khach is None:
        raise SaiQuyTac('Khách hàng không tồn tại.', truong='customer_id')
    xe = crud.phuong_tien_theo_id(du_lieu.vehicle_id)
    if xe is None:
        raise SaiQuyTac('Phương tiện không tồn tại.', truong='vehicle_id')
    # Xe phải thuộc đúng khách hàng đã chọn, nếu không dữ liệu sẽ mâu thuẫn.
    if int(xe['customer_id']) != int(du_lieu.customer_id):
        raise SaiQuyTac(
            'Xe %s không thuộc khách hàng đã chọn. Vui lòng chọn đúng xe của khách.'
            % xe['plate'], truong='vehicle_id')
    trung = fetch_one(
        'SELECT id FROM appointments WHERE vehicle_id = ? AND scheduled_at = ?'
        " AND status <> 'CANCELLED' AND id <> ?",
        (du_lieu.vehicle_id, du_lieu.scheduled_at, du_lieu.id or 0))
    if trung:
        raise XungDdot(
            'Xe %s đã có lịch hẹn vào đúng khung giờ này (lịch số %d).'
            % (xe['plate'], trung['id']), truong='scheduled_at')


def luu_lich(du_lieu: LichHenInput) -> int:
    _kiem_tra_lich(du_lieu)
    du = {'customer_id': du_lieu.customer_id, 'vehicle_id': du_lieu.vehicle_id,
          'scheduled_at': du_lieu.scheduled_at, 'notes': du_lieu.notes,
          'status': du_lieu.status}
    if du_lieu.id:
        crud.yeu_cau_co('appointments', du_lieu.id, 'lịch hẹn')
        crud.sua('appointments', du_lieu.id, du)
        return du_lieu.id
    try:
        return crud.them('appointments', du)
    except sqlite3.IntegrityError as e:
        raise _loi_integrity(e)


def xoa_lich(khoa: int) -> None:
    crud.yeu_cau_co('appointments', khoa, 'lịch hẹn')
    crud.xoa('appointments', khoa)