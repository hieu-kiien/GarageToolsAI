# -*- coding: utf-8 -*-
"""Nghiệp vụ ba chức năng AI và Human Review.

Lớp này nối AI Gateway với nghiệp vụ:
* kiểm tra quyền trước khi gọi,
* giới hạn tần suất để không đốt tiền khoá API,
* dịch lỗi kỹ thuật của dịch vụ ngoài thành thông báo tiếng Việt,
* lưu kết quả ở trạng thái PENDING kèm người đã chạy để truy vết được.

Nguyên tắc bất di bất dịch: **AI không phải nguồn của dữ liệu nghiệp vụ.**
AI không tự thêm hạng mục vào phiếu, không lập hoá đơn, không tự tính lại tổng tiền.
"""
from __future__ import annotations

import json

from .. import crud
from ..ai_gateway import AiError
from ..ai_gateway import bao_gia_nhap as _bao_gia_nhap
from ..ai_gateway import chat_voi_ai as _chat_voi_ai
from ..ai_gateway import giai_thich_dich_vu as _giai_thich
from ..ai_gateway import tom_tat_lich_su as _tom_tat
from ..core import ratelimit
from ..core.db import fetch_all, fetch_one, transaction
from ..core.errors import KhongTimThay, LoiDichVu, SaiQuyTac
from ..core.money import utc_now
from ..models import HangMucBaoGiaInput, TaoBaoGiaInput
from . import quotations as quotations_svc
from .security_matrix import TEN_TRANG_THAI

#: Loại kết quả -> nhãn tiếng Việt
TEN_KINH = {'history': 'AI01 · Tóm tắt lịch sử',
            'explain': 'AI02 · Giải thích dịch vụ',
            'quote': 'AI03 · Báo giá nháp'}


def _chay(ham, *args, **kwargs) -> dict:
    """Bọc lời gọi AI: giới hạn tần suất và dịch lỗi ra thông báo an toàn."""
    try:
        r = ham(*args, **kwargs)
    except AiError as e:
        raise LoiDichVu(str(e))
    except KhongTimThay:
        # Bản ghi không tồn tại là lỗi 404 của nghiệp vụ — giữ nguyên mã HTTP.
        raise
    except Exception as e:                       # lỗi không lường trước
        from ..core.logging import log_thong_tap
        log_thong_tap(e, 'goi_ai')
        raise LoiDichVu('Dịch vụ AI không phản hồi. Vui lòng thử lại sau.')
    if not isinstance(r, dict) or not r.get('output_text'):
        raise LoiDichVu('Dịch vụ AI trả về nội dung rỗng.')
    return r


def chay_ai(request, user, kind: str, *args) -> int:
    ratelimit.kiem_tra_ai(request)
    if kind == 'history':
        r = _chay(_tom_tat, *args)
    elif kind == 'explain':
        r = _chay(_giai_thich, *args)
    elif kind == 'quote':
        if user is not None:
            from .orders import _kiem_tra_quyen_thao_tac
            _kiem_tra_quyen_thao_tac(user, args[0])
        r = _chay(_bao_gia_nhap, *args)
    else:
        raise SaiQuyTac('Chức năng AI không hợp lệ.')
    return luu_ket_qua(r, user)


def luu_ket_qua(r: dict, user) -> int:
    """Lưu kết quả. Luôn sinh ra ở trạng thái PENDING và không có người duyệt."""
    try:
        input_json = r.get('input_json') or '{}'
        json.loads(input_json)                     # phải là JSON hợp lệ
    except (ValueError, TypeError):
        input_json = json.dumps({'provider': 'khong ro'}, ensure_ascii=False)
    with transaction() as c:
        return int(c.execute(
            'INSERT INTO ai_results (kind, repair_order_id, input_json, output_text,'
            ' is_valid, review_status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (r['kind'], r.get('repair_order_id'), input_json, r['output_text'],
             1 if r.get('is_valid') else 0, 'PENDING', utc_now())).lastrowid)


def _bo_sung_meta(dong: list[dict]) -> list[dict]:
    """Trích xuất biển số xe, tên dịch vụ, mô hình AI và hạng mục đề xuất từ `input_json`."""
    for d in dong:
        raw = d.pop('input_json', None)
        meta = {}
        if isinstance(raw, str) and raw.strip():
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    meta = parsed
            except ValueError:
                meta = {}
        if not d.get('plate') and meta.get('plate'):
            d['plate'] = meta.get('plate')
        d['vehicle_id'] = meta.get('vehicle_id')
        d['service_id'] = meta.get('service_id')
        d['service_name'] = meta.get('service_name')
        d['provider_thuc_te'] = meta.get('provider_thuc_te') or meta.get('provider')
        d['model'] = meta.get('model')
        d['fallback_used'] = bool(meta.get('fallback_used'))
        goi_y = meta.get('suggested_items')
        d['suggested_items'] = goi_y if isinstance(goi_y, list) else []
    return dong


def danh_sach_ket_qua(trang, *, trang_thai: str = '') -> tuple[list[dict], int]:
    dieu_kien, tham_so = ['1=1'], []
    if trang_thai:
        dieu_kien.append('a.review_status = ?')
        tham_so.append(trang_thai)
    dong, tong = crud.truy_van_danh_sach(
        'ai_results',
        cot=('a.id', 'a.kind', 'a.repair_order_id', 'a.input_json', 'a.output_text',
             'a.is_valid', 'a.review_status', 'a.reviewed_by', 'a.reviewed_at',
             'a.created_at', 'v.plate', 'us.full_name AS nguoi_duyet'),
        dieu_kien=' AND '.join(dieu_kien), tham_so=tham_so, trang=trang)
    return _bo_sung_meta(dong), tong


def ket_qua_gan_nhat(limit: int = 25) -> list[dict]:
    """Kết quả mới nhất cho trang trợ lý AI và các màn hình nghiệp vụ."""
    dong = fetch_all(
        'SELECT a.id, a.kind, a.repair_order_id, a.input_json, a.output_text,'
        ' a.review_status, a.is_valid, a.created_at, v.plate'
        ' FROM ai_results a'
        ' LEFT JOIN repair_orders r ON r.id = a.repair_order_id'
        ' LEFT JOIN vehicles v ON v.id = r.vehicle_id'
        ' ORDER BY a.id DESC LIMIT ?', (limit,))
    return _bo_sung_meta(dong)


def duyet_ket_qua(result_id: int, quyet_dinh: str, user) -> dict:
    """Chỉ kết quả đang chờ duyệt mới được quyết định, và không duyệt lại được."""
    if quyet_dinh not in ('APPROVED', 'REJECTED'):
        raise SaiQuyTac('Quyết định không hợp lệ.')
    with transaction() as c:
        kq = c.execute('SELECT review_status FROM ai_results WHERE id = ?',
                       (result_id,)).fetchone()
        if kq is None:
            raise KhongTimThay('Không tìm thấy kết quả AI số %d.' % result_id)
        if kq['review_status'] != 'PENDING':
            raise SaiQuyTac(
                'Kết quả này đã ở trạng thái %s nên không duyệt lại được.'
                % TEN_TRANG_THAI.get(kq['review_status'], kq['review_status']))
        c.execute(
            'UPDATE ai_results SET review_status = ?, reviewed_by = ?,'
            ' reviewed_at = ? WHERE id = ? AND review_status = ?',
            (quyet_dinh, user['id'], utc_now(), result_id, 'PENDING'))
        # `repair_logs.repair_order_id` là NOT NULL, còn kết quả AI01/AI02 không
        # gắn với phiếu nào. Vì vậy chỉ ghi nhật ký khi có phiếu.
        phieu_id = c.execute('SELECT repair_order_id FROM ai_results WHERE id = ?',
                             (result_id,)).fetchone()[0]
        if phieu_id:
            c.execute(
                'INSERT INTO repair_logs (repair_order_id, technician_id, note)'
                ' VALUES (?, ?, ?)',
                (phieu_id, user['id'],
                 'Duyệt kết quả AI #%d: %s'
                 % (result_id, TEN_TRANG_THAI.get(quyet_dinh, quyet_dinh))))
    return {'review_status': quyet_dinh}


def tao_bao_gia_tu_ai(result_id: int, user) -> dict:
    """Chuyển kết quả AI03 (báo giá nháp) thành bản ghi Báo giá (`quotations` DRAFT)."""
    kq = fetch_one('SELECT * FROM ai_results WHERE id = ?', (result_id,))
    if kq is None:
        raise KhongTimThay('Không tìm thấy kết quả AI số %d.' % result_id)
    if kq['kind'] != 'quote' or not kq.get('repair_order_id'):
        raise SaiQuyTac('Chỉ kết quả AI03 (Báo giá nháp) gắn với phiếu sửa chữa mới tạo được báo giá.')
    if kq['review_status'] == 'REJECTED':
        raise SaiQuyTac('Kết quả AI này đã bị từ chối nên không thể dùng để lập báo giá.')

    ro_id = int(kq['repair_order_id'])
    meta = {}
    try:
        meta = json.loads(kq.get('input_json') or '{}')
    except ValueError:
        meta = {}

    goi_y = meta.get('suggested_items') if isinstance(meta.get('suggested_items'), list) else []
    if not goi_y:
        # Fallback: lấy từ hạng mục hiện có của phiếu
        items = fetch_all(
            'SELECT service_id, part_id, qty FROM repair_order_items WHERE repair_order_id = ?',
            (ro_id,))
        goi_y = [
            {
                'loai': 'dich_vu' if i.get('service_id') else 'phu_tung',
                'ma': int(i.get('service_id') or i.get('part_id')),
                'qty': int(i['qty']),
            }
            for i in items
            if i.get('service_id') or i.get('part_id')
        ]

    # Kiểm tra xem phiếu đã có báo giá nháp DRAFT đang mở chưa
    bg_mo = fetch_one(
        "SELECT id, status FROM quotations WHERE repair_order_id = ?"
        " AND status IN ('DRAFT', 'SENT', 'APPROVED') AND applied_at IS NULL"
        " ORDER BY id DESC LIMIT 1",
        (ro_id,))

    if bg_mo and bg_mo['status'] == 'DRAFT':
        qid = int(bg_mo['id'])
    else:
        qid = quotations_svc.tao_bao_gia(
            TaoBaoGiaInput(
                repair_order_id=ro_id,
                note='Khởi tạo từ đề xuất AI03 #%d' % result_id,
            ),
            user,
        )

    da_co = fetch_all(
        'SELECT service_id, part_id FROM quotation_items WHERE quotation_id = ?',
        (qid,))
    dv_co = {int(x['service_id']) for x in da_co if x.get('service_id')}
    pt_co = {int(x['part_id']) for x in da_co if x.get('part_id')}

    so_dong_them = 0
    for item in goi_y:
        if not isinstance(item, dict):
            continue
        loai = item.get('loai')
        ma = item.get('ma')
        qty = int(item.get('qty') or 1)
        if loai not in ('dich_vu', 'phu_tung') or not ma:
            continue
        if loai == 'dich_vu' and int(ma) in dv_co:
            continue
        if loai == 'phu_tung' and int(ma) in pt_co:
            continue
        try:
            quotations_svc.them_hang_muc(
                qid,
                HangMucBaoGiaInput(loai=loai, ma=int(ma), qty=max(1, qty)),
            )
            if loai == 'dich_vu':
                dv_co.add(int(ma))
            else:
                pt_co.add(int(ma))
            so_dong_them += 1
        except Exception:
            continue

    return {
        'quotation_id': qid,
        'repair_order_id': ro_id,
        'added_items': so_dong_them,
    }


def chat(request, user, messages: list[dict], *,
         vehicle_id: int | None = None,
         repair_order_id: int | None = None) -> dict:
    """Trò chuyện trực tiếp với Trợ lý AI dựa trên dữ liệu thực của xưởng."""
    ratelimit.kiem_tra_ai(request)
    if repair_order_id and user['role'] == 'TECHNICIAN':
        phieu = fetch_one('SELECT technician_id FROM repair_orders WHERE id = ?',
                          (repair_order_id,))
        if phieu is None or phieu['technician_id'] != user['id']:
            raise SaiQuyTac('Kỹ thuật viên chỉ tra cứu chuyên sâu trên phiếu được phân công cho mình.')
    try:
        return _chat_voi_ai(
            messages,
            vehicle_id=vehicle_id,
            repair_order_id=repair_order_id,
        )
    except AiError as e:
        raise LoiDichVu(str(e))
