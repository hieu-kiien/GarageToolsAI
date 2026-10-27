# -*- coding: utf-8 -*-
"""Chụp ảnh màn hình thật của giao diện chính thức React 19 + TanStack Start.

Cách chạy:
    python -B docs/chup_man_hinh.py

Nếu Backend (cổng 8000) hoặc Frontend Vite (cổng 5173) chưa bật, kịch bản sẽ
tự động khởi chạy cả hai dịch vụ nền, chờ sẵn sàng, chụp đủ 18 màn hình vào
thư mục screenshots/ (kèm ảnh minh chứng AI vào docs/screenshots/), cập nhật
docs/BANG_ANH.md rồi tự dọn tiến trình nền.
"""
import datetime
import io
import os
import socket
import subprocess
import sys
import time
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(BASE)
FRONTEND_DIR = os.path.join(ROOT, "frontend")
OUT = os.path.join(BASE, "screenshots")
DOCS_SHOTS = os.path.join(BASE, "docs", "screenshots")

BACKEND_URL = os.environ.get("GARAGE_BACKEND_URL", "http://127.0.0.1:8000")
FRONTEND_URL = os.environ.get("GARAGE_FRONTEND_URL", "http://127.0.0.1:5173")
MAT_KHAU = "Garage@2026"

# (tên tệp, đường dẫn React, tài khoản đăng nhập, mô tả)
TRANG = [
    ("01_dang_nhap", "/login", None, "Trang đăng nhập (React 19 + shadcn/ui)"),
    ("02_dashboard", "/", "quan_ly", "Tổng quan xưởng (KPI Bento & Biểu đồ doanh thu Recharts)"),
    ("03_phieu_sua_chua", "/repair-orders", "quan_ly", "Danh sách phiếu sửa chữa"),
    ("04_chi_tiet_phieu", "/repair-orders/1", "quan_ly", "Chi tiết phiếu sửa chữa, nghiệm thu & sổ cái"),
    ("05_khach_hang", "/customers", "le_tan", "Quản lý khách hàng & hồ sơ phương tiện"),
    ("06_phuong_tien", "/workflow", "quan_ly", "Bảng điều phối xưởng Kanban 6 trạng thái"),
    ("07_lich_hen", "/appointments", "le_tan", "Quản lý lịch hẹn dịch vụ"),
    ("08_danh_muc", "/catalog", "quan_ly", "Danh mục dịch vụ & đơn giá chuẩn"),
    ("09_tai_khoan", "/users", "quan_ly", "Quản lý tài khoản nhân viên & RBAC"),
    ("10_lich_su", "/quotations", "quan_ly", "Quản lý báo giá chính thức & áp dụng idempotent"),
    ("11_bao_cao", "/reports", "quan_ly", "Báo cáo doanh thu, năng suất KTV & thống kê AI"),
    ("12_ai", "/ai-review", "quan_ly", "Trung tâm trợ lý AI (AI01, AI02, AI03)"),
    ("13_duyet_ai", "/ai-review", "quan_ly", "Hàng đợi duyệt kết quả AI (Human-in-the-Loop)"),
    ("14_cua_hang", "/inventory", "quan_ly", "Kho phụ tùng & sổ cái xuất nhập tồn"),
    ("15_khong_co_quyen", "/users", "ky_thuat_vien", "Phân quyền RBAC: Kỹ thuật viên bị chặn truy cập"),
]

HEP = [
    ("16_responsive_dashboard", "/", "quan_ly", "Giao diện Tổng quan xưởng trên màn hình hẹp 390px"),
    ("17_responsive_phieu", "/repair-orders/1", "quan_ly", "Giao diện Chi tiết phiếu & Drawer trên màn hình hẹp 390px"),
]


def _cong_dang_mo(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def _cho_http(url: str, timeout: float = 30.0) -> bool:
    han = time.time() + timeout
    while time.time() < han:
        try:
            with urllib.request.urlopen(url, timeout=2.0) as resp:
                if resp.status < 500:
                    return True
        except Exception:
            pass
        time.sleep(0.4)
    return False


def _dang_nhap_react(page, tai_khoan: str):
    page.goto(FRONTEND_URL + "/", wait_until="domcontentloaded")
    page.wait_for_selector("#username", timeout=15000)
    page.fill("#username", tai_khoan)
    page.fill("#password", MAT_KHAU)
    page.click('button[type="submit"]')
    page.wait_for_selector("aside", timeout=15000)
    _cho_het_tai(page)


def _cho_het_tai(page, extra_ms: int = 650):
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    try:
        page.locator(".animate-spin").first.wait_for(state="detached", timeout=8000)
    except Exception:
        pass
    page.wait_for_timeout(extra_ms)


def chay():
    from playwright.sync_api import sync_playwright

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(DOCS_SHOTS, exist_ok=True)
    ngay = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    dong = []

    procs = []
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    try:
        if not _cong_dang_mo("127.0.0.1", 8000):
            if os.environ.get("GARAGE_RESET_DB", "1") != "0":
                subprocess.run(
                    [sys.executable, "-B", "database/init_db.py"],
                    cwd=BASE,
                    env=env,
                    check=True,
                )
            print("Dang khoi dong Backend FastAPI tai cong 8000...")
            p_back = subprocess.Popen(
                [sys.executable, "-B", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
                cwd=BASE,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            procs.append(p_back)
            if not _cho_http(BACKEND_URL + "/healthz", 25.0):
                raise RuntimeError("Khong khoi dong duoc Backend FastAPI tai cong 8000")

        if not _cong_dang_mo("127.0.0.1", 5173) and not _cong_dang_mo("localhost", 5173):
            print("Dang khoi dong Frontend React (Vite) tai cong 5173...")
            vite_bin = os.path.join(FRONTEND_DIR, "node_modules", "vite", "bin", "vite.js")
            p_front = subprocess.Popen(
                ["node", vite_bin, "dev", "--host", "127.0.0.1", "--port", "5173"],
                cwd=FRONTEND_DIR,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            procs.append(p_front)
            if not _cho_http("http://127.0.0.1:5173/", 35.0):
                raise RuntimeError("Khong khoi dong duoc Frontend Vite tai cong 5173")

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(channel="chrome", headless=True)
            except Exception:
                browser = p.chromium.launch(headless=True)

            for ten, duong_dan, tk, mo_ta in TRANG:
                ctx = browser.new_context(
                    viewport={"width": 1440, "height": 900},
                    device_scale_factor=1,
                )
                page = ctx.new_page()
                if tk:
                    _dang_nhap_react(page, tk)
                    page.goto(FRONTEND_URL + duong_dan, wait_until="domcontentloaded")
                    _cho_het_tai(page, 700)
                else:
                    page.goto(FRONTEND_URL + "/", wait_until="domcontentloaded")
                    page.wait_for_selector("#username", timeout=15000)
                    page.wait_for_timeout(400)

                # Tinh chỉnh tương tác cho màn hình Duyệt kết quả AI (13_duyet_ai)
                if ten == "13_duyet_ai":
                    nut_da_duyet = page.locator('button:has-text("Đã duyệt")')
                    if nut_da_duyet.count() > 0:
                        nut_da_duyet.first.click()
                        _cho_het_tai(page, 500)

                tep = os.path.join(OUT, ten + ".png")
                page.screenshot(path=tep, full_page=True)
                if ten == "13_duyet_ai":
                    page.screenshot(
                        path=os.path.join(DOCS_SHOTS, "ui_ai_duyet_20261012.png"),
                        full_page=True,
                    )
                dong.append((ten, duong_dan, tk or "-", mo_ta, page.title()))
                print("%-24s %-22s %s" % (ten, duong_dan, "OK"))
                ctx.close()

            # Màn hình hẹp 390x844 (Responsive Mobile)
            for ten, duong_dan, tk, mo_ta in HEP:
                ctx = browser.new_context(
                    viewport={"width": 390, "height": 844},
                    device_scale_factor=2,
                    is_mobile=True,
                    has_touch=True,
                )
                page = ctx.new_page()
                page.goto(FRONTEND_URL + "/", wait_until="domcontentloaded")
                page.wait_for_selector("#username", timeout=15000)
                page.fill("#username", tk)
                page.fill("#password", MAT_KHAU)
                page.click('button[type="submit"]')
                page.wait_for_timeout(800)
                page.goto(FRONTEND_URL + duong_dan, wait_until="domcontentloaded")
                _cho_het_tai(page, 700)

                if ten == "17_responsive_phieu":
                    # Mở thêm ngăn kéo điều hướng hoặc giữ bố cục phiếu trên mobile
                    pass

                tep = os.path.join(OUT, ten + ".png")
                page.screenshot(path=tep, full_page=False)
                dong.append((ten, duong_dan, tk, mo_ta, page.title()))
                print("%-24s %-22s %s" % (ten, duong_dan, "OK (390px)"))

                if ten == "16_responsive_dashboard":
                    page.goto(FRONTEND_URL + "/ai-review", wait_until="domcontentloaded")
                    _cho_het_tai(page, 600)
                    page.screenshot(
                        path=os.path.join(DOCS_SHOTS, "ui_ai_mobile_20261012.png"),
                        full_page=False,
                    )
                ctx.close()

            # 18_loi_thanh_toan: Cảnh báo lỗi nghiệp vụ khi thu vượt số còn phải thu trên /finance
            ctx = browser.new_context(viewport={"width": 1440, "height": 900})
            page = ctx.new_page()
            _dang_nhap_react(page, "quan_ly")
            page.goto(FRONTEND_URL + "/finance", wait_until="domcontentloaded")
            _cho_het_tai(page, 700)
            nut_thu = page.locator('button:has-text("Thu tiền")')
            if nut_thu.count() > 0:
                nut_thu.first.click()
                page.wait_for_timeout(400)
                o_tien = page.locator('div[role="dialog"] input[type="number"]')
                if o_tien.count() > 0:
                    o_tien.first.fill("99999999")
                    page.locator('div[role="dialog"] button:has-text("Xác nhận thu tiền")').click()
                    page.wait_for_timeout(600)
            page.screenshot(path=os.path.join(OUT, "18_loi_thanh_toan.png"), full_page=False)
            dong.append(
                (
                    "18_loi_thanh_toan",
                    "/finance",
                    "quan_ly",
                    "Cảnh báo chặn khi thanh toán vượt số tiền còn phải thu",
                    page.title(),
                )
            )
            print("%-24s %-22s %s" % ("18_loi_thanh_toan", "/finance", "OK"))
            ctx.close()
            browser.close()
    finally:
        for pr in procs:
            try:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pr.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                else:
                    pr.terminate()
                    pr.wait(timeout=5)
            except Exception:
                try:
                    pr.kill()
                except Exception:
                    pass

    return ngay, dong


def viet_bang(ngay, dong):
    with open(os.path.join(BASE, "docs", "BANG_ANH.md"), "w", encoding="utf-8") as f:
        f.write("<!-- Sinh tu dong boi docs/chup_man_hinh.py -->\n\n")
        f.write("| Hình | Màn hình | Vai trò | Đường dẫn |\n|---|---|---|---|\n")
        for ten, duong_dan, tk, mo_ta, _ in dong:
            f.write(
                "| ![%s](screenshots/%s.png) | %s | `%s` | `%s` |\n"
                % (mo_ta, ten, mo_ta, tk, duong_dan)
            )
        f.write(
            "\n> Chụp ngày %s trên giao diện React 19 + TanStack Start kết nối Backend FastAPI đang chạy, dữ liệu lấy từ `seed_data.sql`.\n"
            % ngay
        )
    return len(dong)


if __name__ == "__main__":
    ngay, ds = chay()
    viet_bang(ngay, ds)
    print("Da chup %d man hinh vao %s" % (len(ds), OUT))
    print("Da viet bang anh vao docs/BANG_ANH.md")