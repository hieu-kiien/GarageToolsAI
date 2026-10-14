# -*- coding: utf-8 -*-
"""Hoá đơn và thu tiền. Tổng tiền và tổng đã thu đều do backend tính."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...models import LapHoaDonInput, ThanhToanInput
from ...services import billing
from .deps import (doc_json, quyen, quyen_mot_trong, thanh_cong, trang,
                   trang_kq)

router = APIRouter(prefix='/invoices', tags=['api-hoa-don'])


@router.get('')
def danh_sach(request: Request):
    # Thu ngân cần xem hoá đơn để ghi thu (payment.record); quản lý/lễ tân
    # xem theo báo cáo (report.view). Vẫn chặn kỹ thuật viên.
    quyen_mot_trong(request, 'report.view', 'payment.record')
    tr = trang(request)
    qs = request.query_params
    dong, tong = billing.danh_sach_hoa_don(
        tr, trang_thai=qs.get('trang_thai', qs.get('status', '')).strip(),
        q=qs.get('q', '').strip())
    return JSONResponse(trang_kq(dong, tong, tr))


@router.get('/{iid:int}')
def chi_tiet(request: Request, iid: int):
    quyen_mot_trong(request, 'report.view', 'payment.record')
    return JSONResponse({'hoa_don': billing.lay_hoa_don(iid),
                         'khoan_thu': billing.khoan_thu(iid)})


@router.post('')
async def lap_hoa_don(request: Request):
    user = quyen(request, 'invoice.manage')
    du_lieu = await doc_json(request, LapHoaDonInput)
    hd_id = billing.lap_hoa_don(du_lieu.repair_order_id, user)
    return JSONResponse(thanh_cong('Đã lập hoá đơn.', id=hd_id,
                                   hoa_don=billing.lay_hoa_don(hd_id)), status_code=201)


@router.post('/{iid:int}/payments')
async def thu_tien(request: Request, iid: int):
    user = quyen(request, 'payment.record')
    du_lieu = await doc_json(request, ThanhToanInput)
    billing.ghi_nhan_thanh_toan(iid, du_lieu, user)
    return JSONResponse(thanh_cong('Đã ghi nhận thanh toán %s đồng.' % du_lieu.amount,
                                   hoa_don=billing.lay_hoa_don(iid),
                                   khoan_thu=billing.khoan_thu(iid)), status_code=201)


@router.post('/{iid:int}/payments/{khoan_id:int}/cancel')
async def huy_khoan_thu(request: Request, iid: int, khoan_id: int):
    """Huỷ một khoản thu đã ghi nhầm (thu ngân/ql). Cập nhật lại đã thu."""
    user = quyen(request, 'payment.record')
    billing.huy_thanh_toan(iid, khoan_id, user)
    return JSONResponse(thanh_cong('Đã huỷ khoản thu.',
                                   hoa_don=billing.lay_hoa_don(iid),
                                   khoan_thu=billing.khoan_thu(iid)))
