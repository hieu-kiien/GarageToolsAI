# -*- coding: utf-8 -*-
"""Tiện ích dùng chung cho tầng API JSON."""
from __future__ import annotations

from typing import Type

from fastapi import Request
from pydantic import BaseModel

from .. import LoiForm, du_lieu_form
from ...core.errors import AppError, KhongCoQuyen, KhongXacThuc
from ...core.pagination import Trang, doc_trang
from ...services import auth as auth_svc
from ...services.security_matrix import PERMISSIONS, VAI_TRO, co_quyen


class DauVaoKhongHopLe(AppError):
    """Thân JSON không đúng schema Pydantic."""

    status_code = 400
    ma = 'dau_vao_khong_hop_le'

    def __init__(self, thong_diep: str, *, truong: dict | None = None) -> None:
        super().__init__(thong_diep)
        #: Lỗi theo từng trường, giao diện dùng để tô đỏ ô tương ứng.
        self.api_truong = truong or {}


def kiem_tra(model: Type[BaseModel], data: dict) -> BaseModel:
    """Kiểm tra dữ liệu đã bóc từ JSON, ném lỗi 400 kèm lỗi từng trường."""
    try:
        return du_lieu_form(data, model)
    except LoiForm as e:
        raise DauVaoKhongHopLe(' · '.join(e.danh_sach_loi), truong=e.loi) from e


async def doc_json(request: Request, model: Type[BaseModel]) -> BaseModel:
    """Đọc thân JSON rồi kiểm tra bằng đúng model Pydantic của route HTML.

    Dùng chung `du_lieu_form` nên mọi ràng buộc (khoảng dài, kiểu Literal,
    cấm trường lạ) giống hệt biểu mẫu truyền thống.
    """
    try:
        raw = await request.json()
    except Exception:
        raw = None
    if not isinstance(raw, dict):
        raise DauVaoKhongHopLe('Thân yêu cầu phải là JSON dạng đối tượng.')
    return kiem_tra(model, raw)


def nguoi_dung(request: Request):
    """Bắt buộc đã đăng nhập, nếu chưa thì ném 401 ngay."""
    user = auth_svc.nguoi_dung_hien_tai(request)
    if user is None:
        raise KhongXacThuc('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')
    return user


def quyen(request: Request, ten: str):
    """Bắt buộc đã đăng nhập **và** có quyền `ten`."""
    user = nguoi_dung(request)
    if not co_quyen(user['role'], ten):
        raise KhongCoQuyen(
            'Vai trò %s không được phép thực hiện chức năng này.'
            % VAI_TRO.get(user['role'], user['role']))
    return user


def quyen_mot_trong(request: Request, *ten: str):
    """Đăng nhập và có ít nhất một trong các quyền `ten` (OR).

    Dùng cho những màn hình vừa là "xem báo cáo" vừa là "thao tác tiền"
    (vd. thu ngân cần xem hoá đơn để ghi thu).
    """
    user = nguoi_dung(request)
    if not any(co_quyen(user['role'], t) for t in ten):
        raise KhongCoQuyen(
            'Vai trò %s không được phép thực hiện chức năng này.'
            % VAI_TRO.get(user['role'], user['role']))
    return user


def trang(request: Request) -> Trang:
    return doc_trang(request)


def trang_kq(dong: list[dict], tong: int, tr: Trang) -> dict:
    """Bao phân trang thống nhất cho mọi danh sách."""
    tr = tr.clamp(tong)
    return {
        'dong': dong,
        'tong': int(tong),
        'trang': tr.so_trang,
        'moi_trang': tr.moi_trang,
        'tong_trang': max(1, -(-int(tong) // tr.moi_trang)),
    }


def thanh_cong(thong_diep: str, **khac) -> dict:
    return {'thong_bao': thong_diep, **khac}


def bang_quyen(user) -> dict:
    """{tên quyền: bool} cho đúng người dùng — giao diện không tự suy đoán."""
    return {q: co_quyen(user['role'], q) for q in PERMISSIONS}


def thanh_vien(user) -> dict:
    """Bản ghi người dùng đưa ra cho giao diện (không có mật khẩu)."""
    if not user:
        return None
    return {
        'id': user['id'],
        'username': user['username'],
        'full_name': user['full_name'],
        'email': user.get('email'),
        'role': user['role'],
        'ten_vai_tro': VAI_TRO.get(user['role'], user['role']),
        'is_active': bool(user.get('is_active', True)),
    }
