# -*- coding: utf-8 -*-
"""Lớp lỗi của tầng nghiệp vụ.

Tầng dữ liệu và tầng nghiệp vụ không cần biết HTTP là gì: chúng chỉ ném ra
loại lỗi mô tả được "vì sao không làm được". Tầng HTTP của ứng dụng bắt các
lỗi này và dịch sang mã trạng thái + thông báo cho người dùng.
"""
from __future__ import annotations


class AppError(Exception):
    """Lỗi nghiệp vụ có thể đưa thẳng thông điệp ra cho người dùng."""

    status_code = 400
    ma = 'loi_nghiep_vu'

    def __init__(self, thong_diep: str, *, truong: str | None = None) -> None:
        super().__init__(thong_diep)
        self.thong_diep = thong_diep
        self.truong = truong          # tên ô form sai, để tô đỏ đúng chỗ


class KhongXacThuc(AppError):
    status_code = 401
    ma = 'chua_xac_thuc'


class KhongCoQuyen(AppError):
    status_code = 403
    ma = 'khong_co_quyen'

    def __init__(self, thong_diep: str = 'Bạn không có quyền thực hiện thao tác này.') -> None:
        super().__init__(thong_diep)


class KhongHopLeCsrf(AppError):
    """Mã CSRF sai hoặc thiếu, hoặc nguồn gửi đi không cùng gốc.

    Đây là cách trình duyệt hoặc trang lạ gửi yêu cầu thay người dùng, nên
    trả về 403 như mọi lỗi bị từ chối quyền.
    """

    status_code = 403
    ma = 'csrf_khong_hop_le'


class KhongTimThay(AppError):
    status_code = 404
    ma = 'khong_tim_thay'

    def __init__(self, thong_diep: str = 'Không tìm thấy dữ liệu cần xử lý.') -> None:
        super().__init__(thong_diep)


class XungDdot(AppError):
    """Trùng dữ liệu đã có (biển số, tài khoản, ...)."""

    status_code = 409
    ma = 'trung_du_lieu'

    def __init__(self, thong_diep: str, *, truong: str | None = None) -> None:
        super().__init__(thong_diep, truong=truong)


class SaiQuyTac(AppError):
    """Vi phạm quy tắc nghiệp vụ nhưng không phải do người dùng nhập sai."""

    status_code = 409
    ma = 'sai_quy_tac'


class VuotGioiHan(AppError):
    status_code = 429
    ma = 'vuot_gioi_han'


class LoiDichVu(AppError):
    """Lỗi từ dịch vụ ngoài (AI, mạng...). Thông điệp đã an toàn cho người dùng."""

    status_code = 502
    ma = 'loi_dich_vu'


class LoiKhongMoDuoc(AppError):
    """Lỗi hệ thống không lộ chi tiết ra ngoài."""

    status_code = 500
    ma = 'loi_he_thong'

    def __init__(self, thong_diep: str = 'Hệ thống gặp sự cố. Vui lòng thử lại.') -> None:
        super().__init__(thong_diep)