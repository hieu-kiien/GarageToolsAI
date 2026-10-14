# -*- coding: utf-8 -*-
"""Báo giá: tạo, thêm dòng, gửi, duyệt, áp dụng vào phiếu."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...models import (DuyetBaoGiaInput, HangMucBaoGiaInput, TaoBaoGiaInput)
from ...services import quotations
from ...services.auth import co_the_quyen
from .deps import doc_json, quyen, thanh_cong, trang, trang_kq

router = APIRouter(prefix='/quotations', tags=['api-bao-gia'])


@router.get('')
def danh_sach(request: Request):
    quyen(request, 'quote.manage')
    tr = trang(request)
    qs = request.query_params
    dong, tong = quotations.danh_sach(
        tr, trang_thai=qs.get('trang_thai', qs.get('status', '')).strip(),
        q=qs.get('q', '').strip())
    return JSONResponse(trang_kq(dong, tong, tr))


@router.post('')
async def tao(request: Request):
    user = quyen(request, 'quote.manage')
    du_lieu = await doc_json(request, TaoBaoGiaInput)
    qid = quotations.tao_bao_gia(du_lieu, user)
    return JSONResponse(thanh_cong('Đã tạo báo giá nháp.', id=qid), status_code=201)


@router.get('/{qid:int}')
def chi_tiet(request: Request, qid: int):
    user = quyen(request, 'quote.manage')
    bg = quotations.chi_tiet(qid)
    return JSONResponse({
        'bao_gia': bg,
        'hang_muc': quotations.hang_muc(qid),
        # Các nút bật/tắt tính theo trạng thái + đúng quyền của người xem.
        'co_sua': bg['status'] == 'DRAFT',
        'co_gui': bg['status'] == 'DRAFT',
        'co_duyet': bg['status'] == 'SENT' and co_the_quyen(user, 'quote.approve'),
        'co_huy': bg['status'] in ('DRAFT', 'SENT'),
        # Chỉ ấn được "áp dụng" khi chưa từng áp dụng (applied_at IS NULL)
        # và phiếu đích còn nhận hạng mục.
        'co_ap_dung': (bg['status'] == 'APPROVED'
                       and not bg.get('applied_at')
                       and bg['phieu_status'] not in ('COMPLETED', 'CANCELLED')),
    })


@router.post('/{qid:int}/items')
async def them_hang_muc(request: Request, qid: int):
    quyen(request, 'quote.manage')
    du_lieu = await doc_json(request, HangMucBaoGiaInput)
    quotations.them_hang_muc(qid, du_lieu)
    return JSONResponse(thanh_cong('Đã thêm hạng mục vào báo giá.',
                                   hang_muc=quotations.hang_muc(qid),
                                   bao_gia=quotations.chi_tiet(qid)), status_code=201)


@router.post('/{qid:int}/items/{iid:int}/remove')
async def go_hang_muc(request: Request, qid: int, iid: int):
    quyen(request, 'quote.manage')
    quotations.go_hang_muc(qid, iid)
    return JSONResponse(thanh_cong('Đã gỡ hạng mục.',
                                   hang_muc=quotations.hang_muc(qid),
                                   bao_gia=quotations.chi_tiet(qid)))


@router.post('/{qid:int}/send')
async def gui(request: Request, qid: int):
    quyen(request, 'quote.manage')
    quotations.gui_bao_gia(qid)
    return JSONResponse(thanh_cong('Đã gửi báo giá cho khách hàng.',
                                   bao_gia=quotations.chi_tiet(qid)))


@router.post('/{qid:int}/review')
async def duyet(request: Request, qid: int):
    user = quyen(request, 'quote.approve')
    du_lieu = await doc_json(request, DuyetBaoGiaInput)
    quotations.duyet_bao_gia(qid, du_lieu, user)
    return JSONResponse(thanh_cong(
        'Đã duyệt báo giá.' if du_lieu.quyet_dinh == 'APPROVED'
        else 'Đã từ chối báo giá.', bao_gia=quotations.chi_tiet(qid)))


@router.post('/{qid:int}/cancel')
async def huy(request: Request, qid: int):
    quyen(request, 'quote.manage')
    quotations.huy_bao_gia(qid)
    return JSONResponse(thanh_cong('Đã huỷ báo giá.',
                                   bao_gia=quotations.chi_tiet(qid)))


@router.post('/{qid:int}/apply')
async def ap_dung(request: Request, qid: int):
    user = quyen(request, 'quote.manage')
    n = quotations.ap_dung_vao_phieu(qid, user)
    bg = quotations.chi_tiet(qid)
    return JSONResponse(thanh_cong('Đã áp dụng %d dòng vào phiếu sửa chữa.' % n,
                                   bao_gia=bg, phieu_id=bg['repair_order_id']))
