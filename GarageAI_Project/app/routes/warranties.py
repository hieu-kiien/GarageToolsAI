# -*- coding: utf-8 -*-
"""Bảo hành: danh sách, tạo, huỷ."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Form, Request

from ..core import flash
from ..core.errors import AppError
from ..core.pagination import doc_trang
from ..models import TaoBaoHanhInput
from .. import crud
from ..services import auth as auth_svc
from ..services import warranties
from . import LoiForm, du_lieu_form, paged, render

router = APIRouter(tags=['bao hanh'])


def _ve(r: Request, duong_dan: str, *, loi: str = '', thong_bao: str = ''):
    return flash.chuyen_huong(r, duong_dan, loi=loi, thong_bao=thong_bao)


def _loi(e) -> str:
    if isinstance(e, LoiForm):
        return ' · '.join(e.danh_sach_loi)
    return str(e)


@router.get('/warranties')
def danh_sach_bao_hanh(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'warranty.manage')
    if user is None:
        return _ve(request, '/accounts/login')
    trang = doc_trang(request)
    qs = request.query_params
    dong, tong = warranties.danh_sach(
        trang, trang_thai=qs.get('trang_thai', '').strip(),
        q=qs.get('q', '').strip())
    return render(request, 'bao_hanh.html',
                  paged({}, 'dong', dong, tong, trang) | {
        'q': qs.get('q', ''), 'trang_thai': qs.get('trang_thai', ''),
        'trang_thai_list': list(warranties.TEN_TRANG_THAI_BAOHANH.items()),
    })


@router.get('/warranties/new')
def form_bao_hanh_moi(request: Request, order: int = 0):
    user = auth_svc.yeu_cau_quyen(request, 'warranty.manage')
    if user is None:
        return _ve(request, '/accounts/login')
    if not order:
        return _ve(request, '/repair-orders',
                   loi='Cần chọn phiếu sửa chữa trước khi lập bảo hành.')
    phieu = crud.lay_mot('repair_orders', order)
    if phieu is None:
        return _ve(request, '/repair-orders', loi='Không tìm thấy phiếu.')
    if phieu['status'] != 'COMPLETED':
        return _ve(request, '/repair-orders',
                   loi='Chỉ lập được bảo hành cho phiếu đã hoàn thành.')
    hang_muc = warranties.hang_muc_co_the_bao_hanh(order)
    return render(request, 'bao_hanh_moi.html', {
        'order_id': order, 'hang_muc': hang_muc,
    })


@router.post('/warranties/create')
async def tao_bao_hanh(request: Request, repair_order_id: str = Form(''),
                       months: str = Form(''), service_id: str = Form(''),
                       part_id: str = Form(''), start_date: str = Form(''),
                       note: str = Form('')):
    user = auth_svc.yeu_cau_quyen(request, 'warranty.manage')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        du = du_lieu_form({
            'repair_order_id': repair_order_id, 'months': months,
            'service_id': service_id or None, 'part_id': part_id or None,
            'start_date': start_date, 'note': note}, TaoBaoHanhInput)
        wid = warranties.tao_bao_hanh(du, user)
    except (LoiForm, AppError) as e:
        return _ve(request, '/warranties/new?order=%s' % repair_order_id,
                   loi=_loi(e))
    except sqlite3.Error as e:
        return _ve(request, '/warranties',
                   loi='Không lập được bảo hành: %s' % e)
    return _ve(request, '/warranties', thong_bao='Đã lập bảo hành.')


@router.post('/warranties/{wid}/cancel')
async def huy_bao_hanh(request: Request, wid: int, note: str = Form('')):
    user = auth_svc.yeu_cau_quyen(request, 'warranty.manage')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        warranties.huy_bao_hanh(wid, note, user)
    except AppError as e:
        return _ve(request, '/warranties', loi=_loi(e))
    except sqlite3.Error as e:
        return _ve(request, '/warranties', loi='Không huỷ được: %s' % e)
    return _ve(request, '/warranties', thong_bao='Đã huỷ bảo hành.')
