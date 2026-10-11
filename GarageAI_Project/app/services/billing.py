# -*- coding: utf-8 -*-
"""Nghiệp vụ hoá đơn và thanh toán.

Chống thu vượt là ưu tiên số một ở đây. Cách làm:

    UPDATE invoices SET paid = paid + ?
     WHERE id = ? AND total - paid >= ?

Điều kiện nằm ngay trong câu lệnh nên CSDL tự bảo đảm: hai giao dịch thanh toán
chạy đồng thời không thể cùng thành công vượt tổng. Nếu `rowcount` bằng 0 thì
báo "vượt số còn phải thu" thay vì ghi sai dữ liệu.

`invoices.paid` luôn bằng tổng `payments.amount`; hai bảng được cập nhật
trong cùng một transaction.
"""
from __future__ import annotations

from .. import crud
from ..core.db import fetch_all, fetch_one, transaction, tong_phieu
from ..core.errors import KhongTimThay, SaiQuyTac
from ..core.money import format_tien_dong, utc_now
from ..models import ThanhToanInput
from .security_matrix import TEN_HINH_THUC, TEN_TRANG_THAI


def lay_hoa_don(hd_id: int) -> dict:
    hd = fetch_one(
        'SELECT i.*, r.vehicle_id, v.plate, c.name AS khach'
        ' FROM invoices i'
        ' JOIN repair_orders r ON r.id = i.repair_order_id'
        ' JOIN vehicles v ON v.id = r.vehicle_id'
        ' JOIN customers c ON c.id = v.customer_id'
        ' WHERE i.id = ?', (hd_id,))
    if hd is None:
        raise KhongTimThay('Không tìm thấy hoá đơn số %d.' % hd_id)
    hd['ten_trang_thai'] = TEN_TRANG_THAI.get(hd['status'], hd['status'])
    hd['da_thu'] = fetch_one('SELECT COALESCE(SUM(amount),0) s FROM payments'
                             ' WHERE invoice_id = ?', (hd_id,))['s']
    hd['con_phai_thu'] = int(hd['total']) - int(hd['da_thu'])
    return hd


def khoan_thu(hd_id: int) -> list[dict]:
    return fetch_all('SELECT id, amount, method, paid_at FROM payments'
                     ' WHERE invoice_id = ? ORDER BY id', (hd_id,))


def danh_sach_hoa_don(trang, *, trang_thai: str = '', q: str = '') -> tuple[list[dict], int]:
    dieu_kien, tham_so = ['1=1'], []
    if trang_thai:
        dieu_kien.append('i.status = ?')
        tham_so.append(trang_thai)
    if q:
        dieu_kien.append("(v.plate LIKE ? ESCAPE '\\' OR c.name LIKE ? ESCAPE '\\')")
        like = '%%%s%%' % q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        tham_so += [like, like]
    return crud.truy_van_danh_sach(
        'invoices',
        cot=('i.id', 'i.repair_order_id', 'v.plate', 'c.name AS khach', 'i.total',
             'i.paid', 'i.status', 'i.created_at'),
        dieu_kien=' AND '.join(dieu_kien), tham_so=tham_so, trang=trang)


# ---------------------------------------------------------------------------
# Lập hoá đơn
# ---------------------------------------------------------------------------
def lap_hoa_don(phieu_id: int, user) -> int:
    """Tổng tiền do backend tính, không nhận từ giao diện."""
    phieu = fetch_one('SELECT * FROM repair_orders WHERE id = ?', (phieu_id,))
    if phieu is None:
        raise KhongTimThay('Không tìm thấy phiếu sửa chữa số %d.' % phieu_id)
    if phieu['status'] != 'COMPLETED':
        raise SaiQuyTac('Chỉ lập hoá đơn khi phiếu đã hoàn thành. Phiếu số %d'
                        ' hiện đang %s.' % (phieu_id,
                                           TEN_TRANG_THAI.get(phieu['status'])))
    tong = tong_phieu(phieu_id)
    if tong <= 0:
        raise SaiQuyTac('Phiếu chưa có hạng mục nên chưa lập được hoá đơn.')

    with transaction() as c:
        if c.execute('SELECT 1 FROM invoices WHERE repair_order_id = ?',
                     (phieu_id,)).fetchone():
            raise SaiQuyTac('Phiếu này đã có hoá đơn.')
        hd_id = int(c.execute(
            'INSERT INTO invoices (repair_order_id, total, paid, status, created_at)'
            ' VALUES (?, ?, 0, ?, ?)',
            (phieu_id, tong, 'UNPAID', utc_now())).lastrowid)
        c.execute('INSERT INTO repair_logs (repair_order_id, technician_id, note)'
                  ' VALUES (?, ?, ?)',
                  (phieu_id, user['id'], 'Lập hoá đơn tổng %s' % format_tien_dong(tong)))
    return hd_id


# ---------------------------------------------------------------------------
# Thanh toán
# ---------------------------------------------------------------------------
def ghi_nhan_thanh_toan(hd_id: int, du_lieu: ThanhToanInput, user) -> dict:
    with transaction() as c:
        hd = c.execute('SELECT * FROM invoices WHERE id = ?', (hd_id,)).fetchone()
        if hd is None:
            raise KhongTimThay('Không tìm thấy hoá đơn số %d.' % hd_id)

        # Cập nhật có điều kiện: CSDL tự bảo đảm không vượt tổng.
        n = c.execute(
            'UPDATE invoices SET paid = paid + ? WHERE id = ? AND total - paid >= ?',
            (du_lieu.amount, hd_id, du_lieu.amount)).rowcount
        if n != 1:
            con_phai_thu = hd['total'] - hd['paid']
            if du_lieu.amount > con_phai_thu:
                raise SaiQuyTac(
                    'Số tiền vượt số còn phải thu (%s).'
                    % format_tien_dong(con_phai_thu))
            raise SaiQuyTac('Hoá đơn vừa được cập nhật bởi giao dịch khác,'
                            ' vui lòng thử lại.')

        c.execute('INSERT INTO payments (invoice_id, amount, method, paid_at)'
                  ' VALUES (?, ?, ?, ?)',
                  (hd_id, du_lieu.amount, du_lieu.method, utc_now()))

        da_thu = c.execute('SELECT COALESCE(SUM(amount),0) FROM payments'
                           ' WHERE invoice_id = ?', (hd_id,)).fetchone()[0]
        trang_thai = 'PAID' if da_thu >= hd['total'] else 'PARTIAL'
        c.execute('UPDATE invoices SET paid = ?, status = ? WHERE id = ?',
                  (da_thu, trang_thai, hd_id))

        c.execute('INSERT INTO repair_logs (repair_order_id, technician_id, note)'
                  ' VALUES (?, ?, ?)',
                  (hd['repair_order_id'], user['id'],
                   'Thu %s (%s), còn phải thu %s'
                   % (format_tien_dong(du_lieu.amount),
                      TEN_HINH_THUC.get(du_lieu.method, du_lieu.method),
                      format_tien_dong(hd['total'] - da_thu))))

    return {'da_thu': da_thu, 'con_phai_thu': hd['total'] - da_thu,
            'status': trang_thai}


def huy_thanh_toan(hd_id: int, khoan_id: int, user) -> None:
    """Huỷ một khoản thu và cập nhật lại tổng đã thu."""
    with transaction() as c:
        hd = c.execute('SELECT * FROM invoices WHERE id = ?', (hd_id,)).fetchone()
        if hd is None:
            raise KhongTimThay('Không tìm thấy hoá đơn số %d.' % hd_id)
        khoan = c.execute('SELECT * FROM payments WHERE id = ? AND invoice_id = ?',
                          (khoan_id, hd_id)).fetchone()
        if khoan is None:
            raise KhongTimThay('Không tìm thấy khoản thu cần huỷ.')
        c.execute('DELETE FROM payments WHERE id = ?', (khoan_id,))
        da_thu = c.execute('SELECT COALESCE(SUM(amount),0) FROM payments'
                           ' WHERE invoice_id = ?', (hd_id,)).fetchone()[0]
        trang_thai = 'PAID' if da_thu >= hd['total'] else ('PARTIAL' if da_thu > 0 else 'UNPAID')
        c.execute('UPDATE invoices SET paid = ?, status = ? WHERE id = ?',
                  (da_thu, trang_thai, hd_id))
        c.execute('INSERT INTO repair_logs (repair_order_id, technician_id, note)'
                  ' VALUES (?, ?, ?)',
                  (hd['repair_order_id'], user['id'],
                   'Huỷ khoản thu %s' % format_tien_dong(khoan['amount'])))