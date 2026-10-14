# -*- coding: utf-8 -*-
"""Tiền tệ và thời gian.

Tiền trong toàn hệ thống là số nguyên (đồng). Chỗ này tập trung mọi quy tắc
làm tròn và hiển thị để không chỗ nào tự ý làm khác nhau.
"""
from __future__ import annotations

import datetime as _dt
import re
from zoneinfo import ZoneInfo

MAU_TIEN = 'đồng'
TZ = ZoneInfo('Asia/Ho_Chi_Minh')
_TIEN_RA = re.compile(r'[^\d-]')


def parse_tien(raw) -> int | None:
    """Đọc tiền từ dữ liệu người dùng nhập. Trả None nếu không phải số.

    Cho phép cả `1.500.000`, `1500000`, `1,500,000` và số âm để kiểm tra được
    cả trường hợp sai, thay vì im lặng nuốt thành 0.
    """
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return int(raw) if raw.is_integer() else None
    s = str(raw).strip()
    if not s:
        return None
    s = _TIEN_RA.sub('', s)
    if s in ('', '-', '--'):
        return None
    try:
        return int(s)
    except ValueError:
        return None


def format_tien(v) -> str:
    """1.170.000 — không kèm đơn vị, dùng trong ô bảng và thẻ số."""
    try:
        n = int(v or 0)
    except (TypeError, ValueError):
        n = 0
    return format(n, ',').replace(',', '.')


def format_tien_dong(v) -> str:
    """1.170.000 đồng — dùng ở câu thông báo cho người dùng."""
    return '%s %s' % (format_tien(v), MAU_TIEN)


def _parse_iso(s: str) -> _dt.datetime | None:
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M',
                '%Y-%m-%dT%H:%M', '%Y-%m-%d'):
        try:
            return _dt.datetime.strptime(s, fmt)
        except (ValueError, TypeError):
            continue
    return None


def format_ngay(s, khuong_doi: bool = True) -> str:
    """Hiển thị giờ Việt Nam.

    SQLite lưu mốc thời gian bằng `datetime('now')` là UTC. Nếu in thẳng sẽ
    lệch 7 tiếng so với giờ Việt Nam, nên mặc định quy đổi sang Asia/Ho_Chi_Minh.
    """
    if not s:
        return ''
    if isinstance(s, _dt.datetime):
        d = s
        if d.tzinfo is None:
            d = d.replace(tzinfo=_dt.timezone.utc)
        return d.astimezone(TZ).strftime('%d/%m/%Y %H:%M')
    dt = _parse_iso(str(s).strip())
    if dt is None:
        return str(s)
    if khuong_doi:
        dt = dt.replace(tzinfo=_dt.timezone.utc).astimezone(TZ)
    return dt.strftime('%d/%m/%Y %H:%M')


def utc_now() -> str:
    """Mốc thời gian UTC đúng định dạng các cột đang dùng trong CSDL."""
    return _dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def utc_now_local() -> str:
    return _dt.datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')