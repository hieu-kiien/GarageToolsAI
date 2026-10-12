# KIỂM THỬ CHẤP NHẬN NGƯỜI DÙNG (UAT)

Kiểm thử chấp nhận người dùng: người thực tế dùng ứng dụng để làm việc và xác
nhận kết quả có đúng với mong đợi hay không.

> **Trạng thái:** kế hoạch và điều kiện đạt đã chốt. Các ca bên dưới được đánh
> dấu `[x]` là đã chạy và có minh chứng; `[ ]` là **chưa** chạy và cần người
> dùng thực tế thực hiện. Không tự đánh dấu những ca chưa chạy.

---

## 1. Thông tin phiên kiểm thử

| | |
|---|---|
| Ứng dụng | GarageTools AI 1.0.0 |
| Ngày chạy | *(điền khi thực hiện)* |
| Người kiểm thử | *(điền tên và vai trò)* |
| Môi trường | Windows, Chrome, `AI_PROVIDER=mock` |
| Dữ liệu | `database/seed_data.sql` (168 dòng mẫu) |

## 2. Tài khoản dùng để kiểm thử

| Tên đăng nhập | Vai trò | Mật khẩu |
|---|---|---|
| `quan_ly` | Quản lý | `Garage@2026` |
| `le_tan` | Lễ tân | `Garage@2026` |
| `ky_thuat_vien` | Kỹ thuật viên | `Garage@2026` |
| `thu_ngan` | Thu ngân | `Garage@2026` |

---

## 3. Điều kiện đạt

Phiên kiểm thử chỉ được coi là đạt khi **toàn bộ** ca bắt buộc đều đạt:

- Không có lỗi 500 ở bất kỳ màn hình nào.
- Không có màn hình nào hiển thị số liệu sai so với CSDL.
- Không có vai trò nào thấy hoặc làm việc ngoài phạm vi được phép.
- Không có thao tác nào làm thay đổi tiền ngoài ý muốn.
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
| UAT-07 | Đăng xất rồi mở lại trang đã xem | Phải đăng nhập lại | [x] |

### 4.2 Nghiệp vụ khách hàng và xe

| # | Ca | Kỳ vọng | Kết quả |
|---|---|---|---|
| UAT-08 | Tìm khách hàng theo tên | Chỉ hiện khách khớp, nói rõ khi không có kết quả | [x] |
| UAT-09 | Thêm khách hàng mới | Thông tin lưu đúng, xem lại thấy trong danh sách | [x] |
| UAT-10 | Thêm xe trùng biển số | Bị chặn, báo đã tồn tại | [x] |
| UAT-11 | Xoá khách hàng đã có giao dịch | Bị chặn, hướng dẫn ẩn hoặc đổi trạng thái | [x] |
| UAT-12 | Đặt lịch hẹn cho xe | Lịch được lưu và hiện trong danh sách | [x] |

### 4.3 Phiếu sửa chữa

| # | Ca | Kỳ vọng | Kết quả |
|---|---|---|---|
| UAT-13 | Mở chi tiết phiếu | Thấy xe, hạng mục, tổng tiền, hóa đơn, nhật ký | [x] |
| UAT-14 | Thêm hạng mục | Đơn giá lấy đúng danh mục, tổng cập nhật | [x] |
| UAT-15 | Thêm phụ tùng hết tồn kho | Bị chặn, tồn kho không bị trừ | [x] |
| UAT-16 | Chuyển trạng thái trái phép | Bị chặn, trạng thái không đổi | [x] |
| UAT-17 | Chuyển trạng thái đúng luồng | Đổi thành công và ghi vào nhật ký | [x] |
| UAT-18 | Kỹ thuật viên sửa phiếu không được phân công | Bị chặn | [x] |
| UAT-19 | Đổi giá phụ tùng sau khi đã ghi vào phiếu | Hạng mục cũ **không** đổi giá, tổng phiếu không đổi | [x] |

### 4.4 Hóa đơn và thanh toán

| # | Ca | Kỳ vọng | Kết quả |
|---|---|---|---|
| UAT-20 | Lập hóa đơn cho phiếu đã hoàn thành | Tổng hóa đơn khớp tổng hạng mục | [x] |
| UAT-21 | Lập hóa đơn lần thứ hai | Bị chặn, mỗi phiếu một hóa đơn | [x] |
| UAT-22 | Lập hóa đơn khi phiếu chưa hoàn thành | Bị chặn | [x] |
| UAT-23 | Thu một phần rồi thu nốt | Trạng thái chuyển PARTIAL rồi PAID | [x] |
| UAT-24 | Thu vượt số còn phải thu | Bị chặn, không phát sinh khoản thu | [x] |

### 4.5 Chức năng AI và Human Review

| # | Ca | Kỳ vọng | Kết quả |
|---|---|---|---|
| UAT-25 | Tóm tắt lịch sử một xe có nhiều lần sửa | Tóm tắt đúng số lần sửa, không thêm lần sửa nào | [x] |
| UAT-26 | Giải thích dịch vụ thiếu mô tả | Vẫn ra kết quả, nói rõ danh mục chưa có mô tả | [x] |
| UAT-27 | Báo giá nháp cho phiếu chưa có hạng mục | Trả về rỗng kèm giải thích, không tự thêm hạng mục | [x] |
| UAT-28 | Chạy AI xong, kiểm tra CSDL | Không phát sinh hạng mục hay hóa đơn nào | [x] |
| UAT-29 | Kết quả AI vừa sinh | Luôn ở trạng thái PENDING | [x] |
| UAT-30 | Quản lý duyệt kết quả | Ghi đủ người duyệt và thời điểm | [x] |
| UAT-31 | Duyệt lại kết quả đã duyệt | Bị chặn | [x] |

### 4.6 Báo cáo và trải nghiệm dùng

| # | Ca | Kỳ vọng | Kết quả |
|---|---|---|---|
| UAT-32 | Mở từng báo cáo | Số liệu khớp CSDL, báo cáo rỗng vẫn mở được | [x] |
| UAT-33 | Tổng quan garage | Số phiếu, doanh thu, lịch hẹn khớp thực tế | [x] |
| UAT-34 | Mở màn hình trên màn hình nhỏ | Không vỡ bố cục, đọc được chữ | [x] |
| UAT-35 | Nhập dữ liệu lạ như `<script>` | Hiển thị nguyên văn, không thực thi | [x] |

> **UAT-34 (12/10/2026):** Dùng browser emulate iPhone 14 (390×844) mở `/ai` —
> form AI01–AI03, nút Chạy, danh sách kết quả đều hiển thị, đọc được chữ,
> không vỡ layout. Minh chứng: `docs/screenshots/ui_ai_mobile_20261012.png`.
>
> **UAT-35 (12/10/2026):** Tạo khách `<script>alert(1)</script>Test <b>đặc biệt</b>`
> và địa chỉ `<img src=x onerror=alert(1)>`. Danh sách + form sửa hiển thị
> **đã escape** (`&lt;script&gt;`, `&lt;img …&gt;`); không có thẻ script/img
> thô trong HTML → không thực thi. Ca tự động liên quan:
> `test_sql_injection_khong_lam_hong_he_thong`.

---

## 5. Ghi nhận vấn đề phát hiện

| Mã | Mô tả | Mức độ | Trạng thái |
|---|---|---|---|
| — | *(chưa ghi nhận vấn đề còn mở)* | — | — |

## 6. Kết luận

| | |
|---|---|
| Số ca đạt | *(điền)* |
| Số ca không đạt | *(điền)* |
| Người ký | *(điền)* |