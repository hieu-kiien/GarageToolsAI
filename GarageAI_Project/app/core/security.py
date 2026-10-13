# -*- coding: utf-8 -*-
"""Bảo mật: mật khẩu, phiên, CSRF.

Ba cơ chế tách biệt:

* **Mật khẩu** — Argon2id là lựa chọn mặc định (đề xuất của OWASP). Hàm băm
  cũ PBKDF2 vẫn xác minh được để dữ liệu đã sinh không bị vô hiệu.
* **Phiên** — cookie đã ký, chứa mã người dùng và số phiên bản. Khi đổi mật
  khẩu số phiên bản tăng nên mọi cookie cũ mất hiệu lực.
* **CSRF** — mẫu synchronizer token: cookie `HttpOnly` chứa mã ngẫu nhiên,
  mọi form POST phải gửi lại đúng mã đó. `SameSite=Lax` chỉ là lớp phụ.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .config import get_settings

# ---------------------------------------------------------------------------
# Mật khẩu
# ---------------------------------------------------------------------------
_SO_VONG_PBKDF2 = 200_000
try:                                    # argon2id là lựa chọn ưu tiên
    from argon2 import PasswordHasher
    from argon2.exceptions import (InvalidHashError, VerificationError,
                                   VerifyMismatchError)
    _HAS_ARGON2 = True
except ImportError:                     # vẫn chạy được nếu thiếu thư viện
    _HAS_ARGON2 = False

    class VerifyMismatchError(Exception):   # type: ignore[no-redef]
        """Khai báo giả để nhánh except luôn hợp lệ về cú pháp."""

_ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2) if _HAS_ARGON2 else None


@dataclass(frozen=True)
class ThongTinNguoiDung:
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    auth_version: int


def hash_password(raw: str) -> str:
    """Băm mật khẩu bằng Argon2id; tự sinh muối ngẫu nhiên cho từng tài khoản."""
    if _HAS_ARGON2:
        return _ph.hash(raw)
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', raw.encode(), salt.encode(), _SO_VONG_PBKDF2)
    return 'pbkdf2_sha256$%d$%s$%s' % (_SO_VONG_PBKDF2, salt, dk.hex())


def verify_password(raw: str, stored: str) -> bool:
    """Xác minh mật khẩu với cả hai định dạng lưu trữ.

    Luôn chạy đủ thuật toán kể cả khi tài khoản không tồn tại — xem
    `verify_dummy` — để không rò ra tài khoản nào có trong hệ thống qua độ trễ.
    """
    if not stored:
        return False
    if stored.startswith('pbkdf2_sha256$'):
        try:
            _, so_vong, salt, hex_dich = stored.split('$')
            so_vong = int(so_vong)
        except (ValueError, AttributeError):
            return False
        calc = hashlib.pbkdf2_hmac('sha256', raw.encode(), salt.encode(), so_vong)
        return hmac.compare_digest(calc.hex(), hex_dich)
    if _HAS_ARGON2:
        try:
            return _ph.verify(stored, raw)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False
        except Exception:
            return False
    return False


_HASH_BEN_DE = hash_password('khong-co-tai-khoan-nay')
_DEM_THAO_HASH = 0
import threading as _threading          # noqa: E402

_dem_lock = _threading.Lock()


def verify_dummy(raw: str) -> None:
    """Bằng mật khẩu giả để tài khoản không tồn tại tốn thời gian tương đương."""
    global _DEM_THAO_HASH
    verify_password(raw, _HASH_BEN_DE)
    with _dem_lock:
        _DEM_THAO_HASH += 1


# ---------------------------------------------------------------------------
# Phiên
# ---------------------------------------------------------------------------
def _serializer() -> URLSafeTimedSerializer:
    s = get_settings()
    return URLSafeTimedSerializer(s.SECRET_KEY, salt='garage.session.v1')


@dataclass(frozen=True)
class Phien:
    user_id: int
    auth_version: int


def tao_phien(user_id: int, auth_version: int = 1) -> str:
    return _serializer().dumps({'uid': int(user_id), 'av': int(auth_version)})


def doc_phien(token: str | None) -> Phien | None:
    if not token:
        return None
    s = get_settings()
    try:
        du_lieu = _serializer().loads(token, max_age=s.SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired, Exception):
        return None
    if not isinstance(du_lieu, dict):
        return None
    try:
        return Phien(int(du_lieu['uid']), int(du_lieu.get('av', 1)))
    except (KeyError, TypeError, ValueError):
        return None


def lam_moi_phien(token: str | None) -> str | None:
    """Chỉ tạo lại token từ token cũ còn hợp lệ (giữ phiên khi đổi tài khoản)."""
    p = doc_phien(token)
    return tao_phien(p.user_id, p.auth_version) if p else None


# ---------------------------------------------------------------------------
# CSRF — mẫu synchronizer token
# ---------------------------------------------------------------------------
CSRF_COOKIE = 'garage_csrf'
CSRF_FIELD = 'csrf_token'
_SO_BYTES = 32


def tao_csrf_token() -> str:
    return secrets.token_urlsafe(_SO_BYTES)


def kiem_tra_csrf(token_form: str | None, token_cookie: str | None) -> bool:
    if not token_form or not token_cookie:
        return False
    return hmac.compare_digest(str(token_form), str(token_cookie))


def kiem_tra_origin(request, cho_phep: list[str] | None = None) -> bool:
    """Kiểm tra Origin/Referer như lớp phòng thủ thứ hai cho CSRF.

    Cố ý **không** từ chối khi thiếu cả hai tiêu đề: mã CSRF đã là lớp bảo vệ
    chính (theo OWASP, synchronizer token là cơ chế chuẩn), còn Origin/Referer
    chỉ để bắt thêm trường hợp trình duyệt gửi sai nguồn. Nếu bắt buộc có
    Referer thì mọi client không phải trình duyệt — kể cả kiểm thử — sẽ hỏng.
    """
    for tieu_de, so_sanh in (('origin', True), ('referer', False)):
        gia_tri = request.headers.get(tieu_de)
        if not gia_tri:
            continue
        if tieu_de == 'referer':
            gia_tri = _goc(gia_tri)
        if not _cung_ten_mai(gia_tri, request.url.hostname or ''):
            return False
    return True


def _goc(url: str) -> str:
    """Lấy phần `scheme://host` từ URL đầy đủ."""
    from urllib.parse import urlparse
    u = urlparse(url)
    return '%s://%s' % (u.scheme, u.netloc)


def _cung_ten_mai(url: str, hostname: str) -> bool:
    from urllib.parse import urlparse
    u = urlparse(url)
    host = u.hostname or ''
    return host.lower() == (hostname or '').lower()
