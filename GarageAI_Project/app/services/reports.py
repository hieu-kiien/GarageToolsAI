# -*- coding: utf-8 -*-
"""Dashboard và báo cáo.

Mọi số liệu đều đến từ CSDL, không có con số nào viết cứng trong mã.
Các hàm trả về đúng cấu trúc mà giao diện cần, không trả về `sqlite3.Row`.
"""
from __future__ import annotations

from .. import crud
from ..core.db import fetch_all, fetch_value


def tong_quan() -> dict:
    """Số liệu chính cho màn hình tổng quan."""
    return {
        'tong_phieu': int(fetch_value(
            "SELECT COUNT(*) FROM repair_orders WHERE status <> 'CANCELLED'", (), 0)),
        'dang_xu_ly': int(fetch_value(
            "SELECT COUNT(*) FROM repair_orders WHERE status IN"
            " ('RECEIVED','INSPECTING','ESTIMATING','REPAIRING')", (), 0)),
        'lich_hen': int(fetch_value(
            "SELECT COUNT(*) FROM appointments WHERE status IN"
            " ('SCHEDULED','CONFIRMED') AND scheduled_at >= datetime('now')", (), 0)),
        'da_thu': int(fetch_value("SELECT COALESCE(SUM(paid),0) FROM invoices", (), 0)),
        'chua_thu': int(fetch_value(
            "SELECT COALESCE(SUM(total - paid),0) FROM invoices"
            " WHERE status <> 'PAID'", (), 0)),
        'khach_hang': int(fetch_value('SELECT COUNT(*) FROM customers', (), 0)),
        'xe': int(fetch_value('SELECT COUNT(*) FROM vehicles', (), 0)),
        'cho_duyet_ai': int(fetch_value(
            "SELECT COUNT(*) FROM ai_results WHERE review_status = 'PENDING'", (), 0)),
    }


def phieu_theo_trang_thai() -> list[dict]:
    return fetch_all('SELECT status, COUNT(*) AS n FROM repair_orders'
                     ' GROUP BY status ORDER BY n DESC')


def phieu_moi_nhat(limit: int = 10) -> list[dict]:
    """Giới hạn số dòng để trang không phình theo dữ liệu."""
    return fetch_all(
        'SELECT r.id, r.status, r.created_at, r.technical_notes, v.plate'
        ' FROM repair_orders r JOIN vehicles v ON v.id = r.vehicle_id'
        ' ORDER BY r.created_at DESC LIMIT ?', (limit,))


def bao_cao_doanh_thu(so_thang: int = 6) -> list[dict]:
    return fetch_all(
        "SELECT strftime('%Y-%m', created_at) AS thang, COUNT(*) AS so_hoa_don,"
        ' COALESCE(SUM(total),0) AS tong, COALESCE(SUM(paid),0) AS da_thu'
        " FROM invoices WHERE status <> 'CANCELLED'"
        " GROUP BY thang ORDER BY thang DESC LIMIT ?", (so_thang,))


def bao_cao_dich_vu(limit: int = 15) -> list[dict]:
    return fetch_all(
        'SELECT s.name AS ten, SUM(i.qty) AS so_luong,'
        ' SUM(i.unit_price * i.qty) AS doanh_thu'
        ' FROM repair_order_items i'
        ' JOIN services s ON s.id = i.service_id'
        ' JOIN repair_orders r ON r.id = i.repair_order_id'
        " WHERE r.status <> 'CANCELLED'"
        ' GROUP BY s.id ORDER BY doanh_thu DESC LIMIT ?', (limit,))


def bao_cao_phu_tung(limit: int = 20) -> list[dict]:
    return fetch_all(
        'SELECT pt.name AS ten, SUM(i.qty) AS so_luong,'
        ' SUM(i.unit_price * i.qty) AS doanh_thu, pt.stock AS ton_kho'
        ' FROM repair_order_items i JOIN parts pt ON pt.id = i.part_id'
        ' JOIN repair_orders r ON r.id = i.repair_order_id'
        " WHERE r.status <> 'CANCELLED'"
        ' GROUP BY pt.id ORDER BY so_luong DESC LIMIT ?', (limit,))


def bao_cao_khach_hang(limit: int = 20) -> list[dict]:
    """Chỉ tính hoá đơn đã thu đủ; hóa đơn chưa thu không phải doanh thu."""
    return fetch_all(
        'SELECT c.id, c.name, COUNT(DISTINCT v.id) AS so_xe,'
        ' COUNT(DISTINCT r.id) AS so_lan_sua,'
        " COALESCE(SUM(CASE WHEN i.status = 'PAID' THEN i.total ELSE 0 END), 0)"
        ' AS tong_chi'
        ' FROM customers c'
        ' LEFT JOIN vehicles v ON v.customer_id = c.id'
        ' LEFT JOIN repair_orders r ON r.vehicle_id = v.id'
        ' LEFT JOIN invoices i ON i.repair_order_id = r.id'
        ' GROUP BY c.id ORDER BY tong_chi DESC LIMIT ?', (limit,))


def bao_cao_trang_thai() -> list[dict]:
    return fetch_all('SELECT status, COUNT(*) AS so_luong FROM repair_orders'
                     ' GROUP BY status ORDER BY so_luong DESC')


def lich_su(trang, *, q: str = '') -> tuple[list[dict], int]:
    """Tra cứu lịch sử theo biển số, tên khách hoặc số điện thoại."""
    dieu_kien, tham_so = ['1=1'], []
    if q:
        like = '%%%s%%' % q.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        dieu_kien.append(
            "(v.plate LIKE ? ESCAPE '\\' OR c.name LIKE ? ESCAPE '\\'"
            " OR c.phone LIKE ? ESCAPE '\\')")
        tham_so += [like, like, like]
    return crud.truy_van_danh_sach(
        'repair_orders',
        cot=('r.id', 'r.status', 'r.created_at', 'v.plate', 'v.brand', 'v.model',
             'c.name AS khach', 'c.phone', 'r.technician_id'),
        dieu_kien=' AND '.join(dieu_kien), tham_so=tham_so, trang=trang,
        sap_xep='created_at', huong='desc',
        from_clause=('repair_orders r JOIN vehicles v ON v.id = r.vehicle_id'
                     ' JOIN customers c ON c.id = v.customer_id'))