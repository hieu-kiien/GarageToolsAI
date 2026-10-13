# -*- coding: utf-8 -*-
"""Nghiệp vụ bảo hành.

Quy tắc nghiệp vụ:
* Chỉ tạo bảo hành cho phiếu **COMPLETED** — chưa hoàn thành thì chưa có gì
  để bảo hành.
* Mỗi dòng bảo hành gắn với **đúng một hạng mục** (dịch vụ HOẶC phụ tùng),
  không bao giờ "toàn phiếu". XOR được enforce cả ở CSDL lẫn ở service.
* Một hạng mục chỉ có **một** bảo hành đang ACTIVE/TRACKED tại một thời điểm.
* `end_date` luôn do backend tính từ `start_date + months`, không nhận từ form
  — để người dùng không thể tự chọn ngày hết hạn.
"""
from __future__ import annotations

from datetime import date

from .. import crud
from ..core.db import fetch_all, fetch_one, transaction
from ..core.errors import KhongTimThay, SaiQuyTac
from ..core.pagination import Trang
from ..models import TaoBaoHanhInput
from .security_matrix import TEN_TRANG_THAI

TEN_TRANG_THAI_BAOHANH = {
    'ACTIVE': 'Còn hiệu lực', 'EXPIRED': 'Hết hạn',
    'CLAIMED': 'Đã khiếu nại', 'CANCELLED': 'Đã huỷ',
}
TEN_TRANG_THAI.update(TEN_TRANG_THAI_BAOHANH)


def _tinh_end_date(start: str, months: int) -> str:
    """Tính ngày hết hạn = start + months tháng. Start format YYYY-MM-DD."""
    try:
        d = date.fromisoformat(start)
    except ValueError:
        raise SaiQuyTac('Ngày bắt đầu không hợp lệ (cần YYYY-MM-DD).',
                        truong='start_date')
    # Cộng tháng an toàn: sang tháng có ít ngày hơn thì lấy ngày cuối tháng.
    thang = d.month - 1 + months
    nam = d.year + thang // 12
    thang = thang % 12 + 1
    import calendar
    ngay = min(d.day, calendar.monthrange(nam, thang)[1])
    return date(nam, thang, ngay).isoformat()


def _kiem_tra_trang_thai_moi(conn, repair_order_id: int, scope: str,
                             service_id, part_id) -> None:
    """Chặn khi hạng mục đã có bảo hành ACTIVE hoặc CLAIMED."""
    if scope == 'SERVICE':
        dieu_kien = 'repair_order_id = ? AND service_id = ?'
        tham_so = (repair_order_id, service_id)
    else:
        dieu_kien = 'repair_order_id = ? AND part_id = ?'
        tham_so = (repair_order_id, part_id)
    co = conn.execute(
        "SELECT id FROM warranties WHERE %s AND status IN ('ACTIVE','CLAIMED')"
        ' LIMIT 1' % dieu_kien, tham_so).fetchone()
    if co:
        raise SaiQuyTac('Hạng mục này đã có bảo hành (mã %d) đang còn hiệu lực.'
                        % co['id'])


def tao_bao_hanh(du_lieu: TaoBaoHanhInput, user) -> int:
    with transaction() as c:
        phieu = c.execute('SELECT * FROM repair_orders WHERE id = ?',
                          (du_lieu.repair_order_id,)).fetchone()
        if phieu is None:
            raise KhongTimThay('Không tìm thấy phiếu sửa chữa.')
        if phieu['status'] != 'COMPLETED':
            raise SaiQuyTac('Chỉ lập được bảo hành cho phiếu đã hoàn thành.')

        if du_lieu.service_id is not None:
            scope, sid, pid = 'SERVICE', du_lieu.service_id, None
            hang = c.execute(
                'SELECT 1 FROM repair_order_items WHERE repair_order_id = ?'
                ' AND service_id = ? LIMIT 1',
                (du_lieu.repair_order_id, sid)).fetchone()
            if hang is None:
                raise SaiQuyTac('Dịch vụ không thuộc hạng mục của phiếu này.',
                                truong='service_id')
        else:
            scope, sid, pid = 'PART', None, du_lieu.part_id
            hang = c.execute(
                'SELECT 1 FROM repair_order_items WHERE repair_order_id = ?'
                ' AND part_id = ? LIMIT 1',
                (du_lieu.repair_order_id, pid)).fetchone()
            if hang is None:
                raise SaiQuyTac('Phụ tùng không thuộc hạng mục của phiếu này.',
                                truong='part_id')

        _kiem_tra_trang_thai_moi(c, du_lieu.repair_order_id, scope, sid, pid)
        end = _tinh_end_date(du_lieu.start_date, du_lieu.months)
        khoa = int(c.execute(
            'INSERT INTO warranties (repair_order_id, scope, service_id, part_id,'
            ' months, start_date, end_date, status, note, created_by)'
            ' VALUES (?, ?, ?, ?, ?, ?, ?, \'ACTIVE\', ?, ?)',
            (du_lieu.repair_order_id, scope, sid, pid, du_lieu.months,
             du_lieu.start_date, end, du_lieu.note, user['id'])).lastrowid)
    return khoa


def huy_bao_hanh(wid: int, note: str, user) -> None:
    with transaction() as c:
        bh = c.execute('SELECT * FROM warranties WHERE id = ?', (wid,)).fetchone()
        if bh is None:
            raise KhongTimThay('Không tìm thấy bảo hành.')
        if bh['status'] not in ('ACTIVE',):
            raise SaiQuyTac('Chỉ huỷ được bảo hành đang còn hiệu lực.')
        ghi_chu = (bh['note'] or '')
        if note:
            ghi_chu = (ghi_chu + ' | ' if ghi_chu else '') + 'Huỷ: ' + note
        c.execute("UPDATE warranties SET status = 'CANCELLED', note = ?"
                  ' WHERE id = ?', (ghi_chu, wid))


def danh_sach(trang: Trang, *, trang_thai: str = '',
              q: str = '') -> tuple[list[dict], int]:
    dieu_kien, tham_so = ['1=1'], []
    if trang_thai in TEN_TRANG_THAI_BAOHANH:
        dieu_kien.append('w.status = ?')
        tham_so.append(trang_thai)
    if q:
        like = '%%%s%%' % q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        dieu_kien.append("(v.plate LIKE ? ESCAPE '\\' OR s.name LIKE ? ESCAPE '\\'"
                         " OR p.name LIKE ? ESCAPE '\\' OR CAST(w.id AS TEXT) = ?)")
        tham_so += [like, like, like, q.strip()]
    return crud.truy_van_danh_sach(
        'warranties',
        cot=('w.id', 'w.repair_order_id', 'v.plate', 'w.scope',
             'COALESCE(s.name, p.name) AS ten_hang_muc', 'w.months',
             'w.start_date', 'w.end_date', 'w.status', 'w.note',
             'u.full_name AS nguoi_lap'),
        dieu_kien=' AND '.join(dieu_kien), tham_so=tham_so, trang=trang,
        sap_xep='id', huong='desc')


def chi_tiet(wid: int) -> dict | None:
    return fetch_one(
        'SELECT w.*, v.plate, v.brand, v.model,'
        '       COALESCE(s.name, p.name) AS ten_hang_muc,'
        '       c.name AS ten_khach, u.full_name AS nguoi_lap'
        '  FROM warranties w'
        '  JOIN repair_orders r ON r.id = w.repair_order_id'
        '  JOIN vehicles v ON v.id = r.vehicle_id'
        '  JOIN customers c ON c.id = v.customer_id'
        '  LEFT JOIN services s ON s.id = w.service_id'
        '  LEFT JOIN parts p ON p.id = w.part_id'
        '  LEFT JOIN users u ON u.id = w.created_by'
        ' WHERE w.id = ?', (wid,))


def hang_muc_co_the_bao_hanh(repair_order_id: int) -> list[dict]:
    """Liệt kê hạng mục của phiếu COMPLETED chưa có bảo hành ACTIVE."""
    return fetch_all(
        '''SELECT ri.id AS item_id, ri.service_id, ri.part_id,
                  COALESCE(s.name, p.name) AS ten_hang_muc
             FROM repair_order_items ri
             LEFT JOIN services s ON s.id = ri.service_id
             LEFT JOIN parts p ON p.id = ri.part_id
            WHERE ri.repair_order_id = ?
              AND NOT EXISTS (
                  SELECT 1 FROM warranties w
                   WHERE w.repair_order_id = ri.repair_order_id
                     AND w.service_id IS ri.service_id
                     AND w.part_id IS ri.part_id
                     AND w.status IN ('ACTIVE', 'CLAIMED'))
            ORDER BY ri.id''', (repair_order_id,))
