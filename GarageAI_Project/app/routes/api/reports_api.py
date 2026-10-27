# -*- coding: utf-8 -*-
"""Báo cáo, lịch sử thao tác và các giá trị chọn sẵn cho giao diện.

`/api/lookups` chỉ trả dữ liệu tra cứu (danh mục, danh sách id + tên, bảng
nhãn) — không chứa thông tin tài khoản hay số điện thoại ở ngoài danh mục.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ... import crud
from ...services import security_matrix as sm
from ...services import reports
from ...services.stock import LY_DO
from .deps import quyen, trang, trang_kq

router = APIRouter(tags=['api-bao-cao'])

#: Tên báo cáo -> hàm dịch vụ (khớp `BAO_CAO` của route HTML).
BAO_CAO = {
    'doanh-thu': reports.bao_cao_doanh_thu,
    'dich-vu': reports.bao_cao_dich_vu,
    'phu-tung': reports.bao_cao_phu_tung,
    'khach-hang': reports.bao_cao_khach_hang,
    'trang-thai': reports.bao_cao_trang_thai,
}


@router.get('/reports/{kind}')
def bao_cao(request: Request, kind: str):
    quyen(request, 'report.view')
    ham = BAO_CAO.get(kind)
    if ham is None:
        from ...core.errors import KhongTimThay
        raise KhongTimThay('Không có báo cáo "%s".' % kind)
    return JSONResponse({'kind': kind, 'loai': list(BAO_CAO), 'dong': ham()})


@router.get('/reports')
def danh_sach_loai(request: Request):
    quyen(request, 'report.view')
    return JSONResponse({'loai': list(BAO_CAO)})


@router.get('/history')
def lich_su(request: Request):
    user = quyen(request, 'history.view')
    tr = trang(request)
    q = request.query_params.get('q', '').strip()
    dong, tong = reports.lich_su(tr, q=q, user=user)
    return JSONResponse(trang_kq(dong, tong, tr))


@router.get('/lookups')
def gia_tri_chon(request: Request):
    """Giá trị tra cứu cho mọi form: chỉ id + tên, không kèm thông tin bí mật."""
    user = quyen(request, 'customer.view')
    return JSONResponse({
        'khach_hang': crud.lua_chon_khach(),
        'xe': crud.lua_chon_xe(),
        'dich_vu': crud.lua_chon_dich_vu(),
        'phu_tung': crud.lua_chon_phu_tung(),
        'ky_thuat_vien': crud.lua_chon_ky_thuat_vien(),
        'phieu': crud.fetch_all_phieu(user=user),
        'vai_tro': sm.VAI_TRO,
        'trang_thai': sm.TEN_TRANG_THAI,
        'chuyen_trang_thai': sm.CHUYEN_TRANG_THAI,
        'hinh_thuc': sm.TEN_HINH_THUC,
        'ly_do_kho': LY_DO,
    })


@router.get('/lookups/{ten}')
def gia_tri_chon_mot(request: Request, ten: str):
    user = quyen(request, 'customer.view')
    du_lieu = {
        'khach_hang': lambda: crud.lua_chon_khach(),
        'xe': lambda: crud.lua_chon_xe(),
        'dich_vu': lambda: crud.lua_chon_dich_vu(),
        'phu_tung': lambda: crud.lua_chon_phu_tung(),
        'ky_thuat_vien': lambda: crud.lua_chon_ky_thuat_vien(),
        'phieu': lambda: crud.fetch_all_phieu(user=user),
    }.get(ten)
    if du_lieu is None:
        from ...core.errors import KhongTimThay
        raise KhongTimThay('Không có bảng tra cứu "%s".' % ten)
    return JSONResponse({'dong': du_lieu()})
