# -*- coding: utf-8 -*-
"""Nghiệp vụ ba chức năng AI và Human Review.

Lớp này nối AI Gateway với nghiệp vụ:
* kiểm tra quyền trước khi gọi,
* giới hạn tần suất để không đốt tiền khoá API,
* dịch lỗi kỹ thuật của dịch vụ ngoài thành thông báo tiếng Việt,
* lưu kết quả ở trạng thái PENDING kèm người đã chạy để truy vết được.

Nguyên tắc bất di bất dịch: **AI không phải nguồn của dữ liệu nghiệp vụ.**
AI không thêm hạng mục, không lập hoá đơn, không tự tính lại tổng tiền.
"""
from __future__ import annotations

import json

from .. import crud
from ..ai_gateway import AiError
from ..ai_gateway import bao_gia_nhap as _bao_gia_nhap
from ..ai_gateway import giai_thich_dich_vu as _giai_thich
from ..ai_gateway import tom_tat_lich_su as _tom_tat
from ..core import ratelimit
from ..core.db import fetch_all, fetch_one, transaction
from ..core.errors import KhongTimThay, LoiDichVu, SaiQuyTac, VuotGioiHan
from ..core.money import utc_now
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


def danh_sach_ket_qua(trang, *, trang_thai: str = '') -> tuple[list[dict], int]:
    dieu_kien, tham_so = ['1=1'], []
    if trang_thai:
        dieu_kien.append('a.review_status = ?')
        tham_so.append(trang_thai)
    return crud.truy_van_danh_sach(
        'ai_results',
        cot=('a.id', 'a.kind', 'a.repair_order_id', 'a.output_text', 'a.is_valid',
             'a.review_status', 'a.reviewed_by', 'a.reviewed_at', 'a.created_at',
             'v.plate', 'us.full_name AS nguoi_duyet'),
        dieu_kien=' AND '.join(dieu_kien), tham_so=tham_so, trang=trang)


def ket_qua_gan_nhat(limit: int = 5) -> list[dict]:
    """Kết quả mới nhất cho trang trợ lý AI.

    `ai_results.repair_order_id` tham chiếu `repair_orders`, nên phải đi qua
    `repair_orders` rồi mới tới `vehicles`.
    """
    return fetch_all(
        'SELECT a.id, a.kind, a.output_text, a.review_status, a.is_valid,'
        ' a.created_at, v.plate'
        ' FROM ai_results a'
        ' LEFT JOIN repair_orders r ON r.id = a.repair_order_id'
        ' LEFT JOIN vehicles v ON v.id = r.vehicle_id'
        ' ORDER BY a.id DESC LIMIT ?', (limit,))


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