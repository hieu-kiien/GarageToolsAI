# -*- coding: utf-8 -*-
"""Quản lý tài khoản nhân viên (chỉ quản lý mới xem được)."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...core.errors import KhongTimThay
from ...models import LuuTaiKhoanInput
from ...services import auth as auth_svc
from ...services import security_matrix as sm
from ... import crud
from .deps import DauVaoKhongHopLe, doc_json, quyen, thanh_cong, trang, trang_kq

router = APIRouter(prefix='/users', tags=['api-tai-khoan'])


@router.get('')
def danh_sach(request: Request):
    quyen(request, 'user.manage')
    tr = trang(request)
    qs = request.query_params
    dong, tong = crud.danh_sach_nguoi_dung(
        tr, q=qs.get('q', '').strip(),
        vai_tro=qs.get('vai_tro', qs.get('role', '')).strip(),
        dang_hoat_dong=qs.get('dang_hoat_dong', qs.get('is_active', '')).strip(),
        sap_xep=qs.get('sap'), huong=qs.get('huong'))
    payload = trang_kq(dong, tong, tr)
    payload['vai_tro'] = sm.VAI_TRO
    return JSONResponse(payload)


@router.post('')
async def luu(request: Request):
    """Tạo mới khi `id` rỗng, cập nhật khi có `id`."""
    user = quyen(request, 'user.edit')
    du_lieu = await doc_json(request, LuuTaiKhoanInput)
    if du_lieu.id:
        if du_lieu.id == user['id']:
            # Không cho tự sửa vai trò/username qua chính mình để tránh mất quyền.
            raise DauVaoKhongHopLe('Không thể tự sửa tài khoản của chính mình.')
        auth_svc.sua_tai_khoan(du_lieu)
        return JSONResponse(thanh_cong('Đã cập nhật tài khoản.', id=du_lieu.id))
    if not du_lieu.password:
        raise DauVaoKhongHopLe('Tài khoản mới cần mật khẩu.',
                               truong={'password': ['Bắt buộc, ít nhất 8 ký tự.']})
    uid = auth_svc.tao_tai_khoan(du_lieu, du_lieu.password)
    return JSONResponse(thanh_cong('Đã thêm tài khoản.', id=uid), status_code=201)


@router.post('/{uid:int}/toggle')
def bat_tat(request: Request, uid: int):
    user = quyen(request, 'user.edit')
    if uid == user['id']:
        raise DauVaoKhongHopLe('Không thể khoá tài khoản của chính mình.')
    ban_ghi = crud.nguoi_dung_theo_id(uid)
    if ban_ghi is None:
        raise KhongTimThay('Không tìm thấy tài khoản số %d.' % uid)
    if ban_ghi['is_active']:
        auth_svc.khoa_tai_khoan(uid)
        return JSONResponse(thanh_cong('Đã khoá tài khoản.', id=uid, is_active=False))
    auth_svc.mo_tai_khoan(uid)
    return JSONResponse(thanh_cong('Đã mở tài khoản.', id=uid, is_active=True))
