# -*- coding: utf-8 -*-
"""Danh mục dịch vụ và phụ tùng."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...models import DichVuInput, PhuTungInput
from ...services import catalog
from .deps import doc_json, quyen, thanh_cong, trang, trang_kq

router = APIRouter(tags=['api-danh-muc'])


def _loc(request: Request) -> dict:
    qs = request.query_params
    return {'q': qs.get('q', '').strip(),
            'dang_dung': qs.get('dang_dung', qs.get('is_active', '')).strip()}


# ---------------------------------------------------------------------------
# Dịch vụ
# ---------------------------------------------------------------------------
@router.get('/services')
def danh_sach_dich_vu(request: Request):
    quyen(request, 'catalog.view')
    tr = trang(request)
    f = _loc(request)
    dong, tong = catalog.danh_sach_dich_vu(tr, q=f['q'], dang_dung=f['dang_dung'])
    return JSONResponse(trang_kq(dong, tong, tr))


@router.post('/services')
async def tao_dich_vu(request: Request):
    quyen(request, 'catalog.edit')
    du_lieu = await doc_json(request, DichVuInput)
    new_id = catalog.luu_dich_vu(du_lieu)
    return JSONResponse(thanh_cong('Đã thêm dịch vụ.', id=new_id), status_code=201)


@router.put('/services/{sid:int}')
async def sua_dich_vu(request: Request, sid: int):
    quyen(request, 'catalog.edit')
    du_lieu = await doc_json(request, DichVuInput)
    du_lieu.id = sid
    catalog.luu_dich_vu(du_lieu)
    return JSONResponse(thanh_cong('Đã cập nhật dịch vụ.', id=sid))


@router.delete('/services/{sid:int}')
def xoa_dich_vu(request: Request, sid: int):
    quyen(request, 'catalog.edit')
    catalog.xoa_dich_vu(sid)
    return JSONResponse(thanh_cong('Đã xoá dịch vụ.', id=sid))


# ---------------------------------------------------------------------------
# Phụ tùng
# ---------------------------------------------------------------------------
@router.get('/parts')
def danh_sach_phu_tung(request: Request):
    quyen(request, 'catalog.view')
    tr = trang(request)
    f = _loc(request)
    qs = request.query_params
    dong, tong = catalog.danh_sach_phu_tung(
        tr, q=f['q'], dang_dung=f['dang_dung'],
        het_kho=qs.get('het_kho', '').strip())
    return JSONResponse(trang_kq(dong, tong, tr))


@router.post('/parts')
async def tao_phu_tung(request: Request):
    quyen(request, 'catalog.edit')
    du_lieu = await doc_json(request, PhuTungInput)
    new_id = catalog.luu_phu_tung(du_lieu)
    return JSONResponse(thanh_cong('Đã thêm phụ tùng.', id=new_id), status_code=201)


@router.put('/parts/{pid:int}')
async def sua_phu_tung(request: Request, pid: int):
    quyen(request, 'catalog.edit')
    du_lieu = await doc_json(request, PhuTungInput)
    du_lieu.id = pid
    catalog.luu_phu_tung(du_lieu)
    return JSONResponse(thanh_cong('Đã cập nhật phụ tùng.', id=pid))


@router.delete('/parts/{pid:int}')
def xoa_phu_tung(request: Request, pid: int):
    quyen(request, 'catalog.edit')
    catalog.xoa_phu_tung(pid)
    return JSONResponse(thanh_cong('Đã xoá phụ tùng.', id=pid))
