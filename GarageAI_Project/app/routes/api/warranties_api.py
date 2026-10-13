# -*- coding: utf-8 -*-
"""Bảo hành dịch vụ / phụ tùng của phiếu đã hoàn thành."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...core.errors import KhongTimThay
from ...models import HuyBaoHanhInput, TaoBaoHanhInput
from ...services import warranties
from .deps import DauVaoKhongHopLe, doc_json, quyen, thanh_cong, trang, trang_kq

router = APIRouter(prefix='/warranties', tags=['api-bao-hanh'])


@router.get('')
def danh_sach(request: Request):
    quyen(request, 'warranty.manage')
    tr = trang(request)
    qs = request.query_params
    dong, tong = warranties.danh_sach(
        tr, trang_thai=qs.get('trang_thai', qs.get('status', '')).strip(),
        q=qs.get('q', '').strip())
    return JSONResponse(trang_kq(dong, tong, tr))


@router.get('/eligible')
def hang_muc_co_the_bao_hanh(request: Request):
    """Hạng mục của một phiếu hoàn thành chưa có bảo hành."""
    quyen(request, 'warranty.manage')
    qs = request.query_params
    raw = qs.get('repair_order_id', qs.get('order', '')).strip()
    try:
        oid = int(raw)
    except ValueError:
        raise DauVaoKhongHopLe('Thiếu repair_order_id.',
                               truong={'repair_order_id': 'Bắt buộc.'})
    return JSONResponse({'dong': warranties.hang_muc_co_the_bao_hanh(oid)})


@router.post('')
async def tao(request: Request):
    user = quyen(request, 'warranty.manage')
    du_lieu = await doc_json(request, TaoBaoHanhInput)
    wid = warranties.tao_bao_hanh(du_lieu, user)
    return JSONResponse(thanh_cong('Đã lập bảo hành.', id=wid), status_code=201)


@router.get('/{wid:int}')
def chi_tiet(request: Request, wid: int):
    quyen(request, 'warranty.manage')
    bh = warranties.chi_tiet(wid)
    if bh is None:
        raise KhongTimThay('Không tìm thấy bảo hành số %d.' % wid)
    return JSONResponse({'bao_hanh': bh})


@router.post('/{wid:int}/cancel')
async def huy(request: Request, wid: int):
    user = quyen(request, 'warranty.manage')
    du_lieu = await doc_json(request, HuyBaoHanhInput)
    warranties.huy_bao_hanh(wid, du_lieu.note or '', user)
    return JSONResponse(thanh_cong('Đã huỷ bảo hành.',
                                   bao_hanh=warranties.chi_tiet(wid)))
