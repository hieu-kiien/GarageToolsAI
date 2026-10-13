# -*- coding: utf-8 -*-
"""Số liệu tổng quan cho trang Tổng quan — toàn bộ lấy từ `services.reports`."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...services import reports
from .deps import quyen

router = APIRouter(tags=['api-he-thong'])


@router.get('/dashboard')
def dashboard(request: Request):
    quyen(request, 'dashboard.view')
    return JSONResponse({
        'kpi': reports.tong_quan(),
        'trang_thai': reports.phieu_theo_trang_thai(),
        'gan_nhat': reports.phieu_moi_nhat(8),
        'doanh_thu': reports.bao_cao_doanh_thu(6),
    })
