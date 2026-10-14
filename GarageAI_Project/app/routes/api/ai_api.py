# -*- coding: utf-8 -*-
"""Ba chức năng AI (tóm tắt lịch sử, giải thích, báo giá nháp) và duyệt kết quả.

AI **không** phải nguồn dữ liệu nghiệp vụ: mọi kết quả lưu ở trạng thái PENDING,
phải được người có quyền `ai.review` duyệt thì mới dùng trong báo cáo/trang chủ.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...core.errors import KhongCoQuyen, KhongXacThuc
from ...models import (AIExplainInput, AIHistoryInput, AIQuoteInput, ChayAiInput,
                       DuyetKetQuaInput)
from ...services import ai as ai_svc
from ...services.ai import TEN_KINH
from ...services.auth import co_the_quyen, nguoi_dung_hien_tai
from .deps import (DauVaoKhongHopLe, doc_json, kiem_tra, quyen, thanh_cong, trang,
                   trang_kq)

router = APIRouter(prefix='/ai', tags=['api-ai'])

#: kind -> (mã quyền, model Pydantic, tên trường id cần gửi)
CA_CHAY = {
    'history': ('ai.history', AIHistoryInput, 'vehicle_id'),
    'explain': ('ai.explain', AIExplainInput, 'service_id'),
    'quote': ('ai.quote', AIQuoteInput, 'repair_order_id'),
}


@router.get('/results')
def danh_sach_ket_qua(request: Request):
    """Hàng chờ duyệt — chỉ người có `ai.review`."""
    quyen(request, 'ai.review')
    tr = trang(request)
    tt = request.query_params.get('trang_thai',
                                  request.query_params.get('status', '')).strip()
    dong, tong = ai_svc.danh_sach_ket_qua(tr, trang_thai=tt)
    payload = trang_kq(dong, tong, tr)
    payload['ten_kinh'] = TEN_KINH
    return JSONResponse(payload)


@router.get('/recent')
def ket_qua_gan_nhat(request: Request):
    """5 kết quả mới nhất — cần ít nhất một trong ba quyền AI."""
    user = nguoi_dung_hien_tai(request)
    if user is None:
        raise KhongXacThuc('Chưa đăng nhập.')
    if not any(co_the_quyen(user, ca[0]) for ca in CA_CHAY.values()):
        raise KhongCoQuyen('Bạn không có quyền dùng AI.')
    from ...core.config import get_settings
    return JSONResponse({'dong': ai_svc.ket_qua_gan_nhat(5),
                         'ten_kinh': TEN_KINH,
                         'provider': get_settings().AI_PROVIDER})


@router.post('/run')
def chay(request: Request, yeu_cau: ChayAiInput):
    """Chạy một trong ba chức năng AI, kiểm quyền theo từng chức năng.

    Route `def` (không async): thân JSON do FastAPI parse trước khi vào
    handler, phần chạy AI nặng chạy trong threadpool của Starlette nên không
    chặn event loop (ADR-5).
    """
    kind = yeu_cau.kind.strip()
    if kind not in CA_CHAY:
        raise DauVaoKhongHopLe('Chức năng AI không hợp lệ.',
                               truong={'kind': 'Phải là history, explain hoặc quote.'})
    user = quyen(request, CA_CHAY[kind][0])
    raw = yeu_cau.model_dump()
    raw.pop('kind', None)
    du_lieu = kiem_tra(CA_CHAY[kind][1], raw)
    rid = ai_svc.chay_ai(request, user, kind, getattr(du_lieu, CA_CHAY[kind][2]))
    return JSONResponse(
        thanh_cong('%s: kết quả đang chờ duyệt.' % TEN_KINH[kind], id=rid),
        status_code=201)


@router.post('/results/{rid:int}/review')
async def duyet(request: Request, rid: int):
    user = quyen(request, 'ai.review')
    du_lieu = await doc_json(request, DuyetKetQuaInput)
    kq = ai_svc.duyet_ket_qua(rid, du_lieu.quyet_dinh, user)
    return JSONResponse(thanh_cong('Đã %s kết quả AI.' % (
        'duyệt' if du_lieu.quyet_dinh == 'APPROVED' else 'từ chối'), **kq))
