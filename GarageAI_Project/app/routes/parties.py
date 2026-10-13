# -*- coding: utf-8 -*-
"""Khách hàng, phương tiện, lịch hẹn, danh mục và cửa hàng.

Sáu màn hình này có cùng một hình dạng: xem danh sách, mở biểu mẫu, lưu, xoá.
Phần chung đặt trong `crud` và `services`, route chỉ chuyển đổi dữ liệu.
"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Request

from ..core import flash
from ..core.errors import AppError
from ..core.pagination import doc_trang
from ..models import (DichVuInput, KhachHangInput, LichHenInput, PhuTungInput,
                      PhuongTienInput)
from .. import crud
from ..services import auth as auth_svc
from ..services import catalog, parties
from . import LoiForm, du_lieu_form, paged, render

router = APIRouter(tags=['nghiep vu'])


def _ve(r: Request, duong_dan: str, *, loi: str = '', thong_bao: str = ''):
    return flash.chuyen_huong(r, duong_dan, loi=loi, thong_bao=thong_bao)


def _loi(e) -> str:
    if isinstance(e, LoiForm):
        return ' · '.join(e.danh_sach_loi)
    return str(e)


# ===========================================================================
# Khách hàng
# ===========================================================================
@router.get('/customers')
def danh_sach_khach(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'customer.view')
    if user is None:
        return _ve(request, '/accounts/login')
    trang = doc_trang(request)
    q = request.query_params.get('q', '').strip()
    dong, tong = parties.danh_sach_khach(trang, q=q)
    return render(request, 'danh_sach.html', paged({}, 'dong', dong, tong, trang) | {
        'ten': 'customers', 'tieu_de': 'Khách hàng',
        'mo_ta': 'Danh sách khách hàng của garage',
        'q': q,
        'cot': [('name', 'Họ tên'), ('phone', 'Điện thoại'),
                ('email', 'Email'), ('address', 'Địa chỉ')],
        'co_bang_ten': {}, 'quyen_xem': 'customer.view', 'quyen_sua': 'customer.edit',
    })


@router.get('/customers/new')
def form_khach_moi(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'customer.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    return render(request, 'bieu_mau.html', {
        'ten': 'customers', 'tieu_de': 'Khách hàng', 'b': None, 'id': None,
        'truong': [('name', 'Họ và tên', 'text', True),
                   ('phone', 'Số điện thoại', 'text', True),
                   ('email', 'Email', 'text', False),
                   ('address', 'Địa chỉ', 'text', False)],
        'lua_chon': {}, 'loi': {}})


@router.get('/customers/{cid}/edit')
def form_khach_sua(request: Request, cid: int):
    user = auth_svc.yeu_cau_quyen(request, 'customer.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    b = crud.lay_mot('customers', cid)
    if b is None:
        return _ve(request, '/customers', loi='Không tìm thấy khách hàng.')
    return render(request, 'bieu_mau.html', {
        'ten': 'customers', 'tieu_de': 'Khách hàng', 'b': b, 'id': cid,
        'truong': [('name', 'Họ và tên', 'text', True),
                   ('phone', 'Số điện thoại', 'text', True),
                   ('email', 'Email', 'text', False),
                   ('address', 'Địa chỉ', 'text', False)],
        'lua_chon': {}, 'loi': {}})


@router.post('/customers/save')
async def luu_khach(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'customer.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    form = await request.form()
    du_lieu_form_data = {k: v for k, v in form.multi_items()}
    try:
        du_lieu = du_lieu_form(form, KhachHangInput)
        parties.luu_khach(du_lieu)
        tb = 'Đã lưu khách hàng.'
    except (LoiForm, AppError) as e:
        return _ve(request, _duong_dan_quay_lai(du_lieu_form_data), loi=_loi(e))
    except sqlite3.Error as e:
        return _ve(request, '/customers', loi='Không lưu được: %s' % e)
    return _ve(request, '/customers', thong_bao=tb)


@router.post('/customers/{cid}/delete')
def xoa_khach(request: Request, cid: int):
    user = auth_svc.yeu_cau_quyen(request, 'customer.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        parties.xoa_khach(cid)
    except AppError as e:
        return _ve(request, '/customers', loi=str(e))
    except sqlite3.Error as e:
        return _ve(request, '/customers', loi='Không xoá được: %s' % e)
    return _ve(request, '/customers', thong_bao='Đã xoá khách hàng.')


def _duong_dan_quay_lai(du_lieu: dict) -> str:
    khoa = du_lieu.get('id')
    return '/customers/%s/edit' % khoa if khoa else '/customers/new'


# ===========================================================================
# Phương tiện
# ===========================================================================
@router.get('/vehicles')
def danh_sach_xe(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'vehicle.view')
    if user is None:
        return _ve(request, '/accounts/login')
    trang = doc_trang(request)
    qs = request.query_params
    q = qs.get('q', '').strip()
    khach = qs.get('khach') or None
    dong, tong = parties.danh_sach_xe(trang, q=q, khach=khach)
    return render(request, 'danh_sach.html', paged({}, 'dong', dong, tong, trang) | {
        'ten': 'vehicles', 'tieu_de': 'Phương tiện',
        'mo_ta': 'Danh sách xe của khách hàng', 'q': q,
        'khach_hien_tai': khach or '',
        'cot': [('plate', 'Biển số'), ('brand', 'Hãng'), ('model', 'Dòng xe'),
                ('year', 'Năm'), ('khach', 'Khách hàng')],
        'co_bang_ten': {}, 'quyen_xem': 'vehicle.view', 'quyen_sua': 'vehicle.edit',
        'bo_loc_khach': crud.lua_chon_khach(),
    })


@router.get('/vehicles/new')
def form_xe_moi(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'vehicle.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    return render(request, 'bieu_mau.html', {
        'ten': 'vehicles', 'tieu_de': 'Phương tiện', 'b': None, 'id': None,
        'truong': [('plate', 'Biển số', 'text', True),
                   ('brand', 'Hãng xe', 'text', True),
                   ('model', 'Dòng xe', 'text', True),
                   ('year', 'Năm sản xuất', 'int', False),
                   ('vin', 'VIN (số khung, 17 ký tự)', 'text', False),
                   ('color', 'Màu sơn', 'text', False),
                   ('odometer', 'Số km hiện tại', 'int', False),
                   ('customer_id', 'Khách hàng', 'select', True)],
        'lua_chon': {'customer_id': crud.lua_chon_khach()}, 'loi': {}})


@router.get('/vehicles/{vid}/edit')
def form_xe_sua(request: Request, vid: int):
    user = auth_svc.yeu_cau_quyen(request, 'vehicle.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    b = crud.lay_mot('vehicles', vid)
    if b is None:
        return _ve(request, '/vehicles', loi='Không tìm thấy phương tiện.')
    return render(request, 'bieu_mau.html', {
        'ten': 'vehicles', 'tieu_de': 'Phương tiện', 'b': b, 'id': vid,
        'truong': [('plate', 'Biển số', 'text', True),
                   ('brand', 'Hãng xe', 'text', True),
                   ('model', 'Dòng xe', 'text', True),
                   ('year', 'Năm sản xuất', 'int', False),
                   ('vin', 'VIN (số khung, 17 ký tự)', 'text', False),
                   ('color', 'Màu sơn', 'text', False),
                   ('odometer', 'Số km hiện tại', 'int', False),
                   ('customer_id', 'Khách hàng', 'select', True)],
        'lua_chon': {'customer_id': crud.lua_chon_khach()}, 'loi': {}})


@router.post('/vehicles/save')
async def luu_xe(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'vehicle.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    form = await request.form()
    du = {k: v for k, v in form.multi_items()}
    try:
        parties.luu_xe(du_lieu_form(form, PhuongTienInput))
        tb = 'Đã lưu phương tiện.'
    except (LoiForm, AppError) as e:
        return _ve(request, '/vehicles/%s/edit' % du['id'] if du.get('id')
                   else '/vehicles/new', loi=_loi(e))
    except sqlite3.Error as e:
        return _ve(request, '/vehicles', loi='Không lưu được: %s' % e)
    return _ve(request, '/vehicles', thong_bao=tb)


@router.post('/vehicles/{vid}/delete')
def xoa_xe(request: Request, vid: int):
    user = auth_svc.yeu_cau_quyen(request, 'vehicle.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        parties.xoa_xe(vid)
    except AppError as e:
        return _ve(request, '/vehicles', loi=str(e))
    except sqlite3.Error as e:
        return _ve(request, '/vehicles', loi='Không xoá được: %s' % e)
    return _ve(request, '/vehicles', thong_bao='Đã xoá phương tiện.')


# ===========================================================================
# Lịch hẹn
# ===========================================================================
@router.get('/appointments')
def danh_sach_lich(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'appointment.view')
    if user is None:
        return _ve(request, '/accounts/login')
    trang = doc_trang(request)
    qs = request.query_params
    tt = qs.get('trang_thai', '').strip()
    dong, tong = parties.danh_sach_lich(trang, trang_thai=tt,
                                         q=qs.get('q', '').strip())
    return render(request, 'danh_sach.html', paged({}, 'dong', dong, tong, trang) | {
        'ten': 'appointments', 'tieu_de': 'Lịch hẹn',
        'mo_ta': 'Lịch hẹn tiếp nhận và bảo dưỡng', 'q': qs.get('q', ''),
        'trang_thai': tt, 'trang_thai_list': ['SCHEDULED', 'CONFIRMED', 'CANCELLED', 'DONE'],
        'cot': [('khach', 'Khách hàng'), ('plate', 'Biển số'),
                ('scheduled_at', 'Thời gian'), ('status', 'Trạng thái'),
                ('notes', 'Ghi chú')],
        'co_bang_ten': {}, 'quyen_xem': 'appointment.view',
        'quyen_sua': 'appointment.edit',
    })


@router.get('/appointments/new')
def form_lich_moi(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'appointment.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    return render(request, 'bieu_mau.html', {
        'ten': 'appointments', 'tieu_de': 'Lịch hẹn', 'b': None, 'id': None,
        'truong': [('customer_id', 'Khách hàng', 'select', True),
                   ('vehicle_id', 'Phương tiện', 'select', True),
                   ('scheduled_at', 'Thời gian hẹn (YYYY-MM-DD HH:MM)', 'text', True),
                   ('status', 'Trạng thái', 'fixed', True),
                   ('notes', 'Ghi chú', 'text', False)],
        'lua_chon': {'customer_id': crud.lua_chon_khach(),
                     'vehicle_id': crud.lua_chon_xe()}, 'loi': {}})


@router.get('/appointments/{lid}/edit')
def form_lich_sua(request: Request, lid: int):
    user = auth_svc.yeu_cau_quyen(request, 'appointment.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    b = crud.lay_mot('appointments', lid)
    if b is None:
        return _ve(request, '/appointments', loi='Không tìm thấy lịch hẹn.')
    return render(request, 'bieu_mau.html', {
        'ten': 'appointments', 'tieu_de': 'Lịch hẹn', 'b': b, 'id': lid,
        'truong': [('customer_id', 'Khách hàng', 'select', True),
                   ('vehicle_id', 'Phương tiện', 'select', True),
                   ('scheduled_at', 'Thời gian hẹn (YYYY-MM-DD HH:MM)', 'text', True),
                   ('status', 'Trạng thái', 'fixed', True),
                   ('notes', 'Ghi chú', 'text', False)],
        'lua_chon': {'customer_id': crud.lua_chon_khach(),
                     'vehicle_id': crud.lua_chon_xe()}, 'loi': {}})


@router.post('/appointments/save')
async def luu_lich(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'appointment.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    form = await request.form()
    du = {k: v for k, v in form.multi_items()}
    try:
        parties.luu_lich(du_lieu_form(form, LichHenInput))
        tb = 'Đã lưu lịch hẹn.'
    except (LoiForm, AppError) as e:
        return _ve(request, '/appointments/%s/edit' % du['id'] if du.get('id')
                   else '/appointments/new', loi=_loi(e))
    except sqlite3.Error as e:
        return _ve(request, '/appointments', loi='Không lưu được: %s' % e)
    return _ve(request, '/appointments', thong_bao=tb)


@router.post('/appointments/{lid}/delete')
def xoa_lich(request: Request, lid: int):
    user = auth_svc.yeu_cau_quyen(request, 'appointment.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        parties.xoa_lich(lid)
    except AppError as e:
        return _ve(request, '/appointments', loi=str(e))
    except sqlite3.Error as e:
        return _ve(request, '/appointments', loi='Không xoá được: %s' % e)
    return _ve(request, '/appointments', thong_bao='Đã xoá lịch hẹn.')


# ===========================================================================
# Danh mục
# ===========================================================================
@router.get('/services')
def danh_sach_dich_vu(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'catalog.view')
    if user is None:
        return _ve(request, '/accounts/login')
    trang = doc_trang(request)
    qs = request.query_params
    dong, tong = catalog.danh_sach_dich_vu(
        trang, q=qs.get('q', '').strip(), dang_dung=qs.get('dang_dung', ''))
    return render(request, 'danh_sach.html', paged({}, 'dong', dong, tong, trang) | {
        'ten': 'services', 'tieu_de': 'Danh mục dịch vụ',
        'mo_ta': 'Dịch vụ sửa chữa và đơn giá', 'q': qs.get('q', ''),
        'cot': [('name', 'Tên dịch vụ'), ('price', 'Đơn giá'),
                ('description', 'Mô tả'), ('is_active', 'Đang dùng')],
        'co_bang_ten': {}, 'quyen_xem': 'catalog.view', 'quyen_sua': 'catalog.edit',
    })


@router.get('/services/new')
def form_dich_vu_moi(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'catalog.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    return render(request, 'bieu_mau.html', {
        'ten': 'services', 'tieu_de': 'Dịch vụ', 'b': None, 'id': None,
        'truong': [('name', 'Tên dịch vụ', 'text', True),
                   ('price', 'Đơn giá (đồng)', 'int', True),
                   ('description', 'Mô tả cho khách', 'text', False)],
        'lua_chon': {}, 'loi': {}})


@router.get('/services/{sid}/edit')
def form_dich_vu_sua(request: Request, sid: int):
    user = auth_svc.yeu_cau_quyen(request, 'catalog.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    return render(request, 'bieu_mau.html', {
        'ten': 'services', 'tieu_de': 'Dịch vụ', 'b': crud.lay_mot('services', sid),
        'id': sid,
        'truong': [('name', 'Tên dịch vụ', 'text', True),
                   ('price', 'Đơn giá (đồng)', 'int', True),
                   ('description', 'Mô tả cho khách', 'text', False)],
        'lua_chon': {}, 'loi': {}})


@router.post('/services/save')
async def luu_dich_vu(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'catalog.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    form = await request.form()
    du = {k: v for k, v in form.multi_items()}
    try:
        catalog.luu_dich_vu(du_lieu_form(form, DichVuInput))
        tb = 'Đã lưu dịch vụ.'
    except (LoiForm, AppError) as e:
        return _ve(request, '/services/%s/edit' % du['id'] if du.get('id')
                   else '/services/new', loi=_loi(e))
    except sqlite3.Error as e:
        return _ve(request, '/services', loi='Không lưu được: %s' % e)
    return _ve(request, '/services', thong_bao=tb)


@router.post('/services/{sid}/delete')
def xoa_dich_vu(request: Request, sid: int):
    user = auth_svc.yeu_cau_quyen(request, 'catalog.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        catalog.xoa_dich_vu(sid)
    except AppError as e:
        return _ve(request, '/services', loi=str(e))
    except sqlite3.Error as e:
        return _ve(request, '/services', loi='Không xoá được: %s' % e)
    return _ve(request, '/services', thong_bao='Đã xoá dịch vụ.')


@router.get('/parts')
def danh_sach_phu_tung(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'catalog.view')
    if user is None:
        return _ve(request, '/accounts/login')
    trang = doc_trang(request)
    qs = request.query_params
    dong, tong = catalog.danh_sach_phu_tung(
        trang, q=qs.get('q', '').strip(), dang_dung=qs.get('dang_dung', ''),
        het_kho=qs.get('het_kho', ''))
    return render(request, 'danh_sach.html', paged({}, 'dong', dong, tong, trang) | {
        'ten': 'parts', 'tieu_de': 'Danh mục phụ tùng',
        'mo_ta': 'Phụ tùng, tồn kho và đơn giá', 'q': qs.get('q', ''),
        'cot': [('name', 'Tên phụ tùng'), ('sku', 'Mã'), ('price', 'Đơn giá'),
                ('stock', 'Tồn kho'), ('min_stock', 'Cảnh báo'),
                ('is_active', 'Đang dùng')],
        'co_bang_ten': {}, 'quyen_xem': 'catalog.view', 'quyen_sua': 'catalog.edit',
    })


@router.get('/parts/new')
def form_phu_tung_moi(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'catalog.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    return render(request, 'bieu_mau.html', {
        'ten': 'parts', 'tieu_de': 'Phụ tùng', 'b': None, 'id': None,
        'truong': [('name', 'Tên phụ tùng', 'text', True),
                   ('sku', 'Mã sản phẩm', 'text', False),
                   ('price', 'Đơn giá (đồng)', 'int', True),
                   ('stock', 'Tồn kho đầu kỳ', 'int', True),
                   ('min_stock', 'Ngưỡng cảnh báo', 'int', False),
                   ('description', 'Mô tả', 'text', False)],
        'lua_chon': {}, 'loi': {}})


@router.get('/parts/{pid}/edit')
def form_phu_tung_sua(request: Request, pid: int):
    user = auth_svc.yeu_cau_quyen(request, 'catalog.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    return render(request, 'bieu_mau.html', {
        'ten': 'parts', 'tieu_de': 'Phụ tùng', 'b': crud.lay_mot('parts', pid),
        'id': pid,
        'truong': [('name', 'Tên phụ tùng', 'text', True),
                   ('sku', 'Mã sản phẩm', 'text', False),
                   ('price', 'Đơn giá (đồng)', 'int', True),
                   ('stock', 'Tồn kho', 'int', True),
                   ('min_stock', 'Ngưỡng cảnh báo', 'int', False),
                   ('description', 'Mô tả', 'text', False)],
        'lua_chon': {}, 'loi': {}})


@router.post('/parts/save')
async def luu_phu_tung(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'catalog.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    form = await request.form()
    du = {k: v for k, v in form.multi_items()}
    try:
        catalog.luu_phu_tung(du_lieu_form(form, PhuTungInput))
        tb = 'Đã lưu phụ tùng.'
    except (LoiForm, AppError) as e:
        return _ve(request, '/parts/%s/edit' % du['id'] if du.get('id')
                   else '/parts/new', loi=_loi(e))
    except sqlite3.Error as e:
        return _ve(request, '/parts', loi='Không lưu được: %s' % e)
    return _ve(request, '/parts', thong_bao=tb)


@router.post('/parts/{pid}/delete')
def xoa_phu_tung(request: Request, pid: int):
    user = auth_svc.yeu_cau_quyen(request, 'catalog.edit')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        catalog.xoa_phu_tung(pid)
    except AppError as e:
        return _ve(request, '/parts', loi=str(e))
    except sqlite3.Error as e:
        return _ve(request, '/parts', loi='Không xoá được: %s' % e)
    return _ve(request, '/parts', thong_bao='Đã xoá phụ tùng.')


# ===========================================================================
# Cửa hàng — mở rộng, ngoài phạm vi đề tài
# ===========================================================================
@router.get('/shop')
def cua_hang(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'shop.view')
    if user is None:
        return _ve(request, '/accounts/login')
    trang = doc_trang(request)
    q = request.query_params.get('q', '').strip()
    dong, tong = catalog.danh_sach_san_pham(trang, q=q)
    return render(request, 'cua_hang.html', paged({}, 'dong', dong, tong, trang) | {
        'q': q})