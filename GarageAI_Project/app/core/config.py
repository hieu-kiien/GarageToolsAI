# -*- coding: utf-8 -*-
"""Cấu hình ứng dụng.

Mọi giá trị nhạy cảm đến từ biến môi trường hoặc tệp `.env`, không viết thẳng
trong mã nguồn. Ngoài ra kiểm tra lúc khởi động (fail fast) để ứng dụng không
bao giờ chạy bằng cấu hình mặc định ở môi trường thật.
"""
from __future__ import annotations

import os
import secrets
from functools import lru_cache
from pathlib import Path

from .money import format_tien

BASE_DIR = Path(__file__).resolve().parent.parent.parent

#: Khoá dùng cho môi trường phát triển. Ở production bắt buộc phải thay.
KHOA_MAC_DINH = 'doi-thanh-khoa-nay-truoc-khi-trien-khai-that'


class Settings:
    """Cấu hình đọc một lần từ môi trường, có kiểm tra khi khởi động."""

    def __init__(self, env: dict | None = None) -> None:
        env = dict(env or {})

        def val(key: str, mac_dinh=None):
            v = env.get(key)
            return mac_dinh if v is None or v == '' else v

        def raw(key: str):
            v = env.get(key)
            return None if v is None else str(v)

        # --- ứng dụng ---
        self.APP_NAME: str = val('APP_NAME', 'GarageTools AI')
        self.BASE_DIR: Path = BASE_DIR
        self.TEMPLATE_DIR: Path = BASE_DIR / 'app' / 'templates'
        self.STATIC_DIR: Path = BASE_DIR / 'app' / 'static'
        self.PROMPT_DIR: Path = BASE_DIR / 'config' / 'prompts'

        # --- môi trường chạy ---
        env_name = str(val('APP_ENV', 'development')).strip().lower()
        if env_name not in ('development', 'test', 'production'):
            raise ValueError(
                'APP_ENV phải là development, test hoặc production, nhận được %r' % env_name)
        self.ENV: str = env_name
        self.IS_PRODUCTION: bool = env_name == 'production'
        self.DEBUG: bool = self._bool(val('DEBUG'), default=not self.IS_PRODUCTION)

        # --- bảo mật ---
        self.SECRET_KEY: str = str(val('SECRET_KEY', '')).strip()
        self.ALLOWED_HOSTS: list[str] = [
            h.strip() for h in str(val('ALLOWED_HOSTS', '')).split(',') if h.strip()]
        self.SESSION_COOKIE: str = val('SESSION_COOKIE', 'garage_session')
        self.SESSION_MAX_AGE: int = self._int(val('SESSION_MAX_AGE'), 8 * 3600, minimum=300)
        if val('SESSION_COOKIE_SECURE') is not None:
            self.SESSION_COOKIE_SECURE: bool = self._bool(val('SESSION_COOKIE_SECURE'), True)
        else:
            self.SESSION_COOKIE_SECURE: bool = self.IS_PRODUCTION
        self.SESSION_COOKIE_SAMESITE: str = str(
            val('SESSION_COOKIE_SAMESITE', 'lax')).strip().lower()
        if self.SESSION_COOKIE_SAMESITE not in ('lax', 'strict', 'none'):
            raise ValueError('SESSION_COOKIE_SAMESITE phải là lax, strict hoặc none')

        # --- giới hạn tải ---
        self.MAX_CONTENT_LENGTH: int = self._int(
            val('MAX_CONTENT_LENGTH'), 1_048_576, minimum=1024)
        self.DB_BUSY_TIMEOUT_MS: int = self._int(
            val('DB_BUSY_TIMEOUT_MS'), 10_000, minimum=100)

        # --- phân trang ---
        self.PAGE_SIZE_DEFAULT: int = self._int(
            val('PAGE_SIZE_DEFAULT'), 25, minimum=5, maximum=200)
        self.PAGE_SIZE_MAX: int = self._int(
            val('PAGE_SIZE_MAX'), 100, minimum=5, maximum=500)
        self.PAGE_SIZE_DEFAULT = min(self.PAGE_SIZE_DEFAULT, self.PAGE_SIZE_MAX)

        # --- cơ sở dữ liệu ---
        self.DATABASE_PATH: str = str(val('DATABASE_PATH', str(BASE_DIR / 'garage.db')))
        self.SCHEMA_FILE: Path = BASE_DIR / 'database' / 'schema.sql'
        self.SEED_FILE: Path = BASE_DIR / 'database' / 'seed_data.sql'

        # --- AI ---
        provider = str(val('AI_PROVIDER', 'mock')).strip().lower()
        if provider not in ('mock', 'openai'):
            raise ValueError('AI_PROVIDER phải là mock hoặc openai, nhận được %r' % provider)
        self.AI_PROVIDER: str = provider
        self.OPENAI_API_KEY: str = str(val('OPENAI_API_KEY', '')).strip()
        self.OPENAI_MODEL: str = str(val('OPENAI_MODEL', 'gpt-4o-mini'))
        self.OPENAI_BASE_URL: str = str(
            val('OPENAI_BASE_URL', 'https://api.openai.com/v1/chat/completions')).strip()
        self.AI_TIMEOUT: float = float(val('AI_TIMEOUT', 15))
        self.AI_MAX_CONTEXT: int = self._int(val('AI_MAX_CONTEXT'), 6000, minimum=500)
        # Chống bấm nút "Chạy" liên tục làm đốt tiền khóa API.
        self.AI_RATE_LIMIT: int = self._int(val('AI_RATE_LIMIT'), 10, minimum=1)
        self.AI_RATE_WINDOW: int = self._int(val('AI_RATE_WINDOW'), 60, minimum=1)

        self._validate_startup()

    # ------------------------------------------------------------------ tiện ích
    @staticmethod
    def _bool(v, default: bool) -> bool:
        if v is None or v == '':
            return default
        return str(v).strip().lower() in ('1', 'true', 'yes', 'on', 'co')

    @staticmethod
    def _int(v, mac_dinh: int, *, minimum: int = 0, maximum: int = 10 ** 9) -> int:
        if v is None or v == '':
            return mac_dinh
        try:
            x = int(str(v).strip())
        except ValueError:
            raise ValueError('Giá trị số không hợp lệ: %r' % v)
        return max(minimum, min(x, maximum))

    def _validate_startup(self) -> None:
        """Chặn khởi động sai cấu hình thay vì chạy rồi mới lộ lỗi."""
        if self.IS_PRODUCTION:
            problems = []
            if not self.SECRET_KEY:
                problems.append('thiếu SECRET_KEY')
            elif len(self.SECRET_KEY) < 32:
                problems.append('SECRET_KEY ngắn hơn 32 ký tự')
            elif self.SECRET_KEY == KHOA_MAC_DINH:
                problems.append('SECRET_KEY vẫn để nguyên giá trị mặc định')
            if not self.ALLOWED_HOSTS:
                problems.append('thiếu ALLOWED_HOSTS')
            if not self.SESSION_COOKIE_SECURE:
                problems.append('phải bật SESSION_COOKIE_SECURE khi chạy thật')
            if self.AI_PROVIDER == 'openai' and not self.OPENAI_API_KEY:
                problems.append('AI_PROVIDER=openai nhưng thiếu OPENAI_API_KEY')
            if problems:
                raise RuntimeError(
                    'Cấu hình môi trường production không hợp lệ: ' + '; '.join(problems))
        if not self.SECRET_KEY:
            # Môi trường phát triển vẫn sinh khoá tạm để chạy được ngay.
            self.SECRET_KEY = KHOA_MAC_DINH
        if self.AI_PROVIDER == 'openai' and not self.OPENAI_API_KEY:
            self.AI_PROVIDER = 'mock'

    # ------------------------------------------------------------------ tiện ích
    @property
    def db_dir(self) -> Path:
        return Path(self.DATABASE_PATH).parent

    def format_tien(self, v) -> str:
        return format_tien(v)

    def load_prompt(self, name: str) -> str:
        p = self.PROMPT_DIR / name
        if not p.is_file():
            raise FileNotFoundError('không tìm thấy tệp prompt: %s' % p)
        return p.read_text(encoding='utf-8').strip()

    def render_prompt(self, template: str, **bien) -> str:
        out = template
        for k, v in bien.items():
            out = out.replace('{{%s}}' % k, '' if v is None else str(v))
        return out


def _nap_env() -> dict:
    try:
        from dotenv import dotenv_values
    except ImportError:
        return {}
    tep = BASE_DIR / '.env'
    if not tep.is_file():
        return {}
    return {k: v for k, v in dotenv_values(tep).items() if v is not None}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    env = _nap_env()
    env.update(os.environ)
    return Settings(env)


def tao_khoa_ngau_nhien(dodai: int = 48) -> str:
    """Sinh khoá đủ mạnh cho SECRET_KEY, dùng khi người dùng chạy lần đầu."""
    return secrets.token_urlsafe(dodai)