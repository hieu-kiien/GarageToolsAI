# -*- coding: utf-8 -*-
"""Phiếu sửa chữa: xem, tạo, chuyển trạng thái, hạng mục, nhật ký, nghiệm thu."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...models import (DoiTrangThaiInput, NghiemThuInput, NhatKyInput,
                      PhanCongInput, TaoPhieuInput, ThemHangMucInput,
                      TiepNhanInput)
from ...services import billing, orders
from ...services.security_matrix import TEN_TRANG_THAI
from .deps import doc_json, quyen, thanh_cong, trang, trang_kq

router = APIRouter(prefix='/orders', tags=['api-phieu-sua-chua'])


@router.get('')
def danh_sach(request: Request):
    quyen(request, 'order.view')
    qs = request.query_params
    tr = trang(request)
    dong, tong = orders.danh_sach_phieu(
        tr,
        q=qs.get('q', '').strip(),
        trang_thai=qs.get('trang_thai', qs.get('status', '')).strip())
    return JSONResponse(trang_kq(dong, tong, tr))


@router.post('')
async def tao(request: Request):
    user = quyen(request, 'order.create')
    du_lieu = await doc_json(request, TaoPhieuInput)
    oid = orders.tao_phieu(du_lieu, user)
    return JSONResponse(thanh_cong('Đã tạo phiếu sửa chữa.', id=oid), status_code=201)


@router.get('/{oid:int}')
def chi_tiet(request: Request, oid: int):
    quyen(request, 'order.view')
    return JSONResponse({
        'phieu': orders.chi_tiet(oid),
        'hang_muc': orders.hang_muc(oid),
        'nhat_ky': orders.nhat_ky(oid),
        'hoa_don': orders.hoa_don_cua_phieu(oid),
        'tiep_nhan': orders.bien_ban_tiep_nhan(oid),
    })


@router.post('/{oid:int}/status')
async def doi_trang_thai(request: Request, oid: int):
    user = quyen(request, 'order.progress')
    du_lieu = await doc_json(request, DoiTrangThaiInput)
    orders.doi_trang_thai(oid, du_lieu, user)
    # Thông báo dùng đúng giá trị đã chuẩn hoá (service uppercases),
    # không in nguyên chuỗi người dùng gõ.
    ma = du_lieu.status.strip().upper()
    return JSONResponse(thanh_cong(
        'Đã chuyển sang %s.' % TEN_TRANG_THAI.get(ma, ma),
        phieu=orders.chi_tiet(oid)))


@router.post('/{oid:int}/assign')
async def phan_cong(request: Request, oid: int):
    user = quyen(request, 'order.assign')
    du_lieu = await doc_json(request, PhanCongInput)
    orders.gan_ky_thuat_vien(oid, du_lieu, user)
    return JSONResponse(thanh_cong('Đã cập nhật phân công.', phieu=orders.chi_tiet(oid)))


@router.post('/{oid:int}/items')
async def them_hang_muc(request: Request, oid: int):
    user = quyen(request, 'order.item')
    du_lieu = await doc_json(request, ThemHangMucInput)
    orders.them_hang_muc(oid, du_lieu, user)
    return JSONResponse(thanh_cong('Đã thêm hạng mục.',
                                   hang_muc=orders.hang_muc(oid),
                                   phieu=orders.chi_tiet(oid)), status_code=201)


@router.post('/{oid:int}/items/{iid:int}/remove')
async def go_hang_muc(request: Request, oid: int, iid: int):
    user = quyen(request, 'order.item')
    orders.go_hang_muc(oid, iid, user)
    return JSONResponse(thanh_cong('Đã bỏ hạng mục.',
                                   hang_muc=orders.hang_muc(oid),
                                   phieu=orders.chi_tiet(oid)))


@router.post('/{oid:int}/logs')
async def ghi_nhat_ky(request: Request, oid: int):
    user = quyen(request, 'order.progress')
    du_lieu = await doc_json(request, NhatKyInput)
    orders.them_nhat_ky(oid, du_lieu, user)
    return JSONResponse(thanh_cong('Đã ghi nhật ký.',
                                   nhat_ky=orders.nhat_ky(oid)), status_code=201)


@router.post('/{oid:int}/intake')
async def tiep_nhan(request: Request, oid: int):
    user = quyen(request, 'order.create')
    du_lieu = await doc_json(request, TiepNhanInput)
    orders.ghi_tiep_nhan(oid, du_lieu, user)
    return JSONResponse(thanh_cong('Đã ghi biên bản tiếp nhận.',
                                   tiep_nhan=orders.bien_ban_tiep_nhan(oid),
                                   phieu=orders.chi_tiet(oid)), status_code=201)


@router.post('/{oid:int}/accept')
async def nghiem_thu(request: Request, oid: int):
    user = quyen(request, 'order.accept')
    du_lieu = await doc_json(request, NghiemThuInput)
    orders.nghiem_thu(oid, du_lieu, user)
    return JSONResponse(thanh_cong('Đã nghiệm thu xe.', phieu=orders.chi_tiet(oid)))


@router.post('/{oid:int}/invoice')
def lap_hoa_don(request: Request, oid: int):
    user = quyen(request, 'invoice.manage')
    hd_id = billing.lap_hoa_don(oid, user)
    return JSONResponse(thanh_cong('Đã lập hoá đơn.', id=hd_id), status_code=201)


@router.delete('/{oid:int}')
def xoa(request: Request, oid: int):
    """Xoá phiếu trống (chưa phát sinh hoạt động). Quyền: `order.create`."""
    user = quyen(request, 'order.create')
    orders.xoa_phieu(oid, user)
    return JSONResponse(thanh_cong('Đã xoá phiếu sửa chữa.', id=oid))
