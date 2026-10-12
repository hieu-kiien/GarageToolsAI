# -*- coding: utf-8 -*-
"""Ma trận phân quyền — nguồn duy nhất cho cả backend lẫn giao diện.

Mỗi quyền là một hằng tên; giá trị là tập các vai trò được phép. Thêm một
chức năng mới thì thêm một hằng ở đây, không sửa rải rác trong các route.
"""
from __future__ import annotations

VAI_TRO = {
    'MANAGER': 'Quản lý',
    'RECEPTIONIST': 'Lễ tân',
    'TECHNICIAN': 'Kỹ thuật viên',
    'CASHIER': 'Thu ngân',
}

QUAN_LY = {'MANAGER'}
LE_TAN_VA_QUAN_LY = {'MANAGER', 'RECEPTIONIST'}
KTE = {'MANAGER', 'TECHNICIAN'}
TAT_CA = {'MANAGER', 'RECEPTIONIST', 'TECHNICIAN', 'CASHIER'}

PERMISSIONS: dict[str, set[str]] = {
    # --- xem ---
    'dashboard.view':    TAT_CA,
    'customer.view':     TAT_CA,
    'vehicle.view':      TAT_CA,
    'appointment.view':  TAT_CA,
    'catalog.view':      TAT_CA,
    'order.view':        TAT_CA,
    'history.view':      TAT_CA,
    'report.view':       {'MANAGER', 'RECEPTIONIST'},
    'ai.history':        LE_TAN_VA_QUAN_LY,
    'ai.explain':        LE_TAN_VA_QUAN_LY,
    'ai.quote':          {'MANAGER', 'RECEPTIONIST', 'TECHNICIAN'},
    'ai.review':         QUAN_LY,
    'shop.view':         TAT_CA,
    'user.manage':       QUAN_LY,

    # --- ghi ---
    'customer.edit':     LE_TAN_VA_QUAN_LY,
    'vehicle.edit':      LE_TAN_VA_QUAN_LY,
    'appointment.edit':  LE_TAN_VA_QUAN_LY,
    'catalog.edit':      QUAN_LY,
    'order.create':      LE_TAN_VA_QUAN_LY,
    'order.progress':    KTE,
    'order.assign':      {'MANAGER', 'RECEPTIONIST'},
    'order.item':        KTE,
    'order.accept':      LE_TAN_VA_QUAN_LY,
    'quote.manage':      LE_TAN_VA_QUAN_LY,
    'quote.approve':     QUAN_LY,
    'invoice.manage':    QUAN_LY,
    'payment.record':    {'MANAGER', 'CASHIER'},
    'user.edit':         QUAN_LY,
}

#: Vai trò được sửa phiếu không cần được phân công.
PHAN_CONG_CHINH = {'MANAGER', 'RECEPTIONIST'}

#: Lợi trình chuyển trạng thái hợp lệ của phiếu sửa chữa.
CHUYEN_TRANG_THAI: dict[str, list[str]] = {
    'RECEIVED':   ['INSPECTING', 'CANCELLED'],
    'INSPECTING': ['ESTIMATING', 'CANCELLED'],
    'ESTIMATING': ['REPAIRING', 'INSPECTING', 'CANCELLED'],
    'REPAIRING':  ['COMPLETED', 'INSPECTING'],
    'COMPLETED':  [],
    'CANCELLED':  [],
}

#: Nhãn tiếng Việt dùng thống nhất trên mọi màn hình.
TEN_TRANG_THAI = {
    'RECEIVED': 'Đã tiếp nhận', 'INSPECTING': 'Đang kiểm tra',
    'ESTIMATING': 'Đang báo giá', 'REPAIRING': 'Đang sửa chữa',
    'COMPLETED': 'Đã hoàn thành', 'CANCELLED': 'Đã huỷ',
    'SCHEDULED': 'Đã đặt', 'CONFIRMED': 'Đã xác nhận', 'DONE': 'Đã hoàn thành',
    'UNPAID': 'Chưa thanh toán', 'PARTIAL': 'Thanh toán một phần', 'PAID': 'Đã thanh toán',
    'PENDING': 'Chờ duyệt', 'APPROVED': 'Đã duyệt', 'REJECTED': 'Đã từ chối',
    'RECEIVED_AI': 'Chờ duyệt',
    'DRAFT': 'Bản nháp', 'SENT': 'Đã gửi', 'EXPIRED': 'Hết hiệu lực',
}

TEN_HINH_THUC = {'CASH': 'Tiền mặt', 'CARD': 'Thẻ',
                'TRANSFER': 'Chuyển khoản', 'ZALO': 'Ví điện tử'}


def co_quyen(vai_tro: str, quyen: str) -> bool:
    """Kiểm tra quyền. Quyền lạ (gõ sai) luôn cho False, không ném lỗi."""
    return vai_tro in PERMISSIONS.get(quyen, set())


def duoc_gan_cong(user, phieu) -> bool:
    """Kỹ thuật viên chỉ được thao tác trên phiếu được phân công cho mình."""
    if not phieu:
        return False
    return int(phieu.get('technician_id') or 0) == int(user['id'])


def quyen_cua(vai_tro: str) -> list[str]:
    return sorted(q for q, v in PERMISSIONS.items() if vai_tro in v)