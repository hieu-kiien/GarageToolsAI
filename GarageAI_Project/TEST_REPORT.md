# BÁO CÁO KIỂM THỬ — GarageTools AI

| | |
|---|---|
| Ngày chạy | 2026-10-12 12:00 |
| Môi trường | Python 3.13.14, SQLite 3.50.4 |
| Tổng số ca | **119** |
| Kết quả | **119 đạt / 0 lỗi** |

---

## 1. Phạm vi

Bộ kiểm thử gồm ba phần: ràng buộc và dữ liệu mẫu của cơ sở dữ liệu, quy
trình sao lưu/khôi phục, và toàn bộ ứng dụng web. Phần ứng dụng được kiểm
tra bằng cách gọi thật các đường dẫn HTTP trên một cơ sở dữ liệu tạm dựng
từ `schema.sql` và `seed_data.sql`, nên ca kiểm thử chạm đúng mã nguồn đang
chạy chứ không kiểm tra bản sao.

### Kiểm thử ràng buộc cơ sở dữ liệu

- Tệp: `tests/test_schema_constraints.py`
- Phạm vi: Đối chiếu mục 4.2 (danh sách bảng), mục 4.3 (ràng buộc) và mục 4.5 (dữ liệu mẫu).
- Kết quả: 37 ca, 37 đạt, 0 lỗi

### Kiểm thử sao lưu và khôi phục

- Tệp: `tests/test_backup_restore.py`
- Phạm vi: Đối chiếu quy trình 5 bước tại mục 4.4.
- Kết quả: 6 ca, 6 đạt, 0 lỗi

### Kiểm thử end-to-end ứng dụng web

- Tệp: `tests/test_backend.py`
- Phạm vi: Gọi thật các đường dẫn HTTP trên một CSDL tạm: đăng nhập, phân quyền, CSRF, kiểm tra đầu vào, tiền và tồn kho (kể cả chạy đồng thời), thông báo, phân trang, xoá dữ liệu và AI.
- Kết quả: 76 ca, 76 đạt, 0 lỗi

## 2. Nhóm ca kiểm thử ràng buộc cơ sở dữ liệu

| Nhóm | Nội dung kiểm tra |
|---|---|
| Hạng mục phiếu | `service_id` và `part_id` phải đúng một trong hai; số lượng và đơn giá không âm |
| Chốt giá | `unit_price` và tổng hóa đơn không đổi khi sửa giá danh mục |
| Thanh toán | Không thu vượt tổng; một phiếu chỉ có một hóa đơn; một hóa đơn nhiều khoản thu |
| Ràng buộc khác | Biển số và tên đăng nhập trùng bị chặn; vai trò hợp lệ; mật khẩu lưu dạng băm |
| Bảo vệ lịch sử | Không xóa được xe hoặc khách đã phát sinh giao dịch |
| Human Review | Không thể duyệt kết quả AI mà không có người duyệt và thời điểm |
| Dữ liệu mẫu | Đủ số lượng bản ghi theo mục 4.5; có đủ tình huống đặc biệt |
| Chỉ mục | Đã tạo đủ chỉ mục quy định tại mục 4.3 |

## 3. Nhóm ca kiểm thử sao lưu và khôi phục

| Nhóm | Nội dung kiểm tra |
|---|---|
| Tạo bản sao | Sao lưu tạo được tệp khác rỗng và mở được |
| Toàn vẹn bản sao | Bản sao chứa đủ số bảng của CSDL gốc |
| Khôi phục | Dữ liệu trở về đúng trạng thái trước khi sao lưu |
| Kiểm tra sau khôi phục | `integrity_check` đạt và dữ liệu liên kết vẫn nhất quán |
| Ghi chưa commit | Sao lưu giữa lúc đang ghi không làm hỏng tệp, dữ liệu chưa commit không bị lọt |
| Quy trình 4.4 | Năm bước trong mục 4.4 chạy đúng thứ tự |

## 4. Nhóm ca kiểm thử ứng dụng web

| Nhóm | Nội dung kiểm tra |
|---|---|
| Đăng nhập | Chưa đăng nhập bị chuyển về trang đăng nhập; sai mật khẩu, sai tài khoản và cookie giả đều bị từ chối |
| Phân quyền | Bốn vai trò; kỹ thuật viên không quản lý tài khoản, lễ tân không duyệt AI, thu ngân không tiếp nhận phiếu |
| Tìm kiếm lọc sắp xếp | Tìm theo tên, biển số; lọc trạng thái; sắp xếp đúng chiều; truy vấn độc hại không làm hỏng dữ liệu |
| CRUD dùng chung | Thêm, sửa; biểu mẫu thiếu trường và trùng định danh bị chặn; bản ghi đã phát sinh giao dịch không xóa được |
| Phiếu sửa chữa | Thêm hạng mục chốt đúng đơn giá danh mục; thiếu tồn kho bị chặn; chuyển trạng thái đúng luồng; kỹ thuật viên không sửa được phiếu không được phân công |
| Hóa đơn và thanh toán | Tổng do backend tính; không lập trùng hóa đơn; thu một phần rồi thu đủ; không thu vượt và không thu bằng 0 |
| Chức năng AI | Cả ba chức năng tạo được kết quả ở trạng thái PENDING; dịch vụ thiếu mô tả vẫn chạy; AI không tự thêm hạng mục hay lập hóa đơn |
| Human Review | Duyệt/từ chối ghi đủ người duyệt và thời điểm; không duyệt lại được kết quả đã xử lý; người thiếu quyền bị từ chối |
| Mô-đun cửa hàng | Xem và tìm sản phẩm trong phần mở rộng ngoài phạm vi đề tài |

## 5. Cách chạy lại

```bash
python tests/test_schema_constraints.py
python tests/test_backup_restore.py
python tests/test_backend.py
```

## 6. Ghi chú

- Các ca kiểm thử ứng dụng dùng `AI_PROVIDER=mock` nên không cần kết mối
  mạng, không cần khoá API và cho kết quả lặp lại được.
- Ca kiểm thử chạy trên cơ sở dữ liệu tạm nên không làm thay đổi `garage.db`.
- Các ca kiểm thử không phủ môi trường thật có `AI_PROVIDER=openai` và không
  phủ hành vi khi mất mạng; những tình huống đó cần kiểm thử thủ công.

> Kết quả trên chỉ có giá trị tại thời điểm chạy. Trước khi nộp bài cần chạy
> lại toàn bộ để chắc chắn không phát sinh hồi quy.
