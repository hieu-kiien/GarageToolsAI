# -*- coding: utf-8 -*-
"""Truy cập SQLite.

Ba điểm kỹ thuật quan trọng, cả ba đều vì lý do hiệu năng và an toàn dữ liệu:

1. **Transaction đọc-rồi-ghi phải dùng `BEGIN IMMEDIATE`.** SQLite chỉ cho
   một người ghi tại một thời điểm. Nếu dùng transaction trì hoãn (mặc định),
   hai tiến trình có thể cùng đọc một số dư, rồi cùng ghi, và một bên thất bại
   hoặc — tệ hơn — cả hai đều ghi sai. `BEGIN IMMEDIATE` chiếm khoá ghi ngay
   từ đầu nên loại bỏ đúng lớp lỗi đó (xem https://sqlite.org/isolation.html).

2. **Mọi câu lệnh truy vấn đều qua tham số.** Tên bảng và tên cột đến từ mã,
   không đến từ người dùng; cột sắp xếp luôn đi qua danh sách cho phép.

3. **`PRAGMA foreign_keys = ON` phải bật ở mỗi kết nối** vì SQLite không bật
   sẵn và đặt lại khi đóng.
"""
from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .config import get_settings
from .errors import AppError

_settings = get_settings()

_local = threading.local()
_write_lock = threading.RLock()      # tuần tự hoá ghi trong phạm vi tiến trình
_tat_ca_ket_noi: set = set()          # để đóng được cả kết nối của luồng khác
_khoa = threading.Lock()

SQL_CHON_1 = 'SELECT 1 AS ok'


def _new_connection() -> sqlite3.Connection:
    path = Path(_settings.DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    # isolation_level=None tắt cơ chế tự mở transaction của thư viện, để
    # BEGIN/COMMIT do ta kiểm soát được tôn trọng đúng như viết ra.
    conn = sqlite3.connect(
        str(path),
        timeout=_settings.DB_BUSY_TIMEOUT_MS / 1000.0,
        isolation_level=None,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode = WAL')       # đọc không chặn ghi
    conn.execute('PRAGMA synchronous = NORMAL')     # an toàn với sập máy
    conn.execute('PRAGMA foreign_keys = ON')        # bảo vệ lịch sử
    conn.execute('PRAGMA busy_timeout = %d' % _settings.DB_BUSY_TIMEOUT_MS)
    conn.execute('PRAGMA temp_store = MEMORY')
    with _khoa:
        _tat_ca_ket_noi.add(conn)
    return conn


def connection() -> sqlite3.Connection:
    """Kết nối dùng chung theo luồng. Mỗi luồng có một kết nối riêng."""
    c = getattr(_local, 'conn', None)
    if c is None:
        c = _new_connection()
        _local.conn = c
    return c


def dong_ket_noi() -> None:
    c = getattr(_local, 'conn', None)
    if c is not None:
        _local.conn = None
        with _khoa:
            _tat_ca_ket_noi.discard(c)
        try:
            c.close()
        except sqlite3.Error:
            pass


def dong_tat_ca_ket_noi() -> None:
    """Đóng mọi kết nối của mọi luồng.

    Cần khi chuyển sang một tệp CSDL khác (kiểm thử, hoặc đổi cấu hình lúc
    chạy) — nếu không, Windows sẽ không cho xoá tệp CSDL cũ.
    """
    _local.conn = None
    with _khoa:
        ket_noi = list(_tat_ca_ket_noi)
        _tat_ca_ket_noi.clear()
    for c in ket_noi:
        try:
            c.close()
        except sqlite3.Error:
            pass


# ---------------------------------------------------------------------------
# Truy vấn chỉ đọc
# ---------------------------------------------------------------------------
def _rows(cur: sqlite3.Cursor) -> list[dict[str, Any]]:
    return [dict(r) for r in cur.fetchall()]


def fetch_all(sql: str, params: Sequence | dict = ()) -> list[dict[str, Any]]:
    return _rows(connection().execute(sql, params))


def fetch_one(sql: str, params: Sequence | dict = ()) -> dict[str, Any] | None:
    r = connection().execute(sql, params).fetchone()
    return dict(r) if r is not None else None


def fetch_value(sql: str, params: Sequence | dict = (), mac_dinh=None):
    r = connection().execute(sql, params).fetchone()
    if r is None:
        return mac_dinh
    v = r[0]
    return mac_dinh if v is None else v


# ---------------------------------------------------------------------------
# Ghi trong transaction
# ---------------------------------------------------------------------------
@contextmanager
def transaction(*, chi_doc: bool = False) -> Iterator[sqlite3.Connection]:
    """Mở transaction. Mặc định dùng `BEGIN IMMEDIATE` cho mọi thao tác ghi.

    `_write_lock` chỉ dùng khi nhiều luồng trong cùng tiến trình tranh nhau;
    `busy_timeout` loại tranh chấp giữa nhiều tiến trình.
    """
    conn = connection()
    if chi_doc:
        conn.execute('BEGIN')
        try:
            yield conn
        except Exception:
            conn.execute('ROLLBACK')
            raise
        conn.execute('COMMIT')
        return

    with _write_lock:
        for i in range(5):
            try:
                conn.execute('BEGIN IMMEDIATE')
                break
            except sqlite3.OperationalError as e:
                if 'locked' not in str(e) and 'busy' not in str(e):
                    raise
                if i == 4:
                    raise AppError('Hệ thống đang bận. Vui lòng thử lại sau.') from e
        try:
            yield conn
            conn.execute('COMMIT')
        except Exception:
            try:
                conn.execute('ROLLBACK')
            except sqlite3.Error:
                pass
            raise


# ---------------------------------------------------------------------------
# Ghi đơn lẻ ngoài transaction tùy biến
# ---------------------------------------------------------------------------
def execute(sql: str, params: Sequence | dict = ()) -> int:
    with transaction() as c:
        return c.execute(sql, params).rowcount


def insert(sql: str, params: Sequence | dict = ()) -> int:
    with transaction() as c:
        return int(c.execute(sql, params).lastrowid)


def insert_nhieu(sql: str, hang: Sequence[Sequence]) -> int:
    if not hang:
        return 0
    with transaction() as c:
        c.executemany(sql, hang)
        return len(hang)


# ---------------------------------------------------------------------------
# Tiện ích dùng lại
# ---------------------------------------------------------------------------
def scalar_total(so: int | None) -> int:
    return int(so or 0)


def tong_phieu(phieu_id: int) -> int:
    """Tổng tiền phiếu luôn tính lại từ hạng mục, không đọc giá trị cũ."""
    return int(fetch_value(
        'SELECT COALESCE(SUM(unit_price * qty), 0) FROM repair_order_items'
        ' WHERE repair_order_id = ?', (phieu_id,), 0) or 0)


def da_thu(hd_id: int) -> int:
    return int(fetch_value(
        'SELECT COALESCE(SUM(amount), 0) FROM payments WHERE invoice_id = ?',
        (hd_id,), 0) or 0)


def con_phai_thu(hd_id: int) -> int:
    hd = fetch_one('SELECT total FROM invoices WHERE id = ?', (hd_id,))
    if not hd:
        return 0
    return int(hd['total']) - da_thu(hd_id)


def phieu_da_quyet_toan(phieu_id: int) -> bool:
    """Phiếu đã có hóa đơn thì không được thêm/bớt hạng mục nữa."""
    return fetch_one('SELECT 1 FROM invoices WHERE repair_order_id = ?', (phieu_id,)) is not None


def ban_ghi_da_bi_tham_chieu(bang: str, khoa: int) -> bool:
    """Bản ghi đã phát sinh giao dịch thì không cho xoá vĩnh viễn."""
    if bang not in _BANG_DUOC_XOA:
        raise AppError('Bảng không được phép xoá trực tiếp.')
    for cot_khoa_ngoai in _BANG_DUOC_XOA[bang]:
        bang_con, cot = cot_khoa_ngoai
        if fetch_value('SELECT 1 FROM %s WHERE %s = ? LIMIT 1' % (bang_con, cot), (khoa,)):
            return True
    return False


_BANG_DUOC_XOA = {
    'customers': [('vehicles', 'customer_id'), ('appointments', 'customer_id'),
                  ('repair_orders', 'vehicle_id'), ('shop_orders', 'customer_id')],
    'vehicles': [('appointments', 'vehicle_id'), ('repair_orders', 'vehicle_id')],
    'services': [('repair_order_items', 'service_id')],
    'parts': [('repair_order_items', 'part_id')],
    'shop_categories': [('shop_products', 'category_id')],
    'shop_products': [('shop_order_items', 'product_id')],
}


def kiem_tra_khoa_ngoai(conn: sqlite3.Connection | None = None) -> bool:
    c = conn or connection()
    return c.execute('PRAGMA foreign_keys').fetchone()[0] == 1


def integrity_check() -> str:
    return str(fetch_value('PRAGMA integrity_check', (), 'unknown'))


def db_san_sang() -> bool:
    try:
        return fetch_value(SQL_CHON_1, (), 0) == 1
    except sqlite3.Error:
        return False


def khoi_tao() -> Path:
    """Dựng lại CSDL từ schema và dữ liệu mẫu."""
    db = Path(_settings.DATABASE_PATH)
    dong_tat_ca_ket_noi()
    if db.exists():
        db.unlink()
    for p in db.parent.glob(db.name + '-*'):     # các tệp phụ của WAL
        p.unlink(missing_ok=True)
    conn = _new_connection()
    try:
        conn.executescript(_settings.SCHEMA_FILE.read_text(encoding='utf-8'))
        n = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        if n == 0:
            conn.executescript(_settings.SEED_FILE.read_text(encoding='utf-8'))
        conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    finally:
        conn.close()
    return db


def dat_lai_dich_vu(path: str | None = None) -> None:
    """Trỏ ứng dụng sang một tệp CSDL khác và mở lại kết nối.

    Kiểm thử dùng hàm này để chạy trên CSDL tạm. Phải sửa đối tượng trả về
    của `get_settings()` — đặt thuộc tính lên *module* `config.settings` sẽ
    không có tác dụng gì vì ứng dụng đọc qua `get_settings()`.
    """
    global _settings
    _settings = get_settings()
    if path:
        _settings.DATABASE_PATH = str(path)
    dong_tat_ca_ket_noi()