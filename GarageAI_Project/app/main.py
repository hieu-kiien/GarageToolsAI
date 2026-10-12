# -*- coding: utf-8 -*-
"""Ứng dụng GarageTools AI.

`create_app()` lắp các phần theo đúng thứ tự:

1. Cấu hình và ghi log.
2. Middleware bảo mật: giới hạn tải, giới hạn tần suất, CSRF, đặt mã request.
3. Bộ xử lý lỗi — mọi lỗi đều ra thông điệp tiếng Việt, không lộ stack trace.
4. Gắn các router.

Những thứ **không** làm ở đây: SQL, quy tắc nghiệp vụ, dựng HTML. Chúng thuộc
`crud`, `services` và `routes`.
"""
from __future__ import annotations

import secrets
import sqlite3
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .core import flash as flash_mod
from .core import ratelimit
from .core.config import get_settings
from .core.errors import (AppError, KhongCoQuyen, KhongHopLeCsrf, KhongXacThuc,
                          KhongTimThay,
                           LoiKhongMoDuoc)
from .core.logging import (cau_hinh, get as get_logger, log_thong_tap,
                           request_id_var, user_id_var)
from .core.security import CSRF_FIELD, CSRF_COOKIE, kiem_tra_csrf, kiem_tra_origin

settings = get_settings()
cau_hinh(settings.DEBUG)
log = get_logger('app')

#: Các đường dẫn không cần mã CSRF: GET/HEAD không đổi trạng thái, và chính
#: trang đăng nhập chưa có phiên để đối chiếu.
KHONG_CAN_CSRF = ('/accounts/login', '/health', '/healthz', '/readyz', '/static')


def _can_bypass(url: str) -> bool:
    return any(url == p or url.startswith(p + '/') for p in KHONG_CAN_CSRF)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        docs_url=None, redoc_url=None, openapi_url=None,
        max_content_length=settings.MAX_CONTENT_LENGTH)

    app.mount('/static', StaticFiles(directory=str(settings.STATIC_DIR)),
              name='static')

    if settings.ALLOWED_HOSTS:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

    # --- 1. mã request + đo thời gian ------------------------------------
    @app.middleware('http')
    async def gan_ma_request(request: Request, call_next):
        rid = request.headers.get('x-request-id') or uuid.uuid4().hex[:16]
        token = request_id_var.set(rid)
        user_id_var.set('-')
        bat_dau = time.perf_counter()
        flash_mod.bat_dau_request()
        try:
            response = await call_next(request)
        except Exception:
            log_thong_tap(sys_exc_info()[1], 'middleware')
            raise
        finally:
            request_id_var.reset(token)
        response.headers['X-Request-ID'] = rid
        response.headers['X-Response-Time-ms'] = '%.1f' % ((time.perf_counter() - bat_dau) * 1000)
        return response

    # --- 2. giới hạn tần suất -------------------------------------------
    @app.middleware('http')
    async def gioi_han_tan_suat(request: Request, call_next):
        try:
            ratelimit.kiem_tra_chung(request)
        except AppError as e:
            if request.url.path.startswith(('/health', '/healthz', '/readyz')):
                return await call_next(request)
            return _tra_loi(e, request)
        return await call_next(request)

# --- 3. CSRF ----------------------------------------------------------
    @app.middleware("http")
    async def bao_ve_csrf(request: Request, call_next):
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE') \
                and not _can_bypass(request.url.path):
            token_form = request.headers.get('x-csrf-token')
            if token_form is None:
                # Đọc thân yêu cầu để lấy mã trong biểu mẫu, rồi **phát lại**
                # luồng đọc cho route phía sau. Không có bước này thì route sẽ
                # nhận một thân rỗng vì thân đã bị đọc hết ở middleware.
                body = await request.body()
                request._receive = _phat_lai(body)
                token_form = _token_trong_form(body)
            if not kiem_tra_csrf(token_form, request.cookies.get(CSRF_COOKIE)):
                return _tra_loi(
                    KhongHopLeCsrf('Phiên bảo mật không hợp lệ hoặc đã hết hạn. '
                                   'Vui lòng tải lại trang và thử lại.'), request)
            if not kiem_tra_origin(request):
                return _tra_loi(
                    KhongHopLeCsrf('Nguồn yêu cầu không hợp lệ.'), request)
        return await call_next(request)

    # --- 4. đầu vào, đầu ra ---------------------------------------------
    @app.middleware("http")
    async def ve_bia_an(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'same-origin')
        response.headers.setdefault('Permissions-Policy',
                                    'geolocation=(), microphone=(), camera=()')
        response.headers.setdefault('Cache-Control', 'no-store')
        if settings.IS_PRODUCTION:
            response.headers.setdefault('Strict-Transport-Security',
                                        'max-age=31536000; includeSubDomains')
        return response

    _dang_ky_bat_loi(app)
    _dang_ky_router(app)
    return app


def _phat_lai(body: bytes):
    """Tạo lại hàm nhận dữ liệu thân yêu cầu đã bị đọc trước đó."""
    async def receive():
        return {'type': 'http.request', 'body': body, 'more_body': False}
    return receive


def _token_trong_form(body: bytes) -> str | None:
    """Bóc đúng trường `csrf_token` khỏi thân form, không phân tích nhầm giá trị
    của ô khác cũng tên trùng."""
    if not body:
        return None
    try:
        from urllib.parse import parse_qsl
        for k, v in parse_qsl(body.decode('utf-8', 'replace'), keep_blank_values=True):
            if k == 'csrf_token':
                return v
    except Exception:
        return None
    return None


def sys_exc_info():
    import sys
    return sys.exc_info()


def _tra_loi(e: AppError, request: Request):
    if _muon_json(request):
        return JSONResponse({'loi': e.ma, 'thong_diep': e.thong_diep},
                            status_code=e.status_code)
    from .routes import render
    return render(request, 'loi.html',
                  {'ma': e.status_code, 'tieu_de': _tieu_de(e.status_code),
                   'noi_dung': e.thong_diep}, trang_thai=e.status_code)


def _muon_json(request: Request) -> bool:
    if request.url.path.startswith('/api/'):
        return True
    accept = request.headers.get('accept', '')
    return 'application/json' in accept and 'text/html' not in accept


_TIEU_DE = {400: 'Yêu cầu không hợp lệ', 401: 'Chưa đăng nhập',
            403: 'Không có quyền truy cập', 404: 'Không tìm thấy trang',
            409: 'Dữ liệu xung đột', 429: 'Thao tác quá nhanh',
            500: 'Hệ thống gặp sự cố', 502: 'Dịch vụ ngoài không phản hồi'}


def _tieu_de(ma: int) -> str:
    return _TIEU_DE.get(ma, 'Đã xảy ra lỗi')


def _dang_ky_bat_loi(app: FastAPI) -> None:
    """Mọi lỗi đều đi qua đây, đảm bảo không lộ chi tiết kỹ thuật ra ngoài."""

    @app.exception_handler(AppError)
    async def _app_error(request: Request, e: AppError):
        if e.status_code >= 500:
            log_thong_tap(e, request.url.path)
        return _tra_loi(e, request)

    @app.exception_handler(sqlite3.IntegrityError)
    async def _loi_csql(request: Request, e: sqlite3.IntegrityError):
        """Lỗi ràng buộc CSDL phải thành thông báo, không phải lỗi 500."""
        log_thong_tap(e, request.url.path)
        tb = str(e)
        if 'FOREIGN KEY' in tb:
            msg = 'Dữ liệu tham chiếu không tồn tại hoặc không còn được phép sử dụng.'
        elif 'UNIQUE' in tb:
            msg = 'Giá trị đã tồn tại, không thể lặp lại.'
        elif 'CHECK' in tb:
            msg = 'Dữ liệu không hợp lệ so với ràng buộc của hệ thống.'
        else:
            msg = 'Thao tác không thực hiện được.'
        return _tra_loi(AppError(msg), request)

    @app.exception_handler(sqlite3.OperationalError)
    async def _loi_sqlite(request: Request, e: sqlite3.OperationalError):
        log_thong_tap(e, request.url.path)
        if 'locked' in str(e) or 'busy' in str(e):
            return _tra_loi(
                AppError('Cơ sở dữ liệu đang bận. Vui lòng thử lại sau ít phút.'),
                request)
        return _tra_loi(AppError('Lỗi cơ sở dữ liệu, thao tác không hoàn tất.'),
                        request)

    @app.exception_handler(ValueError)
    async def _loi_gia_tri(request: Request, e: ValueError):
        """Dữ liệu gửi lên sai kiểu — báo lỗi thân thiện, không lộ stack trace."""
        log.info('Dữ liệu đầu vào không hợp lệ: %s', e)
        return _tra_loi(AppError('Dữ liệu gửi lên không hợp lệ: %s' % e), request)

    @app.exception_handler(Exception)
    async def _loi_khong_do(request: Request, e: Exception):
        log_thong_tap(e, 'khong_luu_loai')
        return _tra_loi(LoiKhongMoDuoc(), request)


def _dang_ky_router(app: FastAPI) -> None:
    from .routes import (auth, orders, parties, quotations, stock, system,
                         warranties)
    # Thứ tự không quan trọng vì không route nào chồng lấn nhau nữa, nhưng
    # giữ nhóm theo nghiệp vụ cho dễ đọc.
    app.include_router(system.router)
    app.include_router(auth.router)
    app.include_router(parties.router)
    app.include_router(orders.router)
    app.include_router(quotations.router)
    app.include_router(stock.router)
    app.include_router(warranties.router)


app = create_app()