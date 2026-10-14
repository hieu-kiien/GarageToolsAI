# -*- coding: utf-8 -*-
"""Đăng nhập, đăng xuất và quản lý tài khoản."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Form, Request

from ..core import flash
from ..core.errors import AppError, KhongXacThuc
from ..models import DangNhapInput, DoiMatKhauInput, LuuTaiKhoanInput
from ..core.pagination import doc_trang
from .. import crud
from ..services import auth as svc
from . import LoiForm, du_lieu_form, paged, render

router = APIRouter(tags=['tai-khoan'])


@router.get('/accounts/login')
def trang_dang_nhap(request: Request, next: str = '/'):
    if svc.nguoi_dung_hien_tai(request):
        return flash.chuyen_huong(request, duong_dan_noi_bo(next))
    return render(request, 'dang_nhap.html', {'next': duong_dan_noi_bo(next),
                                              'loi_dang_nhap': None})


@router.post('/accounts/login')
async def dang_nhap(request: Request,
                    username: str = Form(...),
                    password: str = Form(...),
                    next: str = Form('/')):
    try:
        du_lieu = du_lieu_form(
            {'username': username, 'password': password, 'next': next},
            DangNhapInput)
        user = svc.dang_nhap(request, du_lieu)
    except LoiForm as e:
        return render(request, 'dang_nhap.html',
                      {'loi_dang_nhap': ' · '.join(e.danh_sach_loi), 'next': duong_dan_noi_bo(next)},
                      trang_thai=400)
    except KhongXacThuc as e:
        return render(request, 'dang_nhap.html',
                      {'loi_dang_nhap': str(e), 'next': duong_dan_noi_bo(next)},
                      trang_thai=401)

    from ..core.config import get_settings
    s = get_settings()
    r = flash.chuyen_huong(request, du_lieu.next,
                           thong_bao='Xin chào %s.' % user['full_name'])
    r.set_cookie(s.SESSION_COOKIE, svc.tao_phien_cho(user),
                 max_age=s.SESSION_MAX_AGE, httponly=True,
                 secure=s.SESSION_COOKIE_SECURE, samesite=s.SESSION_COOKIE_SAMESITE,
                 path='/')
    return r


def duong_dan_noi_bo(next: str) -> str:
    """Chỉ giữ đường dẫn nội bộ.

    `https://kẻ-tấn-công/...` hoặc `//kẻ-tấn-công` đều là chuyển hướng ra
    ngoài, dùng để đánh cắp phiên bằng kỹ thuật open redirect.
    """
    v = (next or '').strip()
    if not v.startswith('/') or v.startswith('//') or '\\' in v:
        return '/'
    return v


@router.post('/accounts/logout')
def dang_xuat(request: Request):
    from ..core.config import get_settings
    s = get_settings()
    r = flash.chuyen_huong(request, '/accounts/login', thong_bao='Đã đăng xuất.')
    r.delete_cookie(s.SESSION_COOKIE, path='/')
    return r


@router.post('/accounts/password')
async def doi_mat_khau(request: Request,
                        mat_khau_cu: str = Form(...),
                        mat_khau_moi: str = Form(...)):
    user = svc.yeu_cau_dang_nhap(request)
    if user is None:
        return flash.chuyen_huong(request, '/accounts/login')
    try:
        svc.doi_mat_khau(user, du_lieu_form(
            {'mat_khau_cu': mat_khau_cu, 'mat_khau_moi': mat_khau_moi},
            DoiMatKhauInput))
    except LoiForm as e:
        return flash.chuyen_huong(request, '/dashboard', loi=' · '.join(e.danh_sach_loi))
    except AppError as e:
        return flash.chuyen_huong(request, '/dashboard', loi=str(e))
    from ..core.config import get_settings
    s = get_settings()
    r = flash.chuyen_huong(request, '/accounts/login',
                           thong_bao='Đã đổi mật khẩu. Vui lòng đăng nhập lại.')
    r.delete_cookie(s.SESSION_COOKIE, path='/')
    return r


# ---------------------------------------------------------------------------
# Danh sách tài khoản (chỉ quản lý)
# ---------------------------------------------------------------------------
@router.get('/users')
def danh_sach_tai_khoan(request: Request):
    user = svc.yeu_cau_quyen(request, 'user.manage')
    if user is None:
        return flash.chuyen_huong(request, '/accounts/login')
    trang = doc_trang(request)
    qs = request.query_params
    dong, tong = crud.danh_sach_nguoi_dung(
        trang, q=qs.get('q', '').strip(), vai_tro=qs.get('vai_tro', '').strip(),
        dang_hoat_dong=qs.get('dang_hoat_dong', '').strip(),
        sap_xep=qs.get('sap'), huong=qs.get('huong'))
    return render(request, 'danh_sach.html', paged({}, 'dong', dong, tong, trang) | {
        'ten': 'users', 'tieu_de': 'Tài khoản nhân viên',
        'mo_ta': 'Danh sách tài khoản và vai trò phân quyền',
        'q': qs.get('q', ''), 'loc_role': qs.get('vai_tro', ''),
        'cot': [('username', 'Tên đăng nhập'), ('full_name', 'Họ và tên'),
                ('role', 'Vai trò'), ('is_active', 'Đang hoạt động')],
        'quyen_xem': 'user.manage', 'quyen_sua': 'user.edit',
    })


@router.post('/users/save')
async def luu_tai_khoan(request: Request):
    user = svc.yeu_cau_quyen(request, 'user.edit')
    if user is None:
        return flash.chuyen_huong(request, '/accounts/login')
    form = await request.form()
    try:
        du_lieu = du_lieu_form(form, LuuTaiKhoanInput)
        if du_lieu.id:
            if du_lieu.id == user['id']:
                return flash.chuyen_huong(
                    request, '/users',
                    loi='Không thể tự sửa vai trò hoặc trạng thái tài khoản đang đăng nhập.')
            svc.sua_tai_khoan(du_lieu, du_lieu.password)
            tb = 'Đã cập nhật tài khoản.'
        else:
            if not du_lieu.password:
                raise LoiForm({'password': ['Mật khẩu phải có ít nhất 8 ký tự.']}, {})
            svc.tao_tai_khoan(du_lieu, du_lieu.password)
            tb = 'Đã thêm tài khoản.'
    except LoiForm as e:
        return flash.chuyen_huong(request, '/users', loi=' · '.join(e.danh_sach_loi))
    except AppError as e:
        return flash.chuyen_huong(request, '/users', loi=str(e))
    except sqlite3.Error as e:
        return flash.chuyen_huong(request, '/users', loi='Không lưu được: %s' % e)
    return flash.chuyen_huong(request, '/users', thong_bao=tb)


@router.post('/users/{uid}/toggle')
async def bat_tai_khoan(request: Request, uid: int):
    user = svc.yeu_cau_quyen(request, 'user.edit')
    if user is None:
        return flash.chuyen_huong(request, '/accounts/login')
    if uid == user['id']:
        return flash.chuyen_huong(request, '/users',
                                  loi='Không thể tự khoá tài khoản của mình.')
    ban_ghi = crud.nguoi_dung_theo_id(uid)
    if ban_ghi is None:
        return flash.chuyen_huong(request, '/users', loi='Không tìm thấy tài khoản.')
    if ban_ghi['is_active']:
        svc.khoa_tai_khoan(uid)
        return flash.chuyen_huong(request, '/users', thong_bao='Đã khoá tài khoản.')
    svc.mo_tai_khoan(uid)
    return flash.chuyen_huong(request, '/users', thong_bao='Đã mở tài khoản.')