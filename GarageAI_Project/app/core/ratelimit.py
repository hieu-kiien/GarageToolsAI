# -*- coding: utf-8 -*-
"""Giới hạn tần suất theo cửa sổ trượt.

Dùng cấu trúc trong bộ nhớ của tiến trình, đủ dùng cho ứng dụng một tiến trình.
Khi triển khai nhiều worker cần thay bằng kho đếm dùng chung (Redis), nên phần
đọc/ghi được gom vào hai hàm `_tang` và `_xoa` để thay thế dễ dàng.

Thuật toán: cửa sổ trượt theo giây, đếm số mốc thời gian nằm trong cửa sổ.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from .errors import VuotGioiHan


class GioiHanTanSuat:
    def __init__(self, gioi_han: int, cua_so_giay: int = 60) -> None:
        self.gioi_han = max(1, gioi_han)
        self.cua_so = max(1, cua_so_giay)
        self._dem = defaultdict(deque)
        self._lock = threading.Lock()

    def cho_phep(self, khoa: str) -> tuple[bool, int]:
        """Kiểm tra và GHI NHẬN một lượt dùng. Trả (cho phép, số giây còn phải chờ)."""
        return self._quyet_dinh(khoa, ghi=True)

    def con_cho_phep(self, khoa: str) -> tuple[bool, int]:
        """Chỉ kiểm tra, KHÔNG ghi nhận — dùng khi cần xem trước có vượt ngưỡng
        không mà vẫn cho phép thao tác hợp lệ đi qua."""
        return self._quyet_dinh(khoa, ghi=False)

    def _quyet_dinh(self, khoa: str, *, ghi: bool) -> tuple[bool, int]:
        gio = time.monotonic()
        with self._lock:
            hang = self._dem[khoa]
            while hang and gio - hang[0] >= self.cua_so:
                hang.popleft()
            if len(hang) >= self.gioi_han:
                return False, max(1, int(self.cua_so - (gio - hang[0])) + 1)
            if ghi:
                hang.append(gio)
            return True, 0

    def _xoa(self) -> None:
        """Dọn khoá không còn hoạt động để bộ nhớ không phình."""
        gio = time.monotonic()
        with self._lock:
            for khoa in [k for k, q in self._dem.items() if not q or gio - q[-1] > self.cua_so * 2]:
                del self._dem[khoa]

    def xoa(self) -> None:
        self._xoa()

    def quyet_dinh(self, khoa: str) -> None:
        ok, cho = self.cho_phep(khoa)
        if not ok:
            self._xoa()
            raise VuotGioiHan(
                'Bạn thao tác quá nhanh. Vui lòng thử lại sau %d giây.' % cho)


# Bộ giới hạn dùng chung cho từng nhóm chức năng.
#
# Nguyên tắc đặt ngưỡng: cả một văn phòng có thể nằm sau một địa chỉ IP dùng
# chung (NAT, Wi-Fi công ty), nên giới hạn theo IP không được chặn oang những
# nhân viên hợp lệ. Ngưỡng thắt chặt đặt theo *tài khoản bị thử sai*, vì đó mới
# là thứ cần chặn (dò mật khẩu).
from .config import get_settings as _get_settings
_s = _get_settings()
_DEM_DI_CHUC_THEO_IP = GioiHanTanSuat(300, 60)     # 300 lần/phút mọi trang
_DEM_DANG_NHAP_IP = GioiHanTanSuat(60, 60)        # 60 lần đăng nhập/phút mỗi IP
_DEM_THU_SAI = GioiHanTanSuat(5, 900)             # 5 lần sai / 15 phút mỗi tài khoản
_DEM_AI = GioiHanTanSuat(_s.AI_RATE_LIMIT, _s.AI_RATE_WINDOW)  # bấm nút Chạy AI
_DEM_GHI = GioiHanTanSuat(60, 60)                 # thao tác ghi dữ liệu


def dia_chi_ip(request) -> str:
    # Không tin X-Forwarded-For trừ khi đã cấu hình proxy tin cậy; mặc định
    # dùng địa chỉ peer mà ASGI server nhận được.
    client = request.client
    return client.host if client else 'unknown'


def kiem_tra_chung(request) -> None:
    _DEM_DI_CHUC_THEO_IP.quyet_dinh('ip:' + dia_chi_ip(request))


def kiem_tra_dang_nhap(request, username: str) -> None:
    """Chặn trước nếu tài khoản này vừa bị thử sai quá nhiều lần.

    Chỉ **xem** ngưỡng của tài khoản, không ghi nhận ở đây: một lần đăng nhập
    đúng không được tính vào ngân sách "thử sai", nếu không nhân viên đăng nhập
    nhiều lần trong ngày sẽ bị khoá oang.
    """
    if username:
        ok, cho = _DEM_THU_SAI.con_cho_phep('thu-sai:' + username.lower())
        if not ok:
            _xoa_dem()
            raise VuotGioiHan(
                'Tài khoản này đang tạm khoá do quá nhiều lần đăng nhập sai. '
                'Vui lòng thử lại sau %d giây hoặc liên hệ quản lý.' % cho)
    _DEM_DANG_NHAP_IP.quyet_dinh('login-ip:' + dia_chi_ip(request))


def _xoa_dem() -> None:
    for b in (_DEM_DI_CHUC_THEO_IP, _DEM_DANG_NHAP_IP, _DEM_THU_SAI, _DEM_AI, _DEM_GHI):
        b.xoa()


def ghi_nhan_that_bai(username: str) -> None:
    """Ghi nhận một lần đăng nhập sai, dùng để khoá tạm tài khoản đó."""
    if username:
        _DEM_THU_SAI.quyet_dinh('thu-sai:' + username.lower())


def kiem_tra_ai(request) -> None:
    _DEM_AI.quyet_dinh('ai:' + dia_chi_ip(request))


def kiem_tra_ghi(request) -> None:
    _DEM_GHI.quyet_dinh('ghi:' + dia_chi_ip(request))


def dat_lai() -> None:
    for b in (_DEM_DI_CHUC_THEO_IP, _DEM_DANG_NHAP_IP, _DEM_THU_SAI,
              _DEM_AI, _DEM_GHI):
        b._dem.clear()