# -*- coding: utf-8 -*-
"""Phiếu sửa chữa, hạng mục, hoá đơn và thanh toán."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Form, Request

from ..core import flash
from ..core.errors import AppError
from ..core.pagination import doc_trang
from ..models import (DoiTrangThaiInput, NghiemThuInput, NhatKyInput,
                      PhanCongInput, TaoPhieuInput, ThemHangMucInput,
                      ThanhToanInput, TiepNhanInput)
from .. import crud
from ..services import auth as auth_svc
from ..services import billing, orders
from . import LoiForm, du_lieu_form, paged, render

router = APIRouter(tags=['phieu sua chua'])


def _ve(r: Request, duong_dan: str, *, loi: str = '', thong_bao: str = ''):
    return flash.chuyen_huong(r, duong_dan, loi=loi, thong_bao=thong_bao)


def _loi(e: AppError | LoiForm) -> str:
    if isinstance(e, LoiForm):
        return ' · '.join(e.danh_sach_loi)
    return str(e)


# ---------------------------------------------------------------------------
# Danh sách và chi tiết
# ---------------------------------------------------------------------------
@router.get('/repair-orders')
def danh_sach_phieu(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'order.view')
    if user is None:
        return _ve(request, '/accounts/login')
    trang = doc_trang(request)
    qs = request.query_params
    dong, tong = orders.danh_sach_phieu(
        trang, q=qs.get('q', '').strip(),
        trang_thai=qs.get('trang_thai', '').strip(), user=user)
    return render(request, 'phieu.html', paged({}, 'dong', dong, tong, trang) | {
        'q': qs.get('q', ''), 'trang_thai': qs.get('trang_thai', ''),
        'co_the_tao': auth_svc.co_the_quyen(user, 'order.create'),
        'trang_thai_list': ['RECEIVED', 'INSPECTING', 'ESTIMATING', 'REPAIRING',
                            'COMPLETED', 'CANCELLED'],
    })


@router.get('/repair-orders/new')
def form_tiep_nhan(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'order.create')
    if user is None:
        return _ve(request, '/accounts/login')
    return render(request, 'phieu_moi.html', {
        'xe': crud.lua_chon_xe(), 'ktv': crud.lua_chon_ky_thuat_vien()})


@router.post('/repair-orders/create')
async def tao_phieu(request: Request, vehicle_id: str = Form(''),
                    technician_id: str = Form(''), technical_notes: str = Form('')):
    user = auth_svc.yeu_cau_quyen(request, 'order.create')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        khoa = orders.tao_phieu(du_lieu_form(
            {'vehicle_id': vehicle_id, 'technician_id': technician_id,
             'technical_notes': technical_notes}, TaoPhieuInput), user)
    except (LoiForm, AppError) as e:
        return _ve(request, '/repair-orders/new', loi=_loi(e))
    except sqlite3.Error as e:
        return _ve(request, '/repair-orders/new', loi='Không tạo được phiếu: %s' % e)
    return _ve(request, '/repair-orders/%d' % khoa, thong_bao='Đã tiếp nhận xe.')


@router.get('/repair-orders/{oid}')
def chi_tiet_phieu(request: Request, oid: int):
    user = auth_svc.yeu_cau_quyen(request, 'order.view')
    if user is None:
        return _ve(request, '/accounts/login')
    p = orders.chi_tiet(oid, user=user)
    duoc = auth_svc.co_the_quyen(user, 'order.item')
    if duoc and not auth_svc.gan_quyen_phan_cong(user):
        from ..services.security_matrix import duoc_gan_cong
        duoc = duoc_gan_cong(user, p)
    hd = orders.hoa_don_cua_phieu(oid)
    from ..core.db import fetch_one
    tiep_nhan = fetch_one(
        'SELECT i.*, u.full_name AS nguoi_tiep_nhan'
        ' FROM intake_records i LEFT JOIN users u ON u.id = i.created_by'
        ' WHERE i.repair_order_id = ?', (oid,))
    return render(request, 'phieu_chi_tiet.html', {
        'p': p, 'items': orders.hang_muc(oid), 'logs': orders.nhat_ky(oid),
        'hoa_don': hd, 'khoan_thu': billing.khoan_thu(hd['id']) if hd else [],
        'tiep_nhan': tiep_nhan,
        'co_the_sua': duoc,
        'co_gan_cong': auth_svc.co_the_quyen(user, 'order.assign'),
        'co_lap_hoa_don': auth_svc.co_the_quyen(user, 'invoice.manage'),
        'co_thu_tien': auth_svc.co_the_quyen(user, 'payment.record'),
        'co_doi_trang_thai': auth_svc.co_the_quyen(user, 'order.progress'),
        'co_nghiem_thu': auth_svc.co_the_quyen(user, 'order.accept'),
        'ktv': crud.lua_chon_ky_thuat_vien(),
        'dich_vu': crud.lua_chon_dich_vu(), 'phu_tung': crud.lua_chon_phu_tung(),
        'lua_chon_trang_thai': orders.CHUYEN_TRANG_THAI.get(p['status'], []),
    })


# ---------------------------------------------------------------------------
# Thao tác trên phiếu
# ---------------------------------------------------------------------------
@router.post('/repair-orders/{oid}/status')
async def doi_trang_thai(request: Request, oid: int, status: str = Form('')):
    user = auth_svc.yeu_cau_quyen(request, 'order.progress')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        orders.doi_trang_thai(oid, du_lieu_form({'status': status}, DoiTrangThaiInput), user)
        tb = 'Đã đổi trạng thái phiếu.'
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    return _ve(request, '/repair-orders/%d' % oid, loi=loi, thong_bao=tb)


@router.post('/repair-orders/{oid}/assign')
async def gan_ky_thuat_vien(request: Request, oid: int, technician_id: str = Form('')):
    user = auth_svc.yeu_cau_quyen(request, 'order.assign')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        orders.gan_ky_thuat_vien(oid, du_lieu_form(
            {'technician_id': technician_id}, PhanCongInput), user)
        tb = 'Đã phân công.'
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    return _ve(request, '/repair-orders/%d' % oid, loi=loi, thong_bao=tb)


@router.post('/repair-orders/{oid}/items')
async def them_hang_muc(request: Request, oid: int, loai: str = Form(''),
                        ma: str = Form(''), qty: str = Form('1')):
    user = auth_svc.yeu_cau_quyen(request, 'order.item')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        orders.them_hang_muc(oid, du_lieu_form(
            {'loai': loai, 'ma': ma, 'qty': qty}, ThemHangMucInput), user)
        tb = 'Đã thêm hạng mục.'
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    except sqlite3.Error as e:
        tb, loi = '', 'Không thêm được hạng mục: %s' % e
    return _ve(request, '/repair-orders/%d' % oid, loi=loi, thong_bao=tb)


@router.post('/repair-orders/{oid}/items/{iid}/remove')
async def go_hang_muc(request: Request, oid: int, iid: int):
    user = auth_svc.yeu_cau_quyen(request, 'order.item')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        orders.go_hang_muc(oid, iid, user)
        tb = 'Đã gỡ hạng mục.'
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    return _ve(request, '/repair-orders/%d' % oid, loi=loi, thong_bao=tb)


@router.post('/repair-orders/{oid}/logs')
async def them_nhat_ky(request: Request, oid: int, note: str = Form('')):
    user = auth_svc.yeu_cau_quyen(request, 'order.progress')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        orders.them_nhat_ky(oid, du_lieu_form({'note': note}, NhatKyInput), user)
        tb = 'Đã ghi nhật ký.'
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    return _ve(request, '/repair-orders/%d' % oid, loi=loi, thong_bao=tb)


# ---------------------------------------------------------------------------
# Tiếp nhận xe và nghiệm thu
# ---------------------------------------------------------------------------
@router.post('/repair-orders/{oid}/intake')
async def ghi_tiep_nhan(request: Request, oid: int,
                        odometer_at_intake: str = Form(''),
                        fuel_level: str = Form('UNKNOWN'),
                        exterior_condition: str = Form(''),
                        accessories: str = Form(''),
                        notes: str = Form('')):
    user = auth_svc.yeu_cau_quyen(request, 'order.create')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        orders.ghi_tiep_nhan(oid, du_lieu_form(
            {'odometer_at_intake': odometer_at_intake, 'fuel_level': fuel_level,
             'exterior_condition': exterior_condition, 'accessories': accessories,
             'notes': notes}, TiepNhanInput), user)
        tb = 'Đã ghi biên bản tiếp nhận.'
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    except sqlite3.Error as e:
        tb, loi = '', 'Không ghi được biên bản: %s' % e
    return _ve(request, '/repair-orders/%d' % oid, loi=loi, thong_bao=tb)


@router.post('/repair-orders/{oid}/accept')
async def nghiem_thu(request: Request, oid: int, acceptance_note: str = Form('')):
    user = auth_svc.yeu_cau_quyen(request, 'order.accept')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        orders.nghiem_thu(oid, du_lieu_form(
            {'acceptance_note': acceptance_note}, NghiemThuInput), user)
        tb = 'Đã nghiệm thu xe.'
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    except sqlite3.Error as e:
        tb, loi = '', 'Không nghiệm thu được: %s' % e
    return _ve(request, '/repair-orders/%d' % oid, loi=loi, thong_bao=tb)


# ---------------------------------------------------------------------------
# Hoá đơn và thanh toán
# ---------------------------------------------------------------------------
@router.post('/repair-orders/{oid}/invoice')
async def lap_hoa_don(request: Request, oid: int):
    user = auth_svc.yeu_cau_quyen(request, 'invoice.manage')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        billing.lap_hoa_don(oid, user)
        tb = 'Đã lập hoá đơn.'
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    return _ve(request, '/repair-orders/%d' % oid, loi=loi, thong_bao=tb)


@router.get('/invoices')
def danh_sach_hoa_don(request: Request):
    """Trang danh sách hoá đơn — bổ sung so với phiên bản trước."""
    user = auth_svc.nguoi_dung_hien_tai(request)
    if user is None:
        return _ve(request, '/accounts/login')
    if not (auth_svc.co_the_quyen(user, 'report.view')
            or auth_svc.co_the_quyen(user, 'payment.record')):
        from ..core.errors import KhongCoQuyen
        raise KhongCoQuyen('Vai trò của bạn không được phép xem danh sách hoá đơn.')
    trang = doc_trang(request)
    qs = request.query_params
    dong, tong = billing.danh_sach_hoa_don(
        trang, trang_thai=qs.get('trang_thai', '').strip(), q=qs.get('q', '').strip())
    return render(request, 'hoa_don.html', paged({}, 'dong', dong, tong, trang) | {
        'q': qs.get('q', ''), 'trang_thai': qs.get('trang_thai', ''),
        'trang_thai_list': ['UNPAID', 'PARTIAL', 'PAID'],
    })


@router.post('/invoices/{iid}/pay')
async def thanh_toan(request: Request, iid: int, amount: str = Form(''),
                     method: str = Form('CASH')):
    user = auth_svc.yeu_cau_quyen(request, 'payment.record')
    if user is None:
        return _ve(request, '/accounts/login')
    # Lấy đường dẫn quay lại **trước** khi thử ghi: khi thanh toán bị từ chối
    # (ví dụ vượt số còn phải thu) người dùng phải quay lại đúng phiếu đó,
    # chứ không phải danh sách phiếu để tìm lại từ đầu.
    try:
        duong_dan = '/repair-orders/%d' % billing.lay_hoa_don(iid)['repair_order_id']
    except AppError:
        duong_dan = '/invoices'
    try:
        loi = ''
        du_lieu = du_lieu_form({'amount': amount, 'method': method}, ThanhToanInput)
        billing.ghi_nhan_thanh_toan(iid, du_lieu, user)
        tb = 'Đã ghi nhận thanh toán %s đồng.' % du_lieu.amount
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    except sqlite3.Error as e:
        tb, loi = '', 'Không ghi nhận được thanh toán: %s' % e
    return _ve(request, duong_dan, loi=loi, thong_bao=tb)