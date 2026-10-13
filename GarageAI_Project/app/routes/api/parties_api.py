# -*- coding: utf-8 -*-
"""Khách hàng, phương tiện và lịch hẹn."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...models import KhachHangInput, LichHenInput, PhuongTienInput
from ...services import parties
from .deps import doc_json, quyen, thanh_cong, trang, trang_kq

router = APIRouter(tags=['api-khach-xe-lich-hen'])


def _loc(request: Request) -> dict:
    qs = request.query_params
    return {'q': qs.get('q', '').strip()}


# ---------------------------------------------------------------------------
# Khách hàng
# ---------------------------------------------------------------------------
@router.get('/customers')
def danh_sach_khach(request: Request):
    quyen(request, 'customer.view')
    tr = trang(request)
    dong, tong = parties.danh_sach_khach(tr, q=_loc(request)['q'])
    return JSONResponse(trang_kq(dong, tong, tr))


@router.post('/customers')
async def tao_khach(request: Request):
    quyen(request, 'customer.edit')
    du_lieu = await doc_json(request, KhachHangInput)
    new_id = parties.luu_khach(du_lieu)
    return JSONResponse(thanh_cong('Đã thêm khách hàng.', id=new_id), status_code=201)


@router.put('/customers/{cid:int}')
async def sua_khach(request: Request, cid: int):
    quyen(request, 'customer.edit')
    du_lieu = await doc_json(request, KhachHangInput)
    du_lieu.id = cid
    parties.luu_khach(du_lieu)
    return JSONResponse(thanh_cong('Đã cập nhật khách hàng.', id=cid))


@router.delete('/customers/{cid:int}')
def xoa_khach(request: Request, cid: int):
    quyen(request, 'customer.edit')
    parties.xoa_khach(cid)
    return JSONResponse(thanh_cong('Đã xoá khách hàng.', id=cid))


# ---------------------------------------------------------------------------
# Phương tiện
# ---------------------------------------------------------------------------
@router.get('/vehicles')
def danh_sach_xe(request: Request):
    quyen(request, 'vehicle.view')
    tr = trang(request)
    qs = request.query_params
    khach = qs.get('khach') or qs.get('customer_id')
    dong, tong = parties.danh_sach_xe(
        tr, q=qs.get('q', '').strip(),
        khach=int(khach) if khach and str(khach).isdigit() else None)
    return JSONResponse(trang_kq(dong, tong, tr))


@router.post('/vehicles')
async def tao_xe(request: Request):
    quyen(request, 'vehicle.edit')
    du_lieu = await doc_json(request, PhuongTienInput)
    new_id = parties.luu_xe(du_lieu)
    return JSONResponse(thanh_cong('Đã thêm phương tiện.', id=new_id), status_code=201)


@router.put('/vehicles/{vid:int}')
async def sua_xe(request: Request, vid: int):
    quyen(request, 'vehicle.edit')
    du_lieu = await doc_json(request, PhuongTienInput)
    du_lieu.id = vid
    parties.luu_xe(du_lieu)
    return JSONResponse(thanh_cong('Đã cập nhật phương tiện.', id=vid))


@router.delete('/vehicles/{vid:int}')
def xoa_xe(request: Request, vid: int):
    quyen(request, 'vehicle.edit')
    parties.xoa_xe(vid)
    return JSONResponse(thanh_cong('Đã xoá phương tiện.', id=vid))


# ---------------------------------------------------------------------------
# Lịch hẹn
# ---------------------------------------------------------------------------
@router.get('/appointments')
def danh_sach_lich(request: Request):
    quyen(request, 'appointment.view')
    tr = trang(request)
    qs = request.query_params
    dong, tong = parties.danh_sach_lich(
        tr, trang_thai=qs.get('trang_thai', qs.get('status', '')).strip(),
        q=qs.get('q', '').strip())
    return JSONResponse(trang_kq(dong, tong, tr))


@router.post('/appointments')
async def tao_lich(request: Request):
    quyen(request, 'appointment.edit')
    du_lieu = await doc_json(request, LichHenInput)
    new_id = parties.luu_lich(du_lieu)
    return JSONResponse(thanh_cong('Đã đặt lịch hẹn.', id=new_id), status_code=201)


@router.put('/appointments/{lid:int}')
async def sua_lich(request: Request, lid: int):
    quyen(request, 'appointment.edit')
    du_lieu = await doc_json(request, LichHenInput)
    du_lieu.id = lid
    parties.luu_lich(du_lieu)
    return JSONResponse(thanh_cong('Đã cập nhật lịch hẹn.', id=lid))


@router.delete('/appointments/{lid:int}')
def xoa_lich(request: Request, lid: int):
    quyen(request, 'appointment.edit')
    parties.xoa_lich(lid)
    return JSONResponse(thanh_cong('Đã xoá lịch hẹn.', id=lid))
