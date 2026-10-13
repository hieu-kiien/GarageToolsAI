# -*- coding: utf-8 -*-
"""Từ điển hiển thị: trạng thái, quyền, nhãn tiếng Việt.

Giao diện lấy hết nhãn và luật chuyển trạng thái từ đây nên không được phép
hard-code một bản sao thứ hai — sửa một chỗ là cả hai phía đổi theo.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...core.config import get_settings
from ...services import warranties as svc_bh
from ...services.ai import TEN_KINH
from ...services.security_matrix import (CHUYEN_TRANG_THAI, PERMISSIONS,
                                         TEN_HINH_THUC, TEN_TRANG_THAI, VAI_TRO)
from ...services.stock import LY_DO
from .deps import quyen

router = APIRouter(tags=['api-he-thong'])

#: Mức nhiên liệu khi tiếp nhận xe — nhãn hiển thị, không phải quy tắc nghiệp vụ.
MUC_NHIEU_LIEU = {
    'EMPTY': 'Rỗng', 'QUARTER': '1/4', 'HALF': '1/2',
    'THREE_QUARTER': '3/4', 'FULL': 'Đầy', 'UNKNOWN': 'Không rõ',
}

#: Trạng thái báo giá (bảng `quotations.status`).
TRANG_THAI_BAO_GIA = ['DRAFT', 'SENT', 'APPROVED', 'REJECTED', 'EXPIRED']


@router.get('/meta')
def meta(request: Request):
    user = quyen(request, 'dashboard.view')
    s = get_settings()
    return JSONResponse({
        'user': {'id': user['id'], 'role': user['role']},
        'vai_tro': VAI_TRO,
        'quyen': {k: sorted(v) for k, v in PERMISSIONS.items()},
        'trang_thai': TEN_TRANG_THAI,
        'trang_thai_phieu': list(CHUYEN_TRANG_THAI),
        'chuyen_trang_thai': CHUYEN_TRANG_THAI,
        'hinh_thuc_thanh_toan': TEN_HINH_THUC,
        'trang_thai_bao_gia': TRANG_THAI_BAO_GIA,
        'trang_thai_bao_hanh': svc_bh.TEN_TRANG_THAI_BAOHANH,
        'muc_nhien_lieu': MUC_NHIEU_LIEU,
        'ly_do_kho': LY_DO,
        'kinh_ai': TEN_KINH,
        'ai_provider': s.AI_PROVIDER,
    })
