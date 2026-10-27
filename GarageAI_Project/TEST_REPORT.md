# BÁO CÁO KIỂM THỬ — GarageTools AI

| | |
|---|---|
| Ngày chạy | 2026-10-26 22:33 |
| Môi trường | Python 3.13.14, SQLite 3.50.4 |
| Tổng số ca | **231** |
| Kết quả | **231 đạt / 0 lỗi** |

---

## 1. Phạm vi

Bộ kiểm thử gồm bốn phần: ràng buộc và dữ liệu mẫu của cơ sở dữ liệu, quy
trình sao lưu/khôi phục, ứng dụng web (trang Jinja2) và tầng API JSON mà
giao diện React gọi. Phần ứng dụng được kiểm
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
- Kết quả: 136 ca, 136 đạt, 0 lỗi

### Kiểm thử tầng API JSON /api/*

- Tệp: `tests/test_api.py`
- Phạm vi: Gọi các endpoint JSON mà giao diện React gọi: phiên và mã CSRF, lỗi theo từng trường, phong bì phân trang, luồng phiếu – báo giá – hoá đơn – thanh toán, kho, bảo hành, AI và phân quyền bốn vai trò.
- Kết quả: 52 ca, 52 đạt, 0 lỗi

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

## 5. Nhóm ca kiểm thử tầng API JSON

| Nhóm | Nội dung kiểm tra |
|---|---|
| Phiên và CSRF | Cookie `garage_csrf` luôn có; thiếu header CSRF bị 403; chưa đăng nhập nhận 401 JSON |
| Lỗi đầu vào | Thiếu trường và trường thừa trả 400 kèm tên trường; tạo tài khoản thiếu mật khẩu bị chặn |
| Phiếu sửa chữa | Tạo – tiếp nhận – thêm hạng mục – chuyển trạng thái đủ luồng; nhảy cóc bị 409; phân công kỹ thuật viên ghi đúng |
| Báo giá | Tạo, thêm dòng, gửi, duyệt, áp dụng; lễ tân không duyệt được (403) |
| Tiền | Lập hoá đơn chỉ khi phiếu hoàn thành; thu vượt bị 409; thu một phần rồi thu đủ; sai trường tiền bị 400 |
| Kho và bảo hành | Nhập kho và điều chỉnh cập nhật tồn + sổ kho; bảo hành chỉ lập cho phiếu hoàn thành, chi tiết có người lập |
| AI | Chay/duyệt/không duyệt lại được; loại sai bị 400; thiếu quyền bị 403 |
| Phân quyền | Thu ngân không xem người dùng/báo cáo, không tạo phiếu; kỹ thuật viên không tạo phiếu/chạy AI |
| Báo cáo và tra cứu | Báo cáo đúng phong bì; tra cứu không lộ mật khẩu; `/api/meta` đủ từ điển hiển thị |

## 6. Cách chạy lại

```bash
python tests/test_schema_constraints.py
python tests/test_backup_restore.py
python tests/test_backend.py
python tests/test_api.py
```

## 7. Kiểm thử vận hành và E2E trên môi trường thật (14/10/2026)

Chạy trên backend thật `uvicorn app.main:app --port 8000` (SQLite `garage.db`,
`APP_ENV=development`, `AUTO_MIGRATE=true` — migration chạy lúc khởi động).

| Bộ kiểm thử | Công cụ | Kết quả |
|---|---|---|
| Smoke HTTP toàn endpoint + phân quyền | `scripts/smoke.ps1` | **31/31** |
| E2E nghiệp vụ: tiếp nhận → báo giá → áp dụng ×2 → sửa chữa → nghiệm thu ×2 → hoá đơn → thu tiền (thu đủ/vượt/huỷ) → bảo hành → sổ cái | `scripts/e2e.ps1` | **32/32** |
| Docker image build | `docker build GarageAI_Project` | **Đạt** (image `garage-tools-ai:ci-check`) |
| Sao lưu / khôi phục runtime | `scripts/backup.ps1` + `scripts/restore.ps1` | **Đạt** (backup 352KB, restore + `integrity_check` OK) |

Nội dung E2E bao phủ: áp dụng báo giá đúng **một lần** (lần 2 → 409) và **trừ
kho đúng 2 phụ tùng** qua sổ cái; nghiệm thu lặp → 409; thu vượt nợ → 409;
huỷ khoản thu cập nhật lại `con_phai_thu`; bảo hành lặp → 409; sau toàn bộ
quy trình `GET /api/stock/audit` **rỗng** (sổ cái khớp tồn kho).

## 8. Ghi chú

- Các ca kiểm thử tự động mặc định dùng `AI_PROVIDER=mock` và giả lập các lỗi của nhà cung cấp AI (`TimeoutException`, HTTP `429`, HTTP `500`, phản hồi JSON sai định dạng trong `TestAiGateway`) nên không cần kết nối mạng, không tốn hạn mức API và cho kết quả lặp lại 100%.
- Ca kiểm thử chạy trên cơ sở dữ liệu tạm nên không làm thay đổi `garage.db`.
- Ngoài bộ kiểm thử tự động, hệ thống đã được kiểm thử thực tế với mô hình ngôn ngữ thật qua Groq (`AI_PROVIDER=groq`, model `openai/gpt-oss-120b`, xem `KT3_PROMPT_EXPERIMENTS.md`).

> Kết quả trên được tự động sinh từ lần chạy thực tế gần nhất (`tests/run_all.py`).
