# -*- coding: utf-8 -*-
"""Báo giá chính thức: tạo, thêm hạng mục, gửi, duyệt, áp dụng vào phiếu."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Form, Request

from ..core import flash
from ..core.errors import AppError
from ..core.pagination import doc_trang
from ..models import (DuyetBaoGiaInput, HangMucBaoGiaInput, TaoBaoGiaInput)
from .. import crud
from ..services import auth as auth_svc
from ..services import quotations
from . import LoiForm, du_lieu_form, paged, render

router = APIRouter(tags=['bao gia'])


def _ve(r: Request, duong_dan: str, *, loi: str = '', thong_bao: str = ''):
    return flash.chuyen_huong(r, duong_dan, loi=loi, thong_bao=thong_bao)


def _loi(e) -> str:
    if isinstance(e, LoiForm):
        return ' · '.join(e.danh_sach_loi)
    return str(e)


@router.get('/quotations')
def danh_sach_bao_gia(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'quote.manage')
    if user is None:
        return _ve(request, '/accounts/login')
    trang = doc_trang(request)
    qs = request.query_params
    dong, tong = quotations.danh_sach(
        trang, trang_thai=qs.get('trang_thai', '').strip(),
        q=qs.get('q', '').strip())
    return render(request, 'bao_gia.html', paged({}, 'dong', dong, tong, trang) | {
        'q': qs.get('q', ''), 'trang_thai': qs.get('trang_thai', ''),
        'trang_thai_list': ['DRAFT', 'SENT', 'APPROVED', 'REJECTED', 'EXPIRED'],
    })


@router.get('/quotations/new')
def form_bao_gia_moi(request: Request, order: int = 0):
    user = auth_svc.yeu_cau_quyen(request, 'quote.manage')
    if user is None:
        return _ve(request, '/accounts/login')
    if not order:
        return _ve(request, '/repair-orders',
                   loi='Cần chọn phiếu sửa chữa trước khi lập báo giá.')
    return render(request, 'bao_gia_moi.html', {'order_id': order})


@router.post('/quotations/create')
async def tao_bao_gia(request: Request, repair_order_id: str = Form(''),
                      note: str = Form(''), valid_until: str = Form('')):
    user = auth_svc.yeu_cau_quyen(request, 'quote.manage')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        du = du_lieu_form(
            {'repair_order_id': repair_order_id, 'note': note,
             'valid_until': valid_until}, TaoBaoGiaInput)
        bg_id = quotations.tao_bao_gia(du, user)
    except (LoiForm, AppError) as e:
        return _ve(request, '/repair-orders', loi=_loi(e))
    except sqlite3.Error as e:
        return _ve(request, '/repair-orders', loi='Không tạo được báo giá: %s' % e)
    return _ve(request, '/quotations/%d' % bg_id, thong_bao='Đã tạo báo giá nháp.')


@router.get('/quotations/{qid}')
def chi_tiet_bao_gia(request: Request, qid: int):
    user = auth_svc.yeu_cau_quyen(request, 'quote.manage')
    if user is None:
        return _ve(request, '/accounts/login')
    bg = quotations.chi_tiet(qid)
    return render(request, 'bao_gia_chi_tiet.html', {
        'bg': bg,
        'co_sua': bg['status'] == 'DRAFT',
        'co_gui': bg['status'] == 'DRAFT',
        'co_duyet': bg['status'] == 'SENT'
                    and auth_svc.co_the_quyen(user, 'quote.approve'),
        'co_huy': bg['status'] in ('DRAFT', 'SENT'),
        'co_ap_dung': bg['status'] == 'APPROVED'
                      and bg['phieu_status'] not in ('COMPLETED', 'CANCELLED'),
        'dich_vu': crud.lua_chon_dich_vu(),
        'phu_tung': crud.lua_chon_phu_tung(),
    })


@router.post('/quotations/{qid}/items')
async def them_hang_muc(request: Request, qid: int, loai: str = Form(''),
                        ma: str = Form(''), qty: str = Form('1')):
    user = auth_svc.yeu_cau_quyen(request, 'quote.manage')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        quotations.them_hang_muc(qid, du_lieu_form(
            {'loai': loai, 'ma': ma, 'qty': qty}, HangMucBaoGiaInput))
        tb = 'Đã thêm hạng mục vào báo giá.'
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    except sqlite3.Error as e:
        tb, loi = '', 'Không thêm được hạng mục: %s' % e
    return _ve(request, '/quotations/%d' % qid, loi=loi, thong_bao=tb)


@router.post('/quotations/{qid}/items/{iid}/remove')
async def go_hang_muc(request: Request, qid: int, iid: int):
    user = auth_svc.yeu_cau_quyen(request, 'quote.manage')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        quotations.go_hang_muc(qid, iid)
        tb = 'Đã gỡ hạng mục.'
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    return _ve(request, '/quotations/%d' % qid, loi=loi, thong_bao=tb)


@router.post('/quotations/{qid}/send')
async def gui_bao_gia(request: Request, qid: int):
    user = auth_svc.yeu_cau_quyen(request, 'quote.manage')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        quotations.gui_bao_gia(qid)
        tb = 'Đã gửi báo giá cho khách hàng.'
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    return _ve(request, '/quotations/%d' % qid, loi=loi, thong_bao=tb)


@router.post('/quotations/{qid}/review')
async def duyet_bao_gia(request: Request, qid: int, quyet_dinh: str = Form('')):
    user = auth_svc.yeu_cau_quyen(request, 'quote.approve')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        quotations.duyet_bao_gia(qid, du_lieu_form(
            {'quyet_dinh': quyet_dinh}, DuyetBaoGiaInput), user)
        tb = ('Đã duyệt báo giá.' if quyet_dinh == 'APPROVED'
              else 'Đã từ chối báo giá.')
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    return _ve(request, '/quotations/%d' % qid, loi=loi, thong_bao=tb)


@router.post('/quotations/{qid}/cancel')
async def huy_bao_gia(request: Request, qid: int):
    user = auth_svc.yeu_cau_quyen(request, 'quote.manage')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        quotations.huy_bao_gia(qid)
        tb = 'Đã huỷ báo giá.'
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    return _ve(request, '/quotations/%d' % qid, loi=loi, thong_bao=tb)


@router.post('/quotations/{qid}/apply')
async def ap_dung(request: Request, qid: int):
    user = auth_svc.yeu_cau_quyen(request, 'quote.manage')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        n = quotations.ap_dung_vao_phieu(qid, user)
        tb = 'Đã áp dụng %d dòng vào phiếu sửa chữa.' % n
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    except sqlite3.Error as e:
        tb, loi = '', 'Không áp dụng được: %s' % e
    bg = quotations.chi_tiet(qid)
    return _ve(request, '/repair-orders/%d' % bg['repair_order_id'],
               loi=loi, thong_bao=tb)
