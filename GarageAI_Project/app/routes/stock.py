# -*- coding: utf-8 -*-
"""Kho: xem sổ cái, nhập, điều chỉnh, đối chiếu."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Form, Request

from ..core import flash
from ..core.errors import AppError
from ..core.pagination import doc_trang
from ..models import DieuChinhTonKhoInput, NhapKhoInput
from .. import crud
from ..services import auth as auth_svc
from ..services import stock
from . import LoiForm, du_lieu_form, paged, render

router = APIRouter(tags=['kho'])


def _ve(r: Request, duong_dan: str, *, loi: str = '', thong_bao: str = ''):
    return flash.chuyen_huong(r, duong_dan, loi=loi, thong_bao=thong_bao)


def _loi(e) -> str:
    if isinstance(e, LoiForm):
        return ' · '.join(e.danh_sach_loi)
    return str(e)


@router.get('/stock')
def danh_sach_kho(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'order.view')
    if user is None:
        return _ve(request, '/accounts/login')
    trang = doc_trang(request)
    qs = request.query_params
    part_id = qs.get('part_id', '').strip()
    reason = qs.get('reason', '').strip()
    pid = int(part_id) if part_id.isdigit() else None
    dong, tong = stock.danh_sach_giao_dich(trang, part_id=pid, reason=reason)
    lech = stock.kiem_tra_so_sach()
    canh_bao = stock.hang_can_bao_hang()
    return render(request, 'kho.html',
                  paged({}, 'dong', dong, tong, trang) | {
        'q': '', 'part_id': part_id, 'reason': reason,
        'reason_list': list(stock.LY_DO.items()),
        'lech': lech, 'canh_bao': canh_bao,
        'phu_tung': crud.lua_chon_phu_tung(),
    })


@router.post('/stock/receipt')
async def nhap_kho(request: Request, part_id: str = Form(''),
                   qty: str = Form(''), note: str = Form('')):
    user = auth_svc.yeu_cau_quyen(request, 'stock.manage')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        du = du_lieu_form({'part_id': part_id, 'qty': qty, 'note': note},
                          NhapKhoInput)
        stock.nhap_kho(du.part_id, du.qty, du.note or '', user)
    except (LoiForm, AppError) as e:
        return _ve(request, '/stock', loi=_loi(e))
    except sqlite3.Error as e:
        return _ve(request, '/stock', loi='Không nhập được kho: %s' % e)
    return _ve(request, '/stock', thong_bao='Đã ghi nhận nhập kho.')


@router.post('/stock/adjust')
async def dieu_chinh(request: Request, part_id: str = Form(''),
                     moi: str = Form(''), note: str = Form('')):
    user = auth_svc.yeu_cau_quyen(request, 'stock.manage')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        du = du_lieu_form({'part_id': part_id, 'moi': moi, 'note': note},
                          DieuChinhTonKhoInput)
        stock.dieu_chinh(du.part_id, du.moi, du.note or '', user)
    except (LoiForm, AppError) as e:
        return _ve(request, '/stock', loi=_loi(e))
    except sqlite3.Error as e:
        return _ve(request, '/stock', loi='Không điều chỉnh được: %s' % e)
    return _ve(request, '/stock', thong_bao='Đã điều chỉnh tồn kho.')
