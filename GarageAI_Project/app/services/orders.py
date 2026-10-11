# -*- coding: utf-8 -*-
"""Nghiệp vụ phiếu sửa chữa.

Đây là nơi dễ mất tiền và mất hàng nhất, nên mọi thao tác ảnh hưởng đến tiền
hoặc tồn kho đều nằm trong **một** transaction `BEGIN IMMEDIATE`, và điều kiện
được kiểm tra ngay trong câu lệnh `UPDATE` chứ không kiểm tra rồi mới ghi.

Ví dụ trừ kho:

    UPDATE parts SET stock = stock - ? WHERE id = ? AND stock >= ?

Câu lệnh này là nguyên tử: hai phiếu cùng lấy hàng sẽ không bao giờ cùng thành
công. Cách cũ (đọc `stock`, so sánh trong Python, rồi `UPDATE`) bị chạy đua và
có thể trừ kho âm.
"""
from __future__ import annotations

import sqlite3

from .. import crud
from ..core.db import (fetch_all, fetch_one, fetch_value, phieu_da_quyet_toan,
                        tong_phieu, transaction)
from ..core.errors import (AppError, KhongTimThay, LoiKhongMoDuoc, SaiQuyTac,
                           VuotGioiHan)
from ..core.money import utc_now
from ..models import (DoiTrangThaiInput, NhatKyInput, PhanCongInput,
                      TaoPhieuInput, ThemHangMucInput)
from .security_matrix import CHUYEN_TRANG_THAI, TEN_TRANG_THAI

TRANG_THAI_KHOA_HANG_MUC = {'COMPLETED', 'CANCELLED'}


# ---------------------------------------------------------------------------
# Truy vấn
# ---------------------------------------------------------------------------
FROM_PHIEU = ('repair_orders r'
              ' JOIN vehicles v ON v.id = r.vehicle_id'
              ' LEFT JOIN users u ON u.id = r.technician_id')


def danh_sach_phieu(trang, *, q: str = '', trang_thai: str = '') -> tuple[list[dict], int]:
    dieu_kien, tham_so = ['1=1'], []
    if q:
        dieu_kien.append(
            "(v.plate LIKE ? ESCAPE '\\' OR r.technical_notes LIKE ? ESCAPE '\\'"
            " OR CAST(r.id AS TEXT) = ?)")
        like = '%%%s%%' % q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        tham_so += [like, like, q.strip()]
    if trang_thai:
        dieu_kien.append('r.status = ?')
        tham_so.append(trang_thai)
    return crud.truy_van_danh_sach(
        'repair_orders',
        cot=('r.id', 'v.plate', 'v.brand', 'v.model', 'r.status', 'r.created_at',
             'r.technical_notes', 'u.full_name AS ky_thuat_vien'),
        dieu_kien=' AND '.join(dieu_kien), tham_so=tham_so, trang=trang,
        sap_xep='created_at', huong='desc', from_clause=FROM_PHIEU)


def chi_tiet(phieu_id: int) -> dict:
    phieu = fetch_one(
        'SELECT r.*, v.plate, v.brand, v.model, v.year, v.customer_id,'
        ' c.name AS khach, c.phone AS khach_phone, u.full_name AS ky_thuat_vien'
        ' FROM repair_orders r'
        ' JOIN vehicles v ON v.id = r.vehicle_id'
        ' JOIN customers c ON c.id = v.customer_id'
        ' LEFT JOIN users u ON u.id = r.technician_id'
        ' WHERE r.id = ?', (phieu_id,))
    if phieu is None:
        raise KhongTimThay('Không tìm thấy phiếu sửa chữa số %d.' % phieu_id)
    phieu['tong'] = tong_phieu(phieu_id)
    phieu['ten_trang_thai'] = TEN_TRANG_THAI.get(phieu['status'], phieu['status'])
    return phieu


def hang_muc(phieu_id: int) -> list[dict]:
    return fetch_all(
        'SELECT i.id, i.service_id, i.part_id, i.qty, i.unit_price,'
        ' COALESCE(s.name, p.name) AS ten, i.unit_price * i.qty AS thanh_tien'
        ' FROM repair_order_items i'
        ' LEFT JOIN services s ON s.id = i.service_id'
        ' LEFT JOIN parts p ON p.id = i.part_id'
        ' WHERE i.repair_order_id = ? ORDER BY i.id', (phieu_id,))


def nhat_ky(phieu_id: int) -> list[dict]:
    return fetch_all(
        'SELECT l.id, l.note, l.created_at, u.full_name'
        ' FROM repair_logs l LEFT JOIN users u ON u.id = l.technician_id'
        ' WHERE l.repair_order_id = ? ORDER BY l.id', (phieu_id,))


def hoa_don_cua_phieu(phieu_id: int) -> dict | None:
    return fetch_one('SELECT * FROM invoices WHERE repair_order_id = ?', (phieu_id,))


# ---------------------------------------------------------------------------
# Kiểm tra quyền trên phiếu (dùng lại cho mọi thao tác)
# ---------------------------------------------------------------------------
def _kiem_tra_quyen_thao_tac(user, phieu_id: int, *, can_sua=True):
    phieu = fetch_one('SELECT * FROM repair_orders WHERE id = ?', (phieu_id,))
    if phieu is None:
        raise KhongTimThay('Không tìm thấy phiếu sửa chữa số %d.' % phieu_id)
    from .auth import gan_quyen_phan_cong
    from .security_matrix import duoc_gan_cong
    if can_sua and not gan_quyen_phan_cong(user) and not duoc_gan_cong(user, phieu):
        raise SaiQuyTac('Bạn không được phân công phiếu này nên không thể thao tác.')
    return phieu


def _ghi_nhat_ky(conn, phieu_id: int, user_id: int, noi_dung: str) -> None:
    conn.execute('INSERT INTO repair_logs (repair_order_id, technician_id, note)'
                 ' VALUES (?, ?, ?)', (phieu_id, user_id, noi_dung))


# ---------------------------------------------------------------------------
# Tiếp nhận xe
# ---------------------------------------------------------------------------
def tao_phieu(du_lieu: TaoPhieuInput, user) -> int:
    xe = crud.phuong_tien_theo_id(du_lieu.vehicle_id)
    if xe is None:
        raise SaiQuyTac('Phương tiện không tồn tại.', truong='vehicle_id')
    if du_lieu.technician_id:
        ktv = crud.nguoi_dung_theo_id(du_lieu.technician_id)
        if ktv is None or ktv['role'] != 'TECHNICIAN':
            raise SaiQuyTac('Người được chọn không phải kỹ thuật viên.',
                            truong='technician_id')
    dang_mo = fetch_one(
        "SELECT id FROM repair_orders WHERE vehicle_id = ?"
        " AND status IN ('RECEIVED','INSPECTING','ESTIMATING','REPAIRING') LIMIT 1",
        (du_lieu.vehicle_id,))
    if dang_mo:
        raise SaiQuyTac(
            'Xe %s đang có phiếu sửa chữa số %d chưa hoàn tất.'
            % (xe['plate'], dang_mo['id']))

    with transaction() as c:
        khoa = int(c.execute(
            'INSERT INTO repair_orders (vehicle_id, technician_id, status,'
            ' technical_notes, created_at) VALUES (?, ?, ?, ?, ?)',
            (du_lieu.vehicle_id, du_lieu.technician_id, 'RECEIVED',
             du_lieu.technical_notes, utc_now())).lastrowid)
        _ghi_nhat_ky(c, khoa, user['id'],
                     'Tiếp nhận xe %s. %s' % (xe['plate'],
                                             du_lieu.technical_notes or ''))
    return khoa


def gan_ky_thuat_vien(phieu_id: int, du_lieu: PhanCongInput, user) -> None:
    phieu = _kiem_tra_quyen_thao_tac(user, phieu_id, can_sua=False)
    if phieu['status'] in TRANG_THAI_KHOA_HANG_MUC:
        raise SaiQuyTac('Phiếu đã %s nên không thể phân công lại.'
                        % TEN_TRANG_THAI.get(phieu['status'], phieu['status']))
    if du_lieu.technician_id is None:
        crud.execute('UPDATE repair_orders SET technician_id = NULL WHERE id = ?',
                     (phieu_id,))
        ghi = 'Bỏ phân công kỹ thuật viên.'
    else:
        ktv = crud.nguoi_dung_theo_id(du_lieu.technician_id)
        if ktv is None or ktv['role'] != 'TECHNICIAN':
            raise SaiQuyTac('Người được chọn không phải kỹ thuật viên.',
                            truong='technician_id')
        crud.execute('UPDATE repair_orders SET technician_id = ? WHERE id = ?',
                     (du_lieu.technician_id, phieu_id))
        ghi = 'Phân công kỹ thuật viên %s.' % ktv['full_name']
    with transaction() as c:
        _ghi_nhat_ky(c, phieu_id, user['id'], ghi)


# ---------------------------------------------------------------------------
# Hạng mục — nơi cần transaction cẩn thận
# ---------------------------------------------------------------------------
def _khoa_hang_muc(phieu: dict) -> None:
    if phieu['status'] in TRANG_THAI_KHOA_HANG_MUC:
        raise SaiQuyTac(
            'Phiếu đã %s nên không thể thay đổi hạng mục. Muốn phát sinh thêm'
            ' hãy mở một phiếu sửa chữa mới.'
            % TEN_TRANG_THAI.get(phieu['status'], phieu['status']))
    if phieu_da_quyet_toan(phieu['id']):
        raise SaiQuyTac(
            'Phiếu đã có hoá đơn. Hạng mục đã được chốt tiền nên không thể thêm'
            ' hoặc gỡ, tránh lệch giữa tổng hàng mục và tổng hoá đơn.')


def them_hang_muc(phieu_id: int, du_lieu: ThemHangMucInput, user) -> None:
    _kiem_tra_quyen_thao_tac(user, phieu_id)
    phieu = fetch_one('SELECT * FROM repair_orders WHERE id = ?', (phieu_id,))
    _khoa_hang_muc(phieu)

    with transaction() as c:
        if du_lieu.loai == 'dich_vu':
            dong = c.execute('SELECT id, name, price, is_active FROM services'
                             ' WHERE id = ?', (du_lieu.ma,)).fetchone()
            if dong is None:
                raise SaiQuyTac('Dịch vụ không tồn tại.', truong='ma')
            sid, pid, gia, ten = dong['id'], None, int(dong['price']), dong['name']
        else:
            dong = c.execute('SELECT id, name, price, stock, is_active FROM parts'
                             ' WHERE id = ?', (du_lieu.ma,)).fetchone()
            if dong is None:
                raise SaiQuyTac('Phụ tùng không tồn tại.', truong='ma')
            # Trừ kho có điều kiện: nguyên tử, không chạy đua được.
            da_tru = c.execute(
                'UPDATE parts SET stock = stock - ? WHERE id = ? AND stock >= ?',
                (du_lieu.qty, du_lieu.ma, du_lieu.qty)).rowcount
            if da_tru != 1:
                con = c.execute('SELECT stock FROM parts WHERE id = ?',
                                (du_lieu.ma,)).fetchone()
                raise SaiQuyTac('Tồn kho không đủ. Hiện còn %d.'
                                % (con['stock'] if con else 0), truong='qty')
            sid, pid, gia, ten = None, dong['id'], int(dong['price']), dong['name']

        c.execute('INSERT INTO repair_order_items (repair_order_id, service_id,'
                  ' part_id, qty, unit_price) VALUES (?, ?, ?, ?, ?)',
                  (phieu_id, sid, pid, du_lieu.qty, gia))
        _ghi_nhat_ky(c, phieu_id, user['id'],
                     'Thêm hạng mục %s x%d' % (ten, du_lieu.qty))


def go_hang_muc(phieu_id: int, muc_id: int, user) -> None:
    _kiem_tra_quyen_thao_tac(user, phieu_id)
    phieu = fetch_one('SELECT * FROM repair_orders WHERE id = ?', (phieu_id,))
    _khoa_hang_muc(phieu)

    with transaction() as c:
        muc = c.execute('SELECT * FROM repair_order_items'
                        ' WHERE id = ? AND repair_order_id = ?',
                        (muc_id, phieu_id)).fetchone()
        if muc is None:
            raise KhongTimThay('Không tìm thấy hạng mục cần gỡ.')
        if muc['part_id'] is not None:
            # Gỡ hạng mục phải trả lại phụ tùng về kho.
            c.execute('UPDATE parts SET stock = stock + ? WHERE id = ?',
                      (muc['qty'], muc['part_id']))
        c.execute('DELETE FROM repair_order_items WHERE id = ?', (muc_id,))
        ten = c.execute(
            'SELECT COALESCE((SELECT name FROM services WHERE id = ?),'
            ' (SELECT name FROM parts WHERE id = ?))',
            (muc['service_id'], muc['part_id'])).fetchone()[0]
        _ghi_nhat_ky(c, phieu_id, user['id'], 'Gỡ hạng mục %s x%d' % (ten, muc['qty']))


# ---------------------------------------------------------------------------
# Trạng thái
# ---------------------------------------------------------------------------
def doi_trang_thai(phieu_id: int, du_lieu: DoiTrangThaiInput, user) -> None:
    phieu = _kiem_tra_quyen_thao_tac(user, phieu_id)
    moi = du_lieu.status.strip().upper()
    if moi not in CHUYEN_TRANG_THAI.get(phieu['status'], []):
        raise SaiQuyTac(
            'Không thể chuyển từ %s sang %s.'
            % (TEN_TRANG_THAI.get(phieu['status'], phieu['status']),
               TEN_TRANG_THAI.get(moi, moi)))

    with transaction() as c:
        if moi == 'COMPLETED':
            if phieu_da_quyet_toan(phieu_id):
                raise SaiQuyTac('Phiếu đã có hoá đơn, không thể đổi trạng thái'
                                ' sang Hoàn thành. Hãy quản lý thanh toán tại hoá đơn.')
            if tong_phieu(phieu_id) <= 0:
                raise SaiQuyTac('Phiếu chưa có hạng mục nên chưa thể hoàn thành.')
        c.execute('UPDATE repair_orders SET status = ? WHERE id = ?', (moi, phieu_id))
        if moi == 'CANCELLED':
            _hoan_tra_ton_kho(c, phieu_id)
        _ghi_nhat_ky(c, phieu_id, user['id'],
                     'Đổi trạng thái %s → %s'
                     % (TEN_TRANG_THAI.get(phieu['status'], phieu['status']),
                        TEN_TRANG_THAI.get(moi, moi)))


def _hoan_tra_ton_kho(conn, phieu_id: int) -> None:
    """Huỷ phiếu thì trả lại phụ tùng đã trừ. Không trả nếu đã có hoá đơn."""
    if conn.execute('SELECT 1 FROM invoices WHERE repair_order_id = ?',
                    (phieu_id,)).fetchone():
        return
    hang = conn.execute(
        'SELECT part_id, SUM(qty) AS qty FROM repair_order_items'
        ' WHERE repair_order_id = ? AND part_id IS NOT NULL GROUP BY part_id',
        (phieu_id,)).fetchall()
    for h in hang:
        conn.execute('UPDATE parts SET stock = stock + ? WHERE id = ?',
                     (h['qty'], h['part_id']))
        # technician_id cho phép NULL: đây là thay đổi do hệ thống tự thực
        # hiện chứ không phải nhân viên nào ghi tay.
        conn.execute('INSERT INTO repair_logs (repair_order_id, technician_id, note)'
                     ' VALUES (?, NULL, ?)',
                     (phieu_id, 'Hoàn trả tồn kho phụ tùng %d cáy (huỷ phiếu).'
                      % h['qty']))


# ---------------------------------------------------------------------------
# Nhật ký
# ---------------------------------------------------------------------------
def them_nhat_ky(phieu_id: int, du_lieu: NhatKyInput, user) -> None:
    """Có kiểm tra phân công giống hệt các thao tác khác trên phiếu."""
    _kiem_tra_quyen_thao_tac(user, phieu_id)
    with transaction() as c:
        _ghi_nhat_ky(c, phieu_id, user['id'], du_lieu.note)


def xoa_phieu(phieu_id: int, user) -> None:
    """Chỉ cho xoá phiếu chưa phát sinh hạng mục, hoá đơn hay thanh toán."""
    phieu = fetch_one('SELECT * FROM repair_orders WHERE id = ?', (phieu_id,))
    if phieu is None:
        raise KhongTimThay('Không tìm thấy phiếu cần xoá.')
    for bang, cot in (('repair_order_items', 'repair_order_id'),
                      ('invoices', 'repair_order_id'),
                      ('repair_logs', 'repair_order_id')):
        if crud.co_ban_ghi(bang, '%s = ?' % cot, (phieu_id,)):
            raise SaiQuyTac(
                'Phiếu đã phát sinh %s nên không thể xoá. Hãy huỷ phiếu thay vì xoá.'
                % {'repair_order_items': 'hạng mục', 'invoices': 'hoá đơn',
                   'repair_logs': 'nhật ký'}[bang])
    crud.xoa('repair_orders', phieu_id)