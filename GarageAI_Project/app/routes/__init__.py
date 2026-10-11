# -*- coding: utf-8 -*-
"""Tầng HTTP.

Nguyên tắc: **route chỉ làm ba việc** — kiểm tra phiên/quyền, gọi tầng dịch vụ,
trả về trang hoặc chuyển hướng. Không có câu SQL, không có `if` nghiệp vụ.

Hai tiện ích dùng chung:
* `render()` bơm sẵn mọi thứ mọi trang cần (người dùng, thông báo, mã CSRF,
  bảng quyền) để không route nào phải tự chuẩn bị.
* `du_lieu_form()` chuyển dữ liệu biểu mẫu thành đối tượng Pydantic và biến
  lỗi thành thông báo theo từng trường.
"""
from __future__ import annotations

import functools
from typing import Type

from fastapi import Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ValidationError

from ..core import flash as flash_mod
from ..core.config import get_settings
from ..core.money import format_ngay, format_tien, format_tien_dong
from ..core.pagination import Trang, duong_dan_trang
from ..core.security import CSRF_FIELD, tao_csrf_token
from ..services.ai import TEN_KINH
from ..services.auth import co_the_quyen, nguoi_dung_hien_tai
from ..services.security_matrix import (PERMISSIONS, TEN_HINH_THUC,
                                        TEN_TRANG_THAI, VAI_TRO)

settings = get_settings()

CSRF_COOKIE_NAME = 'garage_csrf'

templates = Jinja2Templates(directory=str(settings.TEMPLATE_DIR))
templates.env.globals.update(
    format_tien=format_tien,
    format_tien_dong=format_tien_dong,
    format_ngay=format_ngay,
    vai_tro_ten=lambda r: VAI_TRO.get(r, r),
    ten_trang_thai=lambda s: TEN_TRANG_THAI.get(s, s),
    ten_hinh_thuc=lambda m: TEN_HINH_THUC.get(m, m),
    ten_kinh_ai=lambda k: TEN_KINH.get(k, k),
    PERMISSIONS=PERMISSIONS,
    duong_dan_trang=duong_dan_trang,
    CSRF_FIELD=CSRF_FIELD,
)


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------
def render(request: Request, ten_template: str, ctx: dict | None = None,
           *, trang_thai: int = 200):
    """Trả về trang HTML kèm sẵn ngữ cảnh dùng chung."""
    user = nguoi_dung_hien_tai(request)
    flash = flash_mod.doc(request)
    day_du = {
        'user': user,
        'flash': flash,
        'thong_bao': flash.thong_bao,
        'loi': flash.loi,
        'csrf_token': request.cookies.get(CSRF_COOKIE_NAME) or tao_csrf_token(),
        'quyen': {q: co_the_quyen(user, q) for q in PERMISSIONS},
        'co_quyen': co_the_quyen,
        'duong_dan_hien_tai': request.url.path,
    }
    day_du.update(ctx or {})
    response = templates.TemplateResponse(request, ten_template, day_du,
                                          status_code=trang_thai)
    # Cookie CSRF cố ý không HttpOnly: giao diện dùng fetch cần đọc để gắn
    # mã vào header. Mã chỉ dùng được kèm phiên đang đăng nhập nên vô hại.
    if not request.cookies.get(CSRF_COOKIE_NAME):
        response.set_cookie(
            CSRF_COOKIE_NAME, day_du['csrf_token'],
            max_age=settings.SESSION_MAX_AGE, httponly=False,
            secure=settings.SESSION_COOKIE_SECURE,
            samesite=settings.SESSION_COOKIE_SAMESITE, path='/')
    flash_mod.xoa(response)
    return response


# ---------------------------------------------------------------------------
# Đọc và kiểm tra biểu mẫu
# ---------------------------------------------------------------------------
class LoiForm(Exception):
    """Biểu mẫu không hợp lệ. Giữ luôn dữ liệu đã nhập để hiển thị lại."""

    def __init__(self, loi: dict[str, list[str]], du_lieu: dict) -> None:
        super().__init__('Dữ liệu biểu mẫu không hợp lệ')
        self.loi = loi
        self.du_lieu = du_lieu

    @property
    def danh_sach_loi(self) -> list[str]:
        return [m for ds in self.loi.values() for m in ds]


def _dep(msg: str) -> str:
    """Bỏ tiền tố kỹ thuật của Pydantic để thông báo tự nhiên."""
    return msg.split('Value error, ', 1)[-1]


def du_lieu_form(form, model: Type[BaseModel]) -> BaseModel:
    """Dựng đối tượng Pydantic từ biểu mẫu, ném `LoiForm` khi dữ liệu sai.

    Nhận cả `FormData` của Starlette lẫn `dict` thường, để route nào đã có sẵn
    dữ liệu dạng dict cũng dùng được chung một đường kiểm tra.
    """
    if isinstance(form, dict):
        du_lieu = {k: v for k, v in form.items() if k != CSRF_FIELD}
    else:
        du_lieu = {k: v for k, v in form.multi_items() if k != CSRF_FIELD}
    try:
        return model.model_validate(du_lieu)
    except ValidationError as e:
        loi: dict[str, list[str]] = {}
        for err in e.errors():
            truong = '.'.join(str(x) for x in err['loc']) or '_'
            loi.setdefault(truong, []).append(_dep(err.get('msg', 'Giá trị không hợp lệ.')))
        raise LoiForm(loi, du_lieu) from e


# ---------------------------------------------------------------------------
# Phân trang cho giao diện
# ---------------------------------------------------------------------------
def paged(ctx: dict, khoa_dong: str, dong: list[dict], tong: int, trang: Trang) -> dict:
    tong_trang = max(1, -(-tong // trang.moi_trang))
    ctx.update({
        khoa_dong: dong,
        'tong_so_ban_ghi': tong,
        'trang': trang,
        'tong_trang': tong_trang,
        'co_trang_truoc': trang.so_trang > 1,
        'co_trang_sau': trang.so_trang < tong_trang,
        'co_so_trang': tong_trang > 1,
        'duong_dan_trang': duong_dan_trang,
    })
    return ctx


# ---------------------------------------------------------------------------
# Ghi chú về kiểu hàm
# ---------------------------------------------------------------------------
def route_sync(func):
    """Đánh dấu route chạy đồng bộ (FastAPI đưa vào threadpool).

    Route nào chạm SQLite hay gọi HTTP đồng bộ đều phải khai báo `def`, không
    phải `async def`: hàm `async def` chạy thẳng trên event loop nên một truy
    vấn chậm sẽ chặn mọi request khác của người dùng.
    """
    func.__route_sync__ = True
    return func