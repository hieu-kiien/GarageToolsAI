# -*- coding: utf-8 -*-
"""Nghiệp vụ báo giá chính thức.

Báo giá đi theo phiếu sửa chữa. Ba nguyên tắc:
* Mọi dòng báo giá hoặc là dịch vụ, hoặc là phụ tùng (XOR), giá CHỐT tại
  thời điểm thêm — không tra động để giá catalogue đổi không làm lệch báo giá.
* Tổng báo giá do backend tính lại từ các dòng, không nhận từ giao diện.
* Duyệt báo giá chỉ được khi đang ở trạng thái SENT, và mỗi phiếu chỉ có
  MỘT báo giá APPROVED tại một thời điểm.
"""
from __future__ import annotations


from .. import crud
from ..core.db import fetch_all, fetch_one, fetch_value, transaction
from ..core.errors import (KhongTimThay, SaiQuyTac, XungDdot)
from ..models import (DuyetBaoGiaInput, HangMucBaoGiaInput, TaoBaoGiaInput)

#: Trạng thái được phép thêm/gỡ dòng.
TRANG_THAI_DUOC_SUA = {'DRAFT'}
#: Trạng thái được gửi khách.
TRANG_THAI_DUOC_GUI = {'DRAFT'}
#: Trạng thái được duyệt/từ chối.
TRANG_THAI_DUOC_DUYET = {'SENT'}


def _tong(quotation_id: int) -> int:
    return fetch_value(
        'SELECT COALESCE(SUM(unit_price * qty), 0) FROM quotation_items'
        ' WHERE quotation_id = ?', (quotation_id,), 0)


# ---------------------------------------------------------------------------
# Truy vấn
# ---------------------------------------------------------------------------
FROM_BAO_GIA = ('quotations q'
                ' JOIN repair_orders r ON r.id = q.repair_order_id'
                ' JOIN vehicles v ON v.id = r.vehicle_id')


def danh_sach(trang, *, trang_thai: str = '', q: str = '') -> tuple[list[dict], int]:
    dieu_kien, tham_so = ['1=1'], []
    if trang_thai:
        dieu_kien.append('q.status = ?')
        tham_so.append(trang_thai)
    if q:
        like = '%%%s%%' % q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        dieu_kien.append("(v.plate LIKE ? ESCAPE '\\' OR CAST(q.id AS TEXT) = ?"
                         " OR CAST(r.id AS TEXT) = ?)")
        tham_so += [like, q.strip(), q.strip()]
    return crud.truy_van_danh_sach(
        'quotations',
        cot=('q.id', 'q.repair_order_id', 'v.plate', 'q.status', 'q.total',
             'q.valid_until', 'q.created_at', 'q.note'),
        dieu_kien=' AND '.join(dieu_kien), tham_so=tham_so, trang=trang,
        sap_xep='created_at', huong='desc', from_clause=FROM_BAO_GIA)


def chi_tiet(bao_gia_id: int) -> dict:
    bg = fetch_one(
        'SELECT q.*, r.vehicle_id, r.status AS phieu_status, v.plate,'
        ' v.brand, v.model, c.name AS khach'
        ' FROM quotations q'
        ' JOIN repair_orders r ON r.id = q.repair_order_id'
        ' JOIN vehicles v ON v.id = r.vehicle_id'
        ' JOIN customers c ON c.id = v.customer_id'
        ' WHERE q.id = ?', (bao_gia_id,))
    if bg is None:
        raise KhongTimThay('Không tìm thấy báo giá số %d.' % bao_gia_id)
    bg['hang_muc'] = hang_muc(bao_gia_id)
    bg['tong'] = _tong(bao_gia_id)
    return bg


def hang_muc(bao_gia_id: int) -> list[dict]:
    return fetch_all(
        'SELECT i.id, i.service_id, i.part_id, i.qty, i.unit_price,'
        ' COALESCE(s.name, p.name) AS ten, i.unit_price * i.qty AS thanh_tien'
        ' FROM quotation_items i'
        ' LEFT JOIN services s ON s.id = i.service_id'
        ' LEFT JOIN parts p ON p.id = i.part_id'
        ' WHERE i.quotation_id = ? ORDER BY i.id', (bao_gia_id,))


# ---------------------------------------------------------------------------
# Tạo và sửa báo giá
# ---------------------------------------------------------------------------
def tao_bao_gia(du_lieu: TaoBaoGiaInput, user) -> int:
    phieu = fetch_one('SELECT * FROM repair_orders WHERE id = ?',
                      (du_lieu.repair_order_id,))
    if phieu is None:
        raise KhongTimThay('Không tìm thấy phiếu sửa chữa.')
    if phieu['status'] in ('CANCELLED',):
        raise SaiQuyTac('Không tạo báo giá cho phiếu đã huỷ.')
    if fetch_one("SELECT id FROM quotations WHERE repair_order_id = ?"
                 " AND status IN ('DRAFT', 'SENT', 'APPROVED')",
                 (du_lieu.repair_order_id,)):
        raise XungDdot(
            'Phiếu này đã có báo giá đang mở (nháp, chờ duyệt hoặc đã duyệt).'
            ' Hãy đóng báo giá cũ trước khi tạo bản mới.')
    du = {'repair_order_id': du_lieu.repair_order_id, 'note': du_lieu.note,
          'valid_until': du_lieu.valid_until, 'created_by': user['id'],
          'total': 0}
    with transaction() as c:
        cur = c.execute(
            'INSERT INTO quotations (repair_order_id, note, valid_until,'
            ' created_by, total) VALUES'
            ' (:repair_order_id, :note, :valid_until, :created_by, :total)', du)
        return cur.lastrowid


def them_hang_muc(bao_gia_id: int, du_lieu: HangMucBaoGiaInput) -> None:
    _kiem_tra_sua_duoc(bao_gia_id)
    if du_lieu.loai == 'dich_vu':
        hang = crud.lay_mot('services', du_lieu.ma)
        if hang is None or not hang['is_active']:
            raise SaiQuyTac('Dịch vụ không tồn tại hoặc đã ngừng kinh doanh.',
                            truong='ma')
        gia, part_id, service_id = hang['price'], None, hang['id']
    else:
        hang = crud.lay_mot('parts', du_lieu.ma)
        if hang is None or not hang['is_active']:
            raise SaiQuyTac('Phụ tùng không tồn tại hoặc đã ngừng kinh doanh.',
                            truong='ma')
        gia, part_id, service_id = hang['price'], hang['id'], None
    with transaction() as c:
        c.execute(
            'INSERT INTO quotation_items (quotation_id, service_id, part_id,'
            ' qty, unit_price) VALUES (?, ?, ?, ?, ?)',
            (bao_gia_id, service_id, part_id, du_lieu.qty, gia))
        c.execute('UPDATE quotations SET total = ? WHERE id = ?',
                  (_tong(bao_gia_id), bao_gia_id))


def go_hang_muc(bao_gia_id: int, item_id: int) -> None:
    _kiem_tra_sua_duoc(bao_gia_id)
    if not fetch_one('SELECT id FROM quotation_items WHERE id = ? AND quotation_id = ?',
                     (item_id, bao_gia_id)):
        raise KhongTimThay('Không tìm thấy hạng mục trong báo giá.')
    with transaction() as c:
        c.execute('DELETE FROM quotation_items WHERE id = ?', (item_id,))
        c.execute('UPDATE quotations SET total = ? WHERE id = ?',
                  (_tong(bao_gia_id), bao_gia_id))


def _kiem_tra_sua_duoc(bao_gia_id: int) -> dict:
    bg = fetch_one('SELECT * FROM quotations WHERE id = ?', (bao_gia_id,))
    if bg is None:
        raise KhongTimThay('Không tìm thấy báo giá số %d.' % bao_gia_id)
    if bg['status'] not in TRANG_THAI_DUOC_SUA:
        raise SaiQuyTac('Chỉ sửa được báo giá ở trạng thái bản nháp.'
                        ' Hiện tại: %s.' % bg['status'])
    return bg


# ---------------------------------------------------------------------------
# Gửi / duyệt / huỷ
# ---------------------------------------------------------------------------
def gui_bao_gia(bao_gia_id: int) -> None:
    _kiem_tra_trang_thai(bao_gia_id, TRANG_THAI_DUOC_GUI, 'gửi')
    if not fetch_value('SELECT COUNT(*) FROM quotation_items WHERE quotation_id = ?',
                       (bao_gia_id,), 0):
        raise SaiQuyTac('Báo giá chưa có hạng mục nên không thể gửi.')
    with transaction() as c:
        c.execute("UPDATE quotations SET status = 'SENT' WHERE id = ?", (bao_gia_id,))


def duyet_bao_gia(bao_gia_id: int, du_lieu: DuyetBaoGiaInput, user) -> None:
    bg = _kiem_tra_trang_thai(bao_gia_id, TRANG_THAI_DUOC_DUYET, 'duyệt')
    with transaction() as c:
        if du_lieu.quyet_dinh == 'APPROVED':
            # Mỗi phiếu chỉ một báo giá APPROVED.
            trung = c.execute(
                "SELECT id FROM quotations WHERE repair_order_id = ?"
                " AND status = 'APPROVED' AND id <> ?",
                (bg['repair_order_id'], bao_gia_id)).fetchone()
            if trung:
                raise XungDdot('Phiếu đã có báo giá được duyệt khác (số %d).'
                               % trung['id'])
            c.execute(
                "UPDATE quotations SET status = 'APPROVED', approved_by = ?,"
                " approved_at = datetime('now'), total = ? WHERE id = ?",
                (user['id'], _tong(bao_gia_id), bao_gia_id))
        else:
            c.execute("UPDATE quotations SET status = 'REJECTED' WHERE id = ?",
                      (bao_gia_id,))


def huy_bao_gia(bao_gia_id: int) -> None:
    """Huỷ bản nháp hoặc đánh dấu hết hiệu lực."""
    bg = fetch_one('SELECT * FROM quotations WHERE id = ?', (bao_gia_id,))
    if bg is None:
        raise KhongTimThay('Không tìm thấy báo giá số %d.' % bao_gia_id)
    if bg['status'] not in ('DRAFT', 'SENT'):
        raise SaiQuyTac('Chỉ huỷ được bản nháp hoặc bản đã gửi.'
                        ' Hiện tại: %s.' % bg['status'])
    with transaction() as c:
        c.execute("UPDATE quotations SET status = 'REJECTED' WHERE id = ?",
                  (bao_gia_id,))


# ---------------------------------------------------------------------------
# Chuyển báo giá đã duyệt vào phiếu sửa chữa
# ---------------------------------------------------------------------------
def ap_dung_vao_phieu(bao_gia_id: int, user) -> int:
    """Copy các dòng APPROVED sang repair_order_items với giá đã chốt.

    Trả về số dòng đã thêm. Ngăn thêm nếu phiếu đã có hoá đơn.
    """
    bg = fetch_one('SELECT * FROM quotations WHERE id = ?', (bao_gia_id,))
    if bg is None:
        raise KhongTimThay('Không tìm thấy báo giá số %d.' % bao_gia_id)
    if bg['status'] != 'APPROVED':
        raise SaiQuyTac('Chỉ áp dụng báo giá đã được duyệt.'
                        ' Hiện tại: %s.' % bg['status'])
    phieu_id = bg['repair_order_id']
    from ..core.db import phieu_da_quyet_toan
    if phieu_da_quyet_toan(phieu_id):
        raise SaiQuyTac('Phiếu đã có hoá đơn nên không thể thêm hạng mục.')
    phieu = fetch_one('SELECT status FROM repair_orders WHERE id = ?', (phieu_id,))
    if phieu and phieu['status'] in ('COMPLETED', 'CANCELLED'):
        raise SaiQuyTac('Phiếu đã đóng nên không thể thêm hạng mục.')
    rows = fetch_all(
        'SELECT service_id, part_id, qty, unit_price FROM quotation_items'
        ' WHERE quotation_id = ?', (bao_gia_id,))
    if not rows:
        raise SaiQuyTac('Báo giá không có hạng mục để áp dụng.')
    with transaction() as c:
        for r in rows:
            c.execute(
                'INSERT INTO repair_order_items (repair_order_id, service_id,'
                ' part_id, qty, unit_price) VALUES (?, ?, ?, ?, ?)',
                (phieu_id, r['service_id'], r['part_id'], r['qty'], r['unit_price']))
        from .orders import _ghi_nhat_ky
        _ghi_nhat_ky(c, phieu_id, user['id'],
                     'Áp dụng báo giá số %d (%d dòng) vào phiếu.' % (bao_gia_id, len(rows)))
    return len(rows)


def _kiem_tra_trang_thai(bao_gia_id: int, cho_phep: set[str], hanh_dong: str) -> dict:
    bg = fetch_one('SELECT * FROM quotations WHERE id = ?', (bao_gia_id,))
    if bg is None:
        raise KhongTimThay('Không tìm thấy báo giá số %d.' % bao_gia_id)
    if bg['status'] not in cho_phep:
        raise SaiQuyTac('Không thể %s báo giá ở trạng thái %s.'
                        % (hanh_dong, bg['status']))
    return bg
