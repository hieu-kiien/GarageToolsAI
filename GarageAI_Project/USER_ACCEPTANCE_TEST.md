# KIỂM THỬ CHẤP NHẬN NGƯỜI DÙNG (UAT)

Kiểm thử chấp nhận người dùng: người thực tế dùng ứng dụng để làm việc và xác
nhận kết quả có đúng với mong đợi hay không.

> **Trạng thái:** Đã hoàn thành toàn bộ **35/35 ca kiểm thử** trên dữ liệu thực tế
> (kèm kiểm thử tự động `scripts/smoke.ps1` 31/31 và `scripts/e2e.ps1` 32/32).

---

## 1. Thông tin phiên kiểm thử

| | |
|---|---|
| Ứng dụng | GarageTools AI 1.0.0 (Backend FastAPI + Frontend React TanStack Start) |
| Ngày chạy | 14/10/2026 – 16/10/2026 |
| Người kiểm thử | Nhóm 23 — Học phần AIA331 (Đóng vai Quản lý, Lễ tân, Kỹ thuật viên, Thu ngân) |
| Môi trường | Windows 11, Chrome, Python 3.13 / SQLite 3.50, `AI_PROVIDER=mock` & `groq` (`openai/gpt-oss-120b`) |
| Dữ liệu | `database/seed_data.sql` (171 dòng mẫu, 21 bảng, 37 chỉ mục, đã áp đủ 5 migrations `001` → `005`) |

## 2. Tài khoản dùng để kiểm thử

| Tên đăng nhập | Vai trò | Mật khẩu |
|---|---|---|
| `quan_ly` | Quản lý (`MANAGER`) | `Garage@2026` |
| `le_tan` | Lễ tân (`RECEPTIONIST`) | `Garage@2026` |
| `ky_thuat_vien` | Kỹ thuật viên (`TECHNICIAN`) | `Garage@2026` |
| `thu_ngan` | Thu ngân (`CASHIER`) | `Garage@2026` |

---

## 3. Điều kiện đạt

Phiên kiểm thử chỉ được coi là đạt khi **toàn bộ** ca bắt buộc đều đạt:

- Không có lỗi 500 ở bất kỳ màn hình nào.
- Không có màn hình nào hiển thị số liệu sai so với CSDL.
- Không có vai trò nào thấy hoặc làm việc ngoài phạm vi được phép.
- Không có thao tác nào làm thay đổi tiền hoặc tồn kho ngoài ý muốn (`GET /api/stock/audit` rỗng).
- Người dùng tự làm được mọi ca mà không cần hỗ trợ của người phát triển.

---

## 4. Ca kiểm thử

### 4.1 Đăng nhập và phân quyền

| # | Ca | Kỳ vọng | Kết quả |
|---|---|---|---|
| UAT-01 | Đăng nhập bằng tài khoản đúng | Vào được tổng quan, thấy đúng tên và vai trò | [x] |
| UAT-02 | Đăng nhập sai mật khẩu | Báo chung, không tiết lộ tài khoản có hay không | [x] |
| UAT-03 | Chưa đăng nhập mà mở `/dashboard` | Chuyển về trang đăng nhập | [x] |
| UAT-04 | `ky_thuat_vien` mở `/users` | Bị chặn 403, nói rõ vai trò không được phép | [x] |
| UAT-05 | `le_tan` mở `/ai/results` | Bị chặn 403 | [x] |
| UAT-06 | `thu_ngan` mở `/repair-orders/new` | Bị chặn 403 | [x] |
| UAT-07 | Đăng xuất rồi mở lại trang đã xem | Phải đăng nhập lại | [x] |

### 4.2 Nghiệp vụ khách hàng và xe

| # | Ca | Kỳ vọng | Kết quả |
|---|---|---|---|
| UAT-08 | Tìm khách hàng theo tên | Chỉ hiện khách khớp, nói rõ khi không có kết quả | [x] |
| UAT-09 | Thêm khách hàng mới | Thông tin lưu đúng, xem lại thấy trong danh sách | [x] |
| UAT-10 | Thêm xe trùng biển số | Bị chặn, báo đã tồn tại | [x] |
| UAT-11 | Xoá khách hàng đã có giao dịch | Bị chặn, hướng dẫn ẩn hoặc đổi trạng thái | [x] |
| UAT-12 | Đặt lịch hẹn cho xe | Lịch được lưu và hiện trong danh sách | [x] |

### 4.3 Phiếu sửa chữa, báo giá và nghiệm thu

| # | Ca | Kỳ vọng | Kết quả |
|---|---|---|---|
| UAT-13 | Mở chi tiết phiếu | Thấy xe, biên bản tiếp nhận, hạng mục, báo giá, tổng tiền, hóa đơn, nhật ký | [x] |
| UAT-14 | Thêm hạng mục / áp dụng báo giá đã duyệt | Đơn giá lấy đúng danh mục, tổng cập nhật, tồn kho trừ đúng 1 lần qua sổ cái | [x] |
| UAT-15 | Thêm phụ tùng hết tồn kho | Bị chặn, tồn kho không bị trừ | [x] |
| UAT-16 | Chuyển trạng thái trái phép | Bị chặn, trạng thái không đổi | [x] |
| UAT-17 | Chuyển trạng thái đúng luồng & nghiệm thu | Đổi thành công, ghi vào nhật ký; nghiệm thu lần 2 bị chặn (409) | [x] |
| UAT-18 | Kỹ thuật viên sửa phiếu không được phân công | Bị chặn | [x] |
| UAT-19 | Đổi giá phụ tùng sau khi đã ghi vào phiếu | Hạng mục cũ **không** đổi giá, tổng phiếu không đổi | [x] |

### 4.4 Hóa đơn và thanh toán

| # | Ca | Kỳ vọng | Kết quả |
|---|---|---|---|
| UAT-20 | Lập hóa đơn cho phiếu đã hoàn thành | Tổng hóa đơn khớp tổng hạng mục | [x] |
| UAT-21 | Lập hóa đơn lần thứ hai | Bị chặn, mỗi phiếu một hóa đơn | [x] |
| UAT-22 | Lập hóa đơn khi phiếu chưa hoàn thành | Bị chặn | [x] |
| UAT-23 | Thu một phần rồi thu nốt (và huỷ khoản thu nhầm) | Trạng thái chuyển `PARTIAL` rồi `PAID`; huỷ khoản thu tính lại đúng `con_phai_thu` | [x] |
| UAT-24 | Thu vượt số còn phải thu | Bị chặn (409), không phát sinh khoản thu | [x] |

### 4.5 Chức năng AI và Human Review

| # | Ca | Kỳ vọng | Kết quả |
|---|---|---|---|
| UAT-25 | Tóm tắt lịch sử một xe có nhiều lần sửa | Tóm tắt đúng số lần sửa, không thêm lần sửa nào | [x] |
| UAT-26 | Giải thích dịch vụ thiếu mô tả | Vẫn ra kết quả, nói rõ danh mục chưa có mô tả | [x] |
| UAT-27 | Báo giá nháp cho phiếu chưa có hạng mục | Trả về rỗng kèm giải thích, không tự thêm hạng mục | [x] |
| UAT-28 | Chạy AI xong, kiểm tra CSDL | Không phát sinh hạng mục hay hóa đơn nào | [x] |
| UAT-29 | Kết quả AI vừa sinh | Luôn ở trạng thái `PENDING` | [x] |
| UAT-30 | Quản lý duyệt kết quả | Ghi đủ người duyệt (`reviewed_by`) và thời điểm (`reviewed_at`) | [x] |
| UAT-31 | Duyệt lại kết quả đã duyệt | Bị chặn | [x] |

### 4.6 Báo cáo và trải nghiệm dùng

| # | Ca | Kỳ vọng | Kết quả |
|---|---|---|---|
| UAT-32 | Mở từng báo cáo | Số liệu khớp CSDL, báo cáo rỗng vẫn mở được | [x] |
| UAT-33 | Tổng quan garage | Số phiếu, doanh thu, lịch hẹn khớp thực tế | [x] |
| UAT-34 | Mở màn hình trên màn hình nhỏ | Không vỡ bố cục, đọc được chữ | [x] |
| UAT-35 | Nhập dữ liệu lạ như `<script>` | Hiển thị nguyên văn (đã escape), không thực thi | [x] |

> **UAT-34 (12/10/2026):** Dùng browser emulate iPhone 14 (390×844) mở `/ai` và giao diện React responsive — form AI01–AI03, nút Chạy, menu ngăn kéo (drawer) và danh sách kết quả đều hiển thị rõ ràng, không vỡ layout. Minh chứng: `docs/screenshots/ui_ai_mobile_20261012.png`.
>
> **UAT-35 (12/10/2026):** Tạo khách `<script>alert(1)</script>Test <b>đặc biệt</b>` và địa chỉ `<img src=x onerror=alert(1)>`. Danh sách + form sửa hiển thị **đã escape** (`&lt;script&gt;`, `&lt;img …&gt;`); không có thẻ script/img thô trong HTML → không thực thi. Ca tự động liên quan: `test_sql_injection_khong_lam_hong_he_thong`.

---

## 5. Ghi nhận vấn đề phát hiện

| Mã | Mô tả | Mức độ | Trạng thái |
|---|---|---|---|
| — | Toàn bộ vấn đề phát hiện trong quá trình rà soát (P0-1→P0-11, P1-1→P1-9, FE-1→FE-15) đã được khắc phục triệt để trong `KEP_HOACH_HOAN_THIEN.md` | — | Đã đóng |

## 6. Kết luận

| | |
|---|---|
| Số ca đạt | **35 / 35 (100%)** |
| Số ca không đạt | **0** |
| Người ký | **Đại diện Nhóm 23 — Học phần AIA331 (Đã nghiệm thu ngày 16/10/2026)** |