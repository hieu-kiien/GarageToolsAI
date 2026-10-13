# -*- coding: utf-8 -*-
"""Tầng API JSON — giao diện React gọi FastAPI bằng fetch.

Nguyên tắc giống tầng route HTML: **chỉ kiểm tra phiên/quyền, gọi tầng dịch
vụ, trả JSON**. Mọi quy tắc nghiệp vụ, mọi phép tính tiền, mọi lần trừ kho
đều nằm trong `services` — API không được phép tự tính lại.

Sự khác biệt với route HTML:
* lỗi trả về JSON ``{'loi': ma, 'thong_diep': ...}`` kèm mã trạng thái đúng
  (bộ xử lý lỗi ở `main.py` đã lo phần này cho đường dẫn bắt đầu bằng `/api/`);
* dữ liệu vào đọc từ thân JSON qua ``doc_json`` thay vì biểu mẫu;
* không có flash, không có chuyển hướng — giao diện tự quyết định.
"""
from __future__ import annotations

from fastapi import APIRouter

from . import (admin_api, ai_api, auth_api, billing_api, catalog_api,
               dashboard_api, meta_api, orders_api, parties_api,
               quotations_api, reports_api, stock_api, warranties_api)

#: Router gốc, gắn vào ứng dụng ở `main._dang_ky_router`.
api = APIRouter(prefix='/api')
for _m in (auth_api, meta_api, dashboard_api, orders_api, parties_api,
           catalog_api, quotations_api, stock_api, billing_api,
           warranties_api, ai_api, admin_api, reports_api):
    api.include_router(_m.router)
