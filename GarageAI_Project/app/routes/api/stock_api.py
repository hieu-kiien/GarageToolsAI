# -*- coding: utf-8 -*-
"""Kho: sổ giao dịch, nhập, điều chỉnh, cảnh báo, đối chiếu sổ."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...models import DieuChinhTonKhoInput, NhapKhoInput
from ...services import stock
from .deps import doc_json, quyen, thanh_cong, trang, trang_kq

router = APIRouter(prefix='/stock', tags=['api-kho'])


@router.get('')
def so_kho(request: Request):
    quyen(request, 'order.view')
    tr = trang(request)
    qs = request.query_params
    part_id = qs.get('part_id', '').strip()
    dong, tong = stock.danh_sach_giao_dich(
        tr, part_id=int(part_id) if part_id.isdigit() else None,
        reason=qs.get('reason', '').strip())
    payload = trang_kq(dong, tong, tr)
    payload.update({
        'lech': stock.kiem_tra_so_sach(),
        'canh_bao': stock.hang_can_bao_hang(),
        'ly_do': stock.LY_DO,
    })
    return JSONResponse(payload)


@router.get('/audit')
def doi_chieu_so(request: Request):
    quyen(request, 'order.view')
    return JSONResponse({'lech': stock.kiem_tra_so_sach()})


@router.get('/warnings')
def canh_bao(request: Request):
    quyen(request, 'order.view')
    return JSONResponse({'canh_bao': stock.hang_can_bao_hang()})


@router.post('/receipt')
async def nhap_kho(request: Request):
    user = quyen(request, 'stock.manage')
    du_lieu = await doc_json(request, NhapKhoInput)
    stock.nhap_kho(du_lieu.part_id, du_lieu.qty, du_lieu.note or '', user)
    return JSONResponse(thanh_cong('Đã ghi nhận nhập kho.',
                                   ton_kho=stock.ton_kho_theo_part(du_lieu.part_id)),
                        status_code=201)


@router.post('/adjust')
async def dieu_chinh(request: Request):
    user = quyen(request, 'stock.manage')
    du_lieu = await doc_json(request, DieuChinhTonKhoInput)
    stock.dieu_chinh(du_lieu.part_id, du_lieu.moi, du_lieu.note or '', user)
    return JSONResponse(thanh_cong('Đã điều chỉnh tồn kho.',
                                   ton_kho=stock.ton_kho_theo_part(du_lieu.part_id)))
