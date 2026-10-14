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
from ..core.money import utc_now
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
             'q.valid_until', 'q.created_at', 'q.note', 'q.applied_at'),
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
    if phieu['status'] in ('COMPLETED', 'CANCELLED'):
        raise SaiQuyTac('Không tạo báo giá cho phiếu đã hoàn thành hoặc đã huỷ.')
    du = {'repair_order_id': du_lieu.repair_order_id, 'note': du_lieu.note,
          'valid_until': du_lieu.valid_until, 'created_by': user['id'],
          'total': 0}
    with transaction() as c:
        # Kiểm tra "chưa có báo giá đang mở" PHẢI nằm trong transaction để hai
        # yêu cầu song song không cùng tạo được nháp. Báo giá đã áp dụng
        # (applied_at NOT NULL) không còn chặn báo giá mới cho phiếu.
        trung = c.execute(
            "SELECT id FROM quotations WHERE repair_order_id = ?"
            " AND status IN ('DRAFT', 'SENT', 'APPROVED') AND applied_at IS NULL",
            (du_lieu.repair_order_id,)).fetchone()
        if trung:
            raise XungDdot(
                'Phiếu này đã có báo giá đang mở (số %d — nháp, chờ duyệt hoặc'
                ' đã duyệt). Hãy đóng báo giá cũ trước khi tạo bản mới.'
                % trung['id'])
        cur = c.execute(
            'INSERT INTO quotations (repair_order_id, note, valid_until,'
            ' created_by, total) VALUES'
            ' (:repair_order_id, :note, :valid_until, :created_by, :total)', du)
        return cur.lastrowid


def them_hang_muc(bao_gia_id: int, du_lieu: HangMucBaoGiaInput) -> None:
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
        # Kiểm tra trạng thái INSIDE transaction: gửi/duyệt chạy song song sẽ
        # không thể chèn dòng vào báo giá đã chốt.
        bg = c.execute('SELECT status FROM quotations WHERE id = ?',
                       (bao_gia_id,)).fetchone()
        if bg is None:
            raise KhongTimThay('Không tìm thấy báo giá số %d.' % bao_gia_id)
        if bg['status'] not in TRANG_THAI_DUOC_SUA:
            raise SaiQuyTac('Chỉ sửa được báo giá ở trạng thái bản nháp.'
                            ' Hiện tại: %s.' % bg['status'])
        c.execute(
            'INSERT INTO quotation_items (quotation_id, service_id, part_id,'
            ' qty, unit_price) VALUES (?, ?, ?, ?, ?)',
            (bao_gia_id, service_id, part_id, du_lieu.qty, gia))
        c.execute('UPDATE quotations SET total = ? WHERE id = ? AND status = ?',
                  (_tong(bao_gia_id), bao_gia_id, 'DRAFT'))


def go_hang_muc(bao_gia_id: int, item_id: int) -> None:
    with transaction() as c:
        bg = c.execute('SELECT status FROM quotations WHERE id = ?',
                       (bao_gia_id,)).fetchone()
        if bg is None:
            raise KhongTimThay('Không tìm thấy báo giá số %d.' % bao_gia_id)
        if bg['status'] not in TRANG_THAI_DUOC_SUA:
            raise SaiQuyTac('Chỉ sửa được báo giá ở trạng thái bản nháp.'
                            ' Hiện tại: %s.' % bg['status'])
        muc = c.execute('SELECT id FROM quotation_items'
                        ' WHERE id = ? AND quotation_id = ?',
                        (item_id, bao_gia_id)).fetchone()
        if muc is None:
            raise KhongTimThay('Không tìm thấy hạng mục trong báo giá.')
        c.execute('DELETE FROM quotation_items WHERE id = ?', (item_id,))
        c.execute('UPDATE quotations SET total = ? WHERE id = ? AND status = ?',
                  (_tong(bao_gia_id), bao_gia_id, 'DRAFT'))


def da_ap_dung(bao_gia_id: int) -> bool:
    """Báo giá đã được áp dụng vào phiếu chưa (dùng cho giao diện)."""
    return bool(fetch_value('SELECT applied_at FROM quotations WHERE id = ?',
                            (bao_gia_id,), None))


# ---------------------------------------------------------------------------
# Gửi / duyệt / huỷ
# ---------------------------------------------------------------------------
def gui_bao_gia(bao_gia_id: int) -> None:
    if not fetch_value('SELECT COUNT(*) FROM quotation_items WHERE quotation_id = ?',
                       (bao_gia_id,), 0):
        raise SaiQuyTac('Báo giá chưa có hạng mục nên không thể gửi.')
    with transaction() as c:
        # UPDATE có điều kiện: chỉ nhánh DRAFT mới chuyển được, tránh chạy đua
        # với duyệt/huỷ từ phiên khác.
        n = c.execute("UPDATE quotations SET status = 'SENT'"
                      " WHERE id = ? AND status = 'DRAFT'", (bao_gia_id,)).rowcount
        if n != 1:
            bg = c.execute('SELECT status FROM quotations WHERE id = ?',
                           (bao_gia_id,)).fetchone()
            if bg is None:
                raise KhongTimThay('Không tìm thấy báo giá số %d.' % bao_gia_id)
            raise SaiQuyTac('Không thể gửi báo giá ở trạng thái %s.' % bg['status'])


def duyet_bao_gia(bao_gia_id: int, du_lieu: DuyetBaoGiaInput, user) -> None:
    with transaction() as c:
        bg = c.execute('SELECT * FROM quotations WHERE id = ?',
                       (bao_gia_id,)).fetchone()
        if bg is None:
            raise KhongTimThay('Không tìm thấy báo giá số %d.' % bao_gia_id)
        if bg['status'] not in TRANG_THAI_DUOC_DUYET:
            raise SaiQuyTac('Không thể %s báo giá ở trạng thái %s.'
                            % ('duyệt', bg['status']))
        if du_lieu.quyet_dinh == 'APPROVED':
            # Mỗi phiếu chỉ một báo giá APPROVED còn hiệu lực tại một thời điểm
            # (báo giá đã áp dụng được loại trừ — cho phép làm báo giá mới khi
            # phát sinh thêm việc).
            trung = c.execute(
                "SELECT id FROM quotations WHERE repair_order_id = ?"
                " AND status = 'APPROVED' AND applied_at IS NULL AND id <> ?",
                (bg['repair_order_id'], bao_gia_id)).fetchone()
            if trung:
                raise XungDdot('Phiếu đã có báo giá được duyệt khác (số %d).'
                               % trung['id'])
            c.execute(
                "UPDATE quotations SET status = 'APPROVED', approved_by = ?,"
                " approved_at = datetime('now'), total = ? WHERE id = ?"
                " AND status = 'SENT'",
                (user['id'], _tong(bao_gia_id), bao_gia_id))
        else:
            c.execute("UPDATE quotations SET status = 'REJECTED'"
                      " WHERE id = ? AND status = 'SENT'", (bao_gia_id,))


def huy_bao_gia(bao_gia_id: int) -> None:
    """Huỷ bản nháp hoặc đánh dấu hết hiệu lực."""
    with transaction() as c:
        n = c.execute("UPDATE quotations SET status = 'REJECTED'"
                      " WHERE id = ? AND status IN ('DRAFT', 'SENT')",
                      (bao_gia_id,)).rowcount
        if n != 1:
            bg = c.execute('SELECT status FROM quotations WHERE id = ?',
                           (bao_gia_id,)).fetchone()
            if bg is None:
                raise KhongTimThay('Không tìm thấy báo giá số %d.' % bao_gia_id)
            raise SaiQuyTac('Chỉ huỷ được bản nháp hoặc bản đã gửi.'
                            ' Hiện tại: %s.' % bg['status'])


# ---------------------------------------------------------------------------
# Chuyển báo giá đã duyệt vào phiếu sửa chữa
# ---------------------------------------------------------------------------
def ap_dung_vao_phieu(bao_gia_id: int, user) -> int:
    """Copy các dòng APPROVED sang repair_order_items với giá đã chốt.

    Nguyên tắc:
    * **Chỉ một lần duy nhất** — `applied_at` được kiểm tra và ghi ngay trong
      transaction `BEGIN IMMEDIATE`; double-click/retry không thể nhân đôi.
    * Dòng phụ tùng **trừ kho qua sổ cái** (`USAGE`) đúng như `them_hang_muc`
      của phiếu — không thì tồn kho và báo cáo sẽ lệch.
    * Trả về số dòng đã thêm. Ngăn thêm nếu phiếu đã có hoá đơn.
    """
    from ..core.db import phieu_da_quyet_toan
    from .orders import _ghi_nhat_ky
    with transaction() as c:
        bg = c.execute('SELECT * FROM quotations WHERE id = ?',
                       (bao_gia_id,)).fetchone()
        if bg is None:
            raise KhongTimThay('Không tìm thấy báo giá số %d.' % bao_gia_id)
        if bg['status'] != 'APPROVED':
            raise SaiQuyTac('Chỉ áp dụng báo giá đã được duyệt.'
                            ' Hiện tại: %s.' % bg['status'])
        if bg['applied_at']:
            raise XungDdot(
                'Báo giá số %d đã được áp dụng vào phiếu lúc %s.'
                ' Không áp dụng lại để tránh nhân đôi hạng mục.'
                % (bao_gia_id, bg['applied_at']))
        phieu_id = bg['repair_order_id']
        if phieu_da_quyet_toan(phieu_id):
            raise SaiQuyTac('Phiếu đã có hoá đơn nên không thể thêm hạng mục.')
        phieu = c.execute('SELECT status FROM repair_orders WHERE id = ?',
                          (phieu_id,)).fetchone()
        if phieu and phieu['status'] in ('COMPLETED', 'CANCELLED'):
            raise SaiQuyTac('Phiếu đã đóng nên không thể thêm hạng mục.')
        rows = c.execute(
            'SELECT service_id, part_id, qty, unit_price FROM quotation_items'
            ' WHERE quotation_id = ?', (bao_gia_id,)).fetchall()
        if not rows:
            raise SaiQuyTac('Báo giá không có hạng mục để áp dụng.')
        from .stock import ghi_giao_dich
        for r in rows:
            if r['part_id'] is not None:
                # Trừ kho có điều kiện nguyên tử: không đủ hàng thì cả lần
                # áp dụng thất bại, không ghi nửa chừng.
                ghi_giao_dich(c, r['part_id'], -r['qty'], 'USAGE',
                              repair_order_id=phieu_id,
                              note='Áp dụng báo giá số %d' % bao_gia_id,
                              created_by=user['id'])
            c.execute(
                'INSERT INTO repair_order_items (repair_order_id, service_id,'
                ' part_id, qty, unit_price) VALUES (?, ?, ?, ?, ?)',
                (phieu_id, r['service_id'], r['part_id'], r['qty'], r['unit_price']))
        c.execute('UPDATE quotations SET applied_at = ?, applied_by = ?'
                  ' WHERE id = ? AND applied_at IS NULL',
                  (utc_now(), user['id'], bao_gia_id))
        _ghi_nhat_ky(c, phieu_id, user['id'],
                     'Áp dụng báo giá số %d (%d dòng) vào phiếu.'
                     % (bao_gia_id, len(rows)))
    return len(rows)


def _kiem_tra_trang_thai(bao_gia_id: int, cho_phep: set[str], hanh_dong: str) -> dict:
    bg = fetch_one('SELECT * FROM quotations WHERE id = ?', (bao_gia_id,))
    if bg is None:
        raise KhongTimThay('Không tìm thấy báo giá số %d.' % bao_gia_id)
    if bg['status'] not in cho_phep:
        raise SaiQuyTac('Không thể %s báo giá ở trạng thái %s.'
                        % (hanh_dong, bg['status']))
    return bg
