# -*- coding: utf-8 -*-
"""Tầng truy cập dữ liệu.

Quy tắc bất di bất dịch của tầng này:
* **Chỉ đọc và ghi dữ liệu.** Không kiểm tra nghiệp vụ, không phát sinh thông báo.
  Việc đó thuộc tầng `services`.
* **Mọi giá trị đều qua tham số.** Tên bảng và tên cột lấy từ hằng trong mã.
  Mệnh đề `ORDER BY` là ngoại lệ vì SQLite không nhận tham số, nên tên cột
  luôn phải đi qua `pagination.cot_sap_xep` (danh sách cho phép).
* **Có phân trang.** Không hàm nào trả toàn bộ bảng nếu không ghi rõ.
"""
from __future__ import annotations

from typing import Any, Sequence

from .core.db import fetch_all, fetch_one, fetch_value, transaction
from .core.errors import KhongTimThay, XungDdot
from .core.pagination import Trang, cot_sap_xep, escape_like, huong_sap_xep

#: Thứ tự cột được phép sắp xếp cho từng bảng.
SAP_XEP_CHO_PHEP: dict[str, list[str]] = {
    'customers': ['id', 'name', 'phone', 'created_at'],
    'vehicles': ['id', 'plate', 'brand', 'model', 'year', 'vin', 'color',
                 'odometer', 'created_at'],
    'appointments': ['id', 'scheduled_at', 'status', 'created_at'],
    'services': ['id', 'name', 'price', 'created_at'],
    'parts': ['id', 'name', 'price', 'stock', 'created_at'],
    'users': ['id', 'username', 'full_name', 'role', 'is_active'],
    'repair_orders': ['id', 'status', 'created_at'],
    'invoices': ['id', 'status', 'total', 'created_at'],
    'ai_results': ['id', 'kind', 'review_status', 'created_at'],
    'payments': ['id', 'amount', 'method', 'paid_at'],
    'repair_order_items': ['id', 'qty', 'unit_price'],
    'intake_records': ['id', 'repair_order_id', 'created_at'],
    'quotations': ['id', 'status', 'total', 'created_at'],
    'quotation_items': ['id', 'qty', 'unit_price'],
    'shop_products': ['id', 'name', 'price', 'stock', 'created_at'],
}


# ---------------------------------------------------------------------------
# Truy vấn danh sách có phân trang
# ---------------------------------------------------------------------------
#: Mệnh đề FROM chuẩn cho từng bảng. Nhiều màn hình cần tên khách, biển số…
#: nên phải JOIN; đặt sẵn ở đây để các nơi gọi không phải lặp lại JOIN và để
#: câu `SELECT COUNT(*)` dùng cùng một điều kiện với câu lấy dữ liệu.
FROM_MAC_DINH: dict[str, str] = {
    'vehicles': 'vehicles v JOIN customers c ON c.id = v.customer_id',
    'appointments': ('appointments a JOIN customers c ON c.id = a.customer_id'
                     ' JOIN vehicles v ON v.id = a.vehicle_id'),
    'repair_orders': ('repair_orders r JOIN vehicles v ON v.id = r.vehicle_id'),
    'intake_records': ('intake_records i JOIN repair_orders r ON r.id = i.repair_order_id'
                       ' JOIN vehicles v ON v.id = r.vehicle_id'),
    'quotations': ('quotations q JOIN repair_orders r ON r.id = q.repair_order_id'
                   ' JOIN vehicles v ON v.id = r.vehicle_id'),
    'invoices': ('invoices i JOIN repair_orders r ON r.id = i.repair_order_id'
                 ' JOIN vehicles v ON v.id = r.vehicle_id'
                 ' JOIN customers c ON c.id = v.customer_id'),
    'ai_results': ('ai_results a'
                   ' LEFT JOIN repair_orders r ON r.id = a.repair_order_id'
                   ' LEFT JOIN vehicles v ON v.id = r.vehicle_id'
                   ' LEFT JOIN users us ON us.id = a.reviewed_by'),
    'shop_products': 'shop_products p JOIN shop_categories c ON c.id = p.category_id',
}


def _cot_sap_xep_theo_danh_sach(ten_cot: str, cot: Sequence[str]) -> str:
    """Tìm cột tương ứng trong danh sách đã chọn.

    Khi câu truy vấn có JOIN, các cột thường viết kèm tiền tố bảng (`v.id`).
    `ORDER BY id` khi đó sẽ báo "ambiguous column name", nên phải sắp xếp theo
    đúng biểu thức đã chọn.
    """
    for c in cot:
        if c.split('.')[-1].strip() == ten_cot:
            return c
    return cot[0] if cot else 'id'


def truy_van_danh_sach(bang: str, *, cot: Sequence[str], dieu_kien: str = '',
                       tham_so: Sequence = (), sap_xep: str | None = None,
                       huong: str | None = None, trang: Trang | None = None,
                       mac_dinh_sap_xep: str = 'id',
                       from_clause: str | None = None) -> tuple[list[dict], int]:
    """Trả về (các dòng, tổng số bản ghi khớp điều kiện).

    `bang` là tên bảng chính và phải có trong `SAP_XEP_CHO_PHEP`. Mệnh đề FROM
    lấy từ `FROM_MAC_DINH`, truyền `from_clause` để ghi đè khi cần.
    """
    cot = list(cot)
    if bang not in SAP_XEP_CHO_PHEP:
        raise ValueError('bảng không cho phép truy vấn danh sách: %s' % bang)
    cot_sap = cot_sap_xep(sap_xep, SAP_XEP_CHO_PHEP[bang], mac_dinh_sap_xep)
    cot_sap = _cot_sap_xep_theo_danh_sach(cot_sap, cot)
    tr = trang or Trang()
    frm = from_clause or FROM_MAC_DINH.get(bang, bang)

    where = (' WHERE ' + dieu_kien) if dieu_kien else ''
    tong = int(fetch_value('SELECT COUNT(*) FROM %s%s' % (frm, where),
                           tuple(tham_so), 0) or 0)
    tr = tr.clamp(tong)
    sql = 'SELECT %s FROM %s%s ORDER BY %s %s LIMIT ? OFFSET ?' % (
        ', '.join(cot), frm, where, cot_sap, huong_sap_xep(huong))
    dong = fetch_all(sql, tuple(tham_so) + (tr.moi_trang, tr.bat_dau))
    return dong, tong


def tim_theo_dien_kien(bang: str, cot: Sequence[str], dieu_kien: str,
                       tham_so: Sequence, trang: Trang, sap_xep: str | None = None,
                       huong: str | None = None) -> tuple[list[dict], int]:
    return truy_van_danh_sach(bang, cot=cot, dieu_kien=dieu_kien, tham_so=tham_so,
                              sap_xep=sap_xep, huong=huong, trang=trang)


def _kiem_tra_bang(bang: str) -> str:
    """Chỉ chấp nhận tên bảng có trong danh sách cho phép.

    Tên bảng không nối vào SQL được bằng tham số, nên thay vì tin lời người
    gọi, tầng này tự đối chiếu với danh sách hằng số.
    """
    if bang not in SAP_XEP_CHO_PHEP:
        raise ValueError('bảng không cho phép truy vấn: %s' % bang)
    return bang


# ---------------------------------------------------------------------------
# Thêm / sửa / xoá
# ---------------------------------------------------------------------------
def them(bang: str, du_lieu: dict) -> int:
    bang = _kiem_tra_bang(bang)
    if not du_lieu:
        raise ValueError('không có dữ liệu để thêm')
    cot = ', '.join(du_lieu)
    phat = ', '.join('?' * len(du_lieu))
    with transaction() as c:
        return int(c.execute('INSERT INTO %s (%s) VALUES (%s)' % (bang, cot, phat),
                             tuple(du_lieu.values())).lastrowid)


def sua(bang: str, khoa: int, du_lieu: dict) -> int:
    bang = _kiem_tra_bang(bang)
    if not du_lieu:
        return 0
    sets = ', '.join('%s = ?' % c for c in du_lieu)
    with transaction() as c:
        return c.execute('UPDATE %s SET %s WHERE id = ?' % (bang, sets),
                         tuple(du_lieu.values()) + (khoa,)).rowcount


def xoa(bang: str, khoa: int) -> int:
    bang = _kiem_tra_bang(bang)
    with transaction() as c:
        return c.execute('DELETE FROM %s WHERE id = ?' % bang, (khoa,)).rowcount


def lay_mot(bang: str, khoa: int, cot: Sequence[str] = ('*',)) -> dict | None:
    bang = _kiem_tra_bang(bang)
    return fetch_one('SELECT %s FROM %s WHERE id = ?' % (', '.join(cot), bang), (khoa,))


def bat_bien(unique: bool) -> str:
    return ''


def kiem_tra_trung(bang: str, cot: str, gia_tri, bo_sanh: int | None = None) -> bool:
    bang = _kiem_tra_bang(bang)
    sql = 'SELECT 1 FROM %s WHERE %s = ?' % (bang, cot)
    p = [gia_tri]
    if bo_sanh is not None:
        sql += ' AND id <> ?'
        p.append(bo_sanh)
    return fetch_one(sql, tuple(p)) is not None


def yeu_cau_co(bang: str, khoa: int, nhan: str) -> dict:
    ban_ghi = lay_mot(bang, khoa)
    if ban_ghi is None:
        raise KhongTimThay('Không tìm thấy %s.' % nhan)
    return ban_ghi


# ---------------------------------------------------------------------------
# Truy vấn phục vụ nghiệp vụ
# ---------------------------------------------------------------------------
def khach_hang_theo_id(khoa: int) -> dict | None:
    return fetch_one('SELECT id, name, phone FROM customers WHERE id = ?', (khoa,))


def phuong_tien_theo_id(khoa: int) -> dict | None:
    return fetch_one(
        'SELECT v.id, v.plate, v.brand, v.model, v.year, v.customer_id, c.name AS khach'
        ' FROM vehicles v JOIN customers c ON c.id = v.customer_id WHERE v.id = ?', (khoa,))


def dich_vue_theo_id(khoa: int) -> dict | None:
    return fetch_one('SELECT id, name, price, description, is_active FROM services'
                     ' WHERE id = ?', (khoa,))


def phu_tung_theo_id(khoa: int) -> dict | None:
    return fetch_one('SELECT id, name, price, stock, description, is_active FROM parts'
                     ' WHERE id = ?', (khoa,))


def lua_chon_khach() -> list[dict]:
    return fetch_all('SELECT id, name FROM customers ORDER BY name')


def lua_chon_xe() -> list[dict]:
    return fetch_all('SELECT id, plate, brand, model FROM vehicles WHERE is_active = 1'
                     ' ORDER BY plate')


def lua_chon_dich_vu() -> list[dict]:
    return fetch_all('SELECT id, name, price FROM services WHERE is_active = 1 ORDER BY name')


def lua_chon_phu_tung() -> list[dict]:
    return fetch_all('SELECT id, name, price, stock FROM parts WHERE is_active = 1'
                     ' ORDER BY name')


def lua_chon_ky_thuat_vien() -> list[dict]:
    return fetch_all("SELECT id, full_name FROM users WHERE role = 'TECHNICIAN'"
                     ' AND is_active = 1 ORDER BY full_name')


def fetch_all_phieu(limit: int = 40) -> list[dict]:
    """Danh sách phiếu chưa huỷ, dùng để chọn phiếu khi tạo báo giá nháp."""
    return fetch_all(
        'SELECT r.id, v.plate FROM repair_orders r'
        ' JOIN vehicles v ON v.id = r.vehicle_id'
        " WHERE r.status <> 'CANCELLED' ORDER BY r.id DESC LIMIT ?", (limit,))


def dem_ban_ghi(bang: str, dieu_kien: str = '', tham_so: Sequence = ()) -> int:
    bang = _kiem_tra_bang(bang)
    where = (' WHERE ' + dieu_kien) if dieu_kien else ''
    return int(fetch_value('SELECT COUNT(*) FROM %s%s' % (bang, where),
                           tuple(tham_so), 0) or 0)


def co_ban_ghi(bang: str, dieu_kien: str = '', tham_so: Sequence = ()) -> bool:
    bang = _kiem_tra_bang(bang)
    where = (' WHERE ' + dieu_kien) if dieu_kien else ''
    return fetch_value('SELECT 1 FROM %s%s LIMIT 1' % (bang, where),
                       tuple(tham_so)) is not None


# ---------------------------------------------------------------------------
# Người dùng
# ---------------------------------------------------------------------------
def nguoi_dung_theo_username(username: str) -> dict | None:
    return fetch_one('SELECT * FROM users WHERE username = ?', (username,))


def nguoi_dung_theo_id(khoa: int) -> dict | None:
    return fetch_one('SELECT id, username, full_name, email, role, is_active, auth_version'
                     ' FROM users WHERE id = ?', (khoa,))


def danh_sach_nguoi_dung(trang: Trang, *, q: str = '', vai_tro: str = '',
                         dang_hoat_dong: str = '', sap_xep: str | None = None,
                         huong: str | None = None) -> tuple[list[dict], int]:
    dieu_kien, tham_so = [], []
    if q:
        dieu_kien.append('(username LIKE ? ESCAPE \'\\\' OR full_name LIKE ? ESCAPE \'\\\')')
        tham_so += ['%%%s%%' % escape_like(q)] * 2
    if vai_tro:
        dieu_kien.append('role = ?')
        tham_so.append(vai_tro)
    if dang_hoat_dong in ('0', '1'):
        dieu_kien.append('is_active = ?')
        tham_so.append(int(dang_hoat_dong))
    return truy_van_danh_sach(
        'users', cot=('id', 'username', 'full_name', 'email', 'role', 'is_active'),
        dieu_kien=' AND '.join(dieu_kien), tham_so=tham_so, trang=trang,
        sap_xep=sap_xep, huong=huong, mac_dinh_sap_xep='username')


def tang_phien_ban(user_id: int) -> int:
    """Làm mất hiệu lực mọi phiên đang mở của tài khoản."""
    with transaction() as c:
        c.execute('UPDATE users SET auth_version = auth_version + 1 WHERE id = ?', (user_id,))
        r = c.execute('SELECT auth_version FROM users WHERE id = ?', (user_id,)).fetchone()
        return int(r[0]) if r else 1