# -*- coding: utf-8 -*-
"""Thông báo một lần cho người dùng.

Nguyên nhân lỗi ở phiên bản trước: các route chuyển hướng kèm `?thong_bao=...`
trên URL nhưng không trang nào đọc lại, nên thông báo biến mất. Cách sạch hơn
là lưu thông báo vào cookie đã ký, chỉ dùng một lần rồi xoá, đồng thời đưa vào
mọi lần render template mà không cần từng route tự truyền.

Giao diện mới chỉ cần hiển thị `{{ flash.loi }}` và `{{ flash.thong_bao }}`.
Với ứng dụng gọi bằng JSON, server còn gửi thêm header `X-Flash-Error` /
`X-Flash-Message`.
"""
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass

from itsdangerous import BadSignature, URLSafeSerializer

from .config import get_settings

COOKIE_FLASH = 'garage_flash'
_COOKIE_MAX_AGE = 60


@dataclass(frozen=True)
class Flash:
    loi: str = ''
    thong_bao: str = ''

    @property
    def rong(self) -> bool:
        return not self.loi and not self.thong_bao


_flash_dang_doc: ContextVar[Flash | None] = ContextVar('flash_dang_doc', default=None)


def _serializer() -> URLSafeSerializer:
    return URLSafeSerializer(get_settings().SECRET_KEY, salt='garage.flash.v1')


def _clean(text: str | None) -> str:
    """Thông báo phải là chữ đơn giản, không kẽ giấy, không chèn mã."""
    if not text:
        return ''
    t = str(text).strip()
    if len(t) > 500:
        t = t[:497] + '...'
    # Cắt ký tự điều khiển, giữ nguyên chữ tiếng Việt.
    return ''.join(ch for ch in t if ch == '\n' or ord(ch) >= 32)


def tao_flash(*, loi: str = '', thong_bao: str = '') -> Flash:
    return Flash(loi=_clean(loi), thong_bao=_clean(thong_bao))


def ghi(response, flash: Flash) -> None:
    """Đính thông báo vào response để mang sang lần tải trang kế tiếp."""
    if flash.rong:
        return
    from urllib.parse import quote

    from .config import get_settings
    s = get_settings()
    response.set_cookie(
        COOKIE_FLASH, _serializer().dumps({'e': flash.loi, 'm': flash.thong_bao}),
        max_age=_COOKIE_MAX_AGE, httponly=True,
        secure=s.SESSION_COOKIE_SECURE, samesite=s.SESSION_COOKIE_SAMESITE,
        path='/',
    )
    # HTTP header chỉ mang được ký tự latin-1, nên tiếng Việt bắt buộc phải mã
    # hoá phần trăm trước khi đặt vào header. Client tự giải mã bằng
    # decodeURIComponent.
    if flash.loi:
        response.headers['X-Flash-Error'] = quote(flash.loi, safe='')
    if flash.thong_bao:
        response.headers['X-Flash-Message'] = quote(flash.thong_bao, safe='')


def doc(request) -> Flash:
    """Lấy thông báo đang chờ; giá trị chỉ có hiệu lực một lần."""
    da_doc = _flash_dang_doc.get()
    if da_doc is not None:
        return da_doc
    token = request.cookies.get(COOKIE_FLASH)
    if not token:
        rong = Flash()
        _flash_dang_doc.set(rong)
        return rong
    try:
        du_lieu = _serializer().loads(token)
        flash = tao_flash(loi=du_lieu.get('e', ''), thong_bao=du_lieu.get('m', ''))
    except (BadSignature, Exception):
        flash = Flash()
    _flash_dang_doc.set(flash)
    return flash


def xoa(response, *, co_cookie: bool = True) -> None:
    _flash_dang_doc.set(None)
    if co_cookie:
        response.delete_cookie(COOKIE_FLASH, path='/')


def bat_dau_request() -> None:
    """Đặt lại bộ nhớ tạm trước mỗi request (middleware gọi)."""
    _flash_dang_doc.set(None)


def chuyen_huong(request, duong_dan: str, *, loi: str = '', thong_bao: str = '',
                 status: int = 303):
    """Tạo chuyển hướng kèm thông báo, không còn dùng query string."""
    from fastapi.responses import RedirectResponse
    r = RedirectResponse(duong_dan, status_code=status)
    ghi(r, tao_flash(loi=loi, thong_bao=thong_bao))
    return r