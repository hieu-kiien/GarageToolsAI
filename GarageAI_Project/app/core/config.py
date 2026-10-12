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

#: Bảng preset nhà cung cấp AI (OpenAI-compatible chat/completions).
#: free = free tier khả dụng; key_env = biến môi trường mang khoá riêng.
AI_PROVIDERS: dict[str, dict] = {
    'mock': {
        'base': '',
        'model': '',
        'key_env': '',
        'free': True,
        'ghichu': 'Không gọi mạng — demo và kiểm thử.',
    },
    'openai': {
        'base': 'https://api.openai.com/v1',
        'model': 'gpt-4o-mini',
        'key_env': 'OPENAI_API_KEY',
        'free': False,
        'ghichu': 'Có phí. Vẫn dùng được OPENAI_API_KEY cũ.',
    },
    'groq': {
        'base': 'https://api.groq.com/openai/v1',
        'model': 'llama-3.3-70b-versatile',
        'key_env': 'GROQ_API_KEY',
        'free': True,
        'ghichu': 'Free tier tại console.groq.com — nhanh, OpenAI-compatible.',
    },
    'openrouter': {
        'base': 'https://openrouter.ai/api/v1',
        'model': 'meta-llama/llama-3.3-70b-instruct:free',
        'key_env': 'OPENROUTER_API_KEY',
        'free': True,
        'ghichu': 'openrouter.ai — model có hậu tố :free, cần credit 0đ.',
    },
    'gemini': {
        # Endpoint OpenAI-compatible của Google AI Studio.
        'base': 'https://generativelanguage.googleapis.com/v1beta/openai/',
        'model': 'gemini-2.0-flash',
        'key_env': 'GOOGLE_API_KEY',
        'free': True,
        'ghichu': 'aistudio.google.com — free tier, biến GOOGLE_API_KEY.',
    },
    # 9Router: proxy cục bộ (npm i -g 9router) gom 60+ provider + fallback free.
    # Endpoint OpenAI-compatible tại localhost:20128/v1. Key lấy từ dashboard.
    '9router': {
        'base': 'http://localhost:20128/v1',
        'model': 'my9model-free',
        'key_env': 'NINEROUTER_KEY',
        'free': True,
        'ghichu': '9router.com — cài `npm i -g 9router`, dán key dashboard '
                  'hoặc để trống nếu requireApiKey=false.',
    },
    'custom': {
        'base': '',
        'model': '',
        'key_env': 'AI_API_KEY',
        'free': False,
        'ghichu': 'Tự đặt AI_BASE_URL + AI_MODEL + AI_API_KEY.',
    },
}


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

        def truong(*keys, mac_dinh=''):
            """Đọc biến môi trường theo thứ tự ưu tiên; key rỗng = bỏ qua."""
            for k in keys:
                if not k:
                    continue
                v = env.get(k)
                if v is not None and str(v).strip() != '':
                    return str(v).strip()
            return mac_dinh

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
        # Nhà cung cấp. Mọi provider đều đi qua giao thức OpenAI-compatible
        # (chat/completions), nên chỉ khác base URL + model + khoá.
        #   mock       — không gọi mạng, dùng demo/test
        #   openai     — https://api.openai.com/v1
        #   groq       — https://api.groq.com/openai/v1   (free tier)
        #   openrouter — https://openrouter.ai/api/v1     (nhiều model :free)
        #   gemini     — Google AI Studio OpenAI-compat   (free tier)
        #   9router    — proxy cục bộ localhost:20128  (npm i -g 9router)
        #   custom     — tự đặt AI_BASE_URL + AI_API_KEY + AI_MODEL
        provider = str(val('AI_PROVIDER', 'mock')).strip().lower()
        if provider not in AI_PROVIDERS:
            raise ValueError(
                'AI_PROVIDER phải là một trong %s, nhận được %r'
                % (', '.join(sorted(AI_PROVIDERS)), provider))
        self.AI_PROVIDER: str = provider

        preset = AI_PROVIDERS.get(provider, {})
        # Khoá: ưu tiên AI_API_KEY (dùng chung), sau đó biến riêng của provider,
        # cuối cùng OPENAI_API_KEY (giữ tương thích ngược).
        self.AI_API_KEY: str = truong(
            'AI_API_KEY', preset.get('key_env', ''), 'OPENAI_API_KEY',
            'NINEROUTER_KEY', '9ROUTER_API_KEY')
        self.AI_BASE_URL: str = str(
            val('AI_BASE_URL', '') or preset.get('base', '')
        ).rstrip('/')
        self.AI_MODEL: str = str(
            val('AI_MODEL', '') or preset.get('model', '')
        ).strip()
        # Biến cũ vẫn đọc được (backward-compat).
        if not self.AI_BASE_URL:
            self.AI_BASE_URL = str(
                val('OPENAI_BASE_URL', 'https://api.openai.com/v1')).rstrip('/')
        if not self.AI_MODEL:
            self.AI_MODEL = str(val('OPENAI_MODEL', 'gpt-4o-mini')).strip()
        # Alias cũ → dùng khi cần code ngoài.
        self.OPENAI_API_KEY = self.AI_API_KEY
        self.OPENAI_MODEL = self.AI_MODEL
        self.OPENAI_BASE_URL = self.AI_BASE_URL + '/chat/completions'
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
        # 9router local thường chạy without API key (requireApiKey=false).
        khoaBat_buoc = self.AI_PROVIDER not in ('mock', '9router')
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
            if khoaBat_buoc and not self.AI_API_KEY:
                problems.append(
                    'AI_PROVIDER=%s nhưng thiếu API key (%s)'
                    % (self.AI_PROVIDER, AI_PROVIDERS[self.AI_PROVIDER].get('key_env') or 'AI_API_KEY'))
            if self.AI_PROVIDER != 'mock' and not self.AI_BASE_URL:
                problems.append('AI_PROVIDER=%s nhưng thiếu AI_BASE_URL' % self.AI_PROVIDER)
            if self.AI_PROVIDER != 'mock' and not self.AI_MODEL:
                problems.append('AI_PROVIDER=%s nhưng thiếu AI_MODEL' % self.AI_PROVIDER)
            if problems:
                raise RuntimeError(
                    'Cấu hình môi trường production không hợp lệ: ' + '; '.join(problems))
        if not self.SECRET_KEY:
            # Môi trường phát triển vẫn sinh khoá tạm để chạy được ngay.
            self.SECRET_KEY = KHOA_MAC_DINH
        # Dev/test: provider cần khoá mà không có thì hạ về mock.
        # 9router giữ nguyên — có thể chạy local không key.
        if khoaBat_buoc and not self.AI_API_KEY:
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