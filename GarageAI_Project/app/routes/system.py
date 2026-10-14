# -*- coding: utf-8 -*-
"""Dashboard, báo cáo, lịch sử, trợ lý AI và kiểm tra sức khoẻ."""
from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from ..core import flash
from ..core.db import db_san_sang, integrity_check
from ..core.errors import AppError
from ..core.pagination import doc_trang
from ..models import (AIExplainInput, AIHistoryInput, AIQuoteInput,
                      DuyetKetQuaInput)
from .. import crud
from ..services import ai as ai_svc
from ..services import auth as auth_svc
from ..services import reports
from . import LoiForm, du_lieu_form, paged, render

router = APIRouter(tags=['he thong'])


def _ve(r: Request, duong_dan: str, *, loi: str = '', thong_bao: str = ''):
    return flash.chuyen_huong(r, duong_dan, loi=loi, thong_bao=thong_bao)


# ===========================================================================
# Dashboard
# ===========================================================================
@router.get('/')
def trang_chu(request: Request):
    if auth_svc.nguoi_dung_hien_tai(request) is None:
        return _ve(request, '/accounts/login')
    return _ve(request, '/dashboard')


@router.get('/dashboard')
def dashboard(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'dashboard.view')
    if user is None:
        return _ve(request, '/accounts/login')
    return render(request, 'dashboard.html', {
        'kpi': reports.tong_quan(),
        'trang_thai': reports.phieu_theo_trang_thai(),
        'gan_nhat': reports.phieu_moi_nhat(8),
    })


# ===========================================================================
# Lịch sử và báo cáo
# ===========================================================================
@router.get('/history')
def lich_su(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'history.view')
    if user is None:
        return _ve(request, '/accounts/login')
    trang = doc_trang(request)
    q = request.query_params.get('q', '').strip()
    dong, tong = reports.lich_su(trang, q=q)
    return render(request, 'lich_su.html', paged({}, 'dong', dong, tong, trang) | {'q': q})


BAO_CAO = {
    'doanh-thu': reports.bao_cao_doanh_thu,
    'dich-vu': reports.bao_cao_dich_vu,
    'phu-tung': reports.bao_cao_phu_tung,
    'khach-hang': reports.bao_cao_khach_hang,
    'trang-thai': reports.bao_cao_trang_thai,
}


@router.get('/reports/{kind}')
def bao_cao(request: Request, kind: str):
    user = auth_svc.yeu_cau_quyen(request, 'report.view')
    if user is None:
        return _ve(request, '/accounts/login')
    ham = BAO_CAO.get(kind)
    dong = ham() if ham else []
    return render(request, 'bao_cao.html', {
        'kind': kind, 'dong': dong,
        'danh_sach_loai': list(BAO_CAO),
        'loai_bao_cao': kind if ham else 'khong-co',
    })


# ===========================================================================
# Trợ lý AI
# ===========================================================================
@router.get('/ai')
def cong_ai(request: Request):
    user = auth_svc.nguoi_dung_hien_tai(request)
    if user is None:
        return _ve(request, '/accounts/login')
    if not any(auth_svc.co_the_quyen(user, q)
               for q in ('ai.history', 'ai.explain', 'ai.quote', 'ai.review')):
        from ..core.errors import KhongCoQuyen
        raise KhongCoQuyen('Vai trò của bạn không được phép sử dụng trợ lý AI.')
    from ..core.config import get_settings
    return render(request, 'ai.html', {
        'dich_vu': crud.lua_chon_dich_vu(),
        'xe': crud.lua_chon_xe(),
        'phieu_list': crud.fetch_all_phieu() if hasattr(crud, 'fetch_all_phieu') else [],
        'ket_qua': ai_svc.ket_qua_gan_nhat(5),
        'phieu': request.query_params.get('phieu', ''),
        'provider': get_settings().AI_PROVIDER,
    })


@router.post('/ai/history')
async def chay_ai_history(request: Request, vehicle_id: str = Form('')):
    user = auth_svc.yeu_cau_quyen(request, 'ai.history')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        ai_svc.chay_ai(request, user, 'history',
                       du_lieu_form({'vehicle_id': vehicle_id}, AIHistoryInput).vehicle_id)
        tb = 'Đã tạo tóm tắt lịch sử. Kết quả đang chờ duyệt.'
    except (LoiForm, AppError) as e:
        tb, loi = '', (_loi(e))
    return _ve(request, '/ai', loi=loi, thong_bao=tb)


@router.post('/ai/explain')
async def chay_ai_explain(request: Request, service_id: str = Form('')):
    user = auth_svc.yeu_cau_quyen(request, 'ai.explain')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        ai_svc.chay_ai(request, user, 'explain',
                       du_lieu_form({'service_id': service_id}, AIExplainInput).service_id)
        tb = 'Đã tạo phần giải thích. Kết quả đang chờ duyệt.'
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    return _ve(request, '/ai', loi=loi, thong_bao=tb)


@router.post('/ai/quote')
async def chay_ai_quote(request: Request, repair_order_id: str = Form('')):
    user = auth_svc.yeu_cau_quyen(request, 'ai.quote')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        ai_svc.chay_ai(request, user, 'quote', du_lieu_form(
            {'repair_order_id': repair_order_id}, AIQuoteInput).repair_order_id)
        tb = 'Đã tạo báo giá nháp. Kết quả đang chờ duyệt.'
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    return _ve(request, '/ai', loi=loi, thong_bao=tb)


@router.get('/ai/results')
def danh_sach_ket_qua(request: Request):
    user = auth_svc.yeu_cau_quyen(request, 'ai.review')
    if user is None:
        return _ve(request, '/accounts/login')
    trang = doc_trang(request)
    tt = request.query_params.get('trang_thai', '').strip()
    dong, tong = ai_svc.danh_sach_ket_qua(trang, trang_thai=tt)
    return render(request, 'ai_duyet.html', paged({}, 'dong', dong, tong, trang) | {
        'trang_thai': tt, 'trang_thai_list': ['PENDING', 'APPROVED', 'REJECTED']})


@router.post('/ai/results/{rid}/review')
async def duyet_ket_qua(request: Request, rid: int, quyet_dinh: str = Form('')):
    user = auth_svc.yeu_cau_quyen(request, 'ai.review')
    if user is None:
        return _ve(request, '/accounts/login')
    try:
        loi = ''
        du_lieu = du_lieu_form({'quyet_dinh': quyet_dinh}, DuyetKetQuaInput)
        ai_svc.duyet_ket_qua(rid, du_lieu.quyet_dinh, user)
        tb = 'Đã ghi nhận quyết định.'
    except (LoiForm, AppError) as e:
        tb, loi = '', _loi(e)
    return _ve(request, '/ai/results', loi=loi, thong_bao=tb)


def _loi(e) -> str:
    if isinstance(e, LoiForm):
        return ' · '.join(e.danh_sach_loi)
    return str(e)


# ===========================================================================
# Kiểm tra sức khoẻ
# ===========================================================================
@router.get('/health')
@router.get('/healthz')
def healthz():
    """Sống hay chết: tiến trình còn phản hồi không."""
    from ..core.config import get_settings
    s = get_settings()
    return JSONResponse({
        'trang_thai': 'ok', 'ung_dung': s.APP_NAME, 'mo_truong': s.ENV})


@router.get('/readyz')
def readyz():
    """Sẵn sàng nhận việc: có kết nối được CSDL không."""
    from ..core.config import get_settings
    s = get_settings()
    san_sang = db_san_sang()
    return JSONResponse({
        'trang_thai': 'ok' if san_sang else 'loi',
        'co_so_du_lieu': 'ok' if san_sang else 'loi',
        'integrity': integrity_check() if san_sang else 'khong_kiem_tra_duoc',
        'ai_provider': s.AI_PROVIDER,
    }, status_code=200 if san_sang else 503)