# -*- coding: utf-8 -*-
"""Phân trang và kiểm tra đầu vào dùng chung."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

from .config import get_settings
from .errors import AppError


@dataclass(frozen=True)
class Trang:
    so_trang: int = 1
    moi_trang: int = 25

    @property
    def bat_dau(self) -> int:
        return (self.so_trang - 1) * self.moi_trang

    def clamp(self, tong_so_ban_ghi: int) -> 'Trang':
        """Ép số trang nằm trong khoảng hợp lệ sau khi biết tổng số bản ghi."""
        s = get_settings()
        toi_da = max(1, s.PAGE_SIZE_MAX)
        moi_trang = self.moi_trang if self.moi_trang >= 1 else s.PAGE_SIZE_DEFAULT
        moi_trang = min(moi_trang, toi_da)
        so_trang = self.so_trang if self.so_trang >= 1 else 1
        tong_trang = max(1, -(-int(tong_so_ban_ghi) // moi_trang))
        if so_trang > tong_trang:
            so_trang = tong_trang
        return Trang(so_trang, moi_trang)

    @property
    def tong_trang(self) -> int | None:
        return None


def doc_trang(request) -> Trang:
    """Đọc tham số truy vấn `trang` và `moi_trang`, luôn nằm trong giới hạn."""
    s = get_settings()

    def _int(name: str, mac_dinh: int) -> int:
        raw = request.query_params.get(name)
        if raw is None or raw == '':
            return mac_dinh
        try:
            return int(raw)
        except ValueError:
            return mac_dinh

    return Trang(_int('trang', 1), _int('moi_trang', s.PAGE_SIZE_DEFAULT))


def duong_dan_trang(duong_dan_cu: str, trang: int, moi_trang: int | None = None) -> str:
    """Ghép lại tham số truy vấn kèm số trang, giữ nguyên bộ lọc đang dùng."""
    sep = '&' if '?' in duong_dan_cu else '?'
    moi = {'trang': str(trang)}
    if moi_trang:
        moi['moi_trang'] = str(moi_trang)
    return '%s%s%s' % (duong_dan_cu, sep, urlencode(moi))


def cot_sap_xep(yeu_cau: str | None, cho_phep: list[str], mac_dinh: str) -> str:
    """Chỉ nhận tên cột nằm trong danh sách cho phép — chặn SQL injection
    qua mệnh đề ORDER BY, vốn không nhận tham số."""
    if not yeu_cau:
        return mac_dinh
    cot = yeu_cau.strip()
    if cot not in cho_phep:
        raise AppError('Tiêu chí sắp xếp không hợp lệ.')
    return cot


def huong_sap_xep(yeu_cau: str | None) -> str:
    return 'DESC' if (yeu_cau or '').strip().lower() in ('desc', 'giam') else 'ASC'


def escape_like(text: str) -> str:
    """Escape ký tự đặc biệt của LIKE để tìm kiếm đúng nghĩa đen.

    Nếu không escape, tìm chuỗi rỗng sẽ khớp tất cả bản ghi vì `%%` là wildcard.
    """
    return (text or '').replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def gia_tri_filter(qs, ten: str, mac_dinh: str = '') -> str:
    v = qs.get(ten)
    return v.strip() if isinstance(v, str) else mac_dinh


def so_nguyen(raw, mac_dinh=None, *, nho_nhat=None, lon_nhat=None):
    """Đọc số nguyên có kiểm tra khoảng; trả `mac_dinh` nếu sai."""
    if raw is None or raw == '':
        return mac_dinh
    try:
        v = int(str(raw).strip())
    except (TypeError, ValueError):
        return mac_dinh
    if nho_nhat is not None and v < nho_nhat:
        return mac_dinh
    if lon_nhat is not None and v > lon_nhat:
        return mac_dinh
    return v