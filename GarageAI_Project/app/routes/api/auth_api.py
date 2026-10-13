# -*- coding: utf-8 -*-
"""Phiên đăng nhập của giao diện React: session, login, logout, đổi mật khẩu."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...core.config import get_settings
from ...core.errors import KhongXacThuc
from ...models import DangNhapInput, DoiMatKhauInput
from ...services import auth as auth_svc
from .deps import bang_quyen, doc_json, thanh_cong, thanh_vien

router = APIRouter(prefix='/auth', tags=['api-tai-khoan'])


def _phien_response(user, *, thong_bao: str = '', status: int = 200) -> JSONResponse:
    """JSON kèm cookie phiên — FastAPI không tự gắn cookie khi trả Response."""
    s = get_settings()
    payload = {'user': thanh_vien(user), 'quyen': bang_quyen(user)}
    if thong_bao:
        payload['thong_bao'] = thong_bao
    r = JSONResponse(payload, status_code=status)
    if user is not None:
        r.set_cookie(s.SESSION_COOKIE, auth_svc.tao_phien_cho(user),
                     max_age=s.SESSION_MAX_AGE, httponly=True,
                     secure=s.SESSION_COOKIE_SECURE,
                     samesite=s.SESSION_COOKIE_SAMESITE, path='/')
    return r


@router.get('/session')
async def phien_hien_tai(request: Request):
    """Gọi ngay khi tải trang: trả về người dùng + bảng quyền hoặc user=null."""
    user = auth_svc.nguoi_dung_hien_tai(request)
    if user is None:
        return JSONResponse({'user': None, 'quyen': {}})
    return JSONResponse({'user': thanh_vien(user), 'quyen': bang_quyen(user)})


@router.post('/login')
async def dang_nhap(request: Request):
    du_lieu = await doc_json(request, DangNhapInput)
    user = auth_svc.dang_nhap(request, du_lieu)      # ném 401 nếu sai
    return _phien_response(user, thong_bao='Xin chào %s.' % user['full_name'])


@router.post('/logout')
async def dang_xuat(request: Request):
    s = get_settings()
    r = JSONResponse(thanh_cong('Đã đăng xuất.'))
    r.delete_cookie(s.SESSION_COOKIE, path='/')
    return r


@router.post('/password')
async def doi_mat_khau(request: Request):
    user = auth_svc.nguoi_dung_hien_tai(request)
    if user is None:
        raise KhongXacThuc('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')
    du_lieu = await doc_json(request, DoiMatKhauInput)
    auth_svc.doi_mat_khau(user, du_lieu)             # ném 401 nếu sai mật khẩu cũ
    s = get_settings()
    r = JSONResponse(thanh_cong('Đã đổi mật khẩu. Vui lòng đăng nhập lại.'))
    r.delete_cookie(s.SESSION_COOKIE, path='/')
    return r
