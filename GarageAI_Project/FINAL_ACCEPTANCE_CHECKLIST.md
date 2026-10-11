# PHIẾU KIỂM TRA HOÀN THÀNH — GarageTools AI

Phiếu tự kiểm tra trước khi nộp. Mỗi mục phải **ĐẠT** mới được ký.

Ngày kiểm tra: *(điền)* — Người kiểm tra: *(điền)*

---

## A. Mã nguồn

| # | Hạng mục | Cách kiểm | Kết quả |
|---|---|---|---|
| A1 | Mọi tệp Python biên dịch được | `python -m compileall app database tests` | [x] |
| A2 | Ứng dụng nạp được | `from app.main import create_app` | [x] |
| A3 | Không còn biến chết, import thừa hay đoạn mã rác | Rà soát thủ công `app/` | [x] |
| A4 | Không ghi thẳng `SECRET_KEY` hay khoá API trong mã | Đọc `app/core/config.py` | [x] |
| A5 | Mọi giá trị truy vấn đều qua tham số | Rà soát `app/crud.py`, `app/services/` | [x] |
| A6 | Tên bảng/tên cột sắp xếp qua danh sách cho phép | `crud._kiem_tra_bang`, whitelist `SAP_XEP_CHO_PHEP` | [x] |

## B. Cơ sở dữ liệu

| # | Hạng mục | Cách kiểm | Kết quả |
|---|---|---|---|
| B1 | Dựng lại CSDL từ đầu không lỗi | `python database/init_db.py` | [x] |
| B2 | Đủ 16 bảng theo mục 4.2 | `python tests/test_schema_constraints.py` | [x] |
| B3 | Đạt số lượng dữ liệu mẫu tối thiểu ở mục 4.5 | `test_so_luong_theo_muc_4_5` | [x] |
| B4 | `PRAGMA foreign_keys = ON` mọi lần kết nối | `app/core/db.py` | [x] |
| B5 | `integrity_check` đạt | `test_kiem_tra_toan_ven` | [x] |
| B6 | Mỗi hạng mục đúng một trong `service_id` / `part_id` | Nhóm ràng buộc | [x] |
| B7 | Đổi giá danh mục không làm đổi hạng mục đã chốt | `test_thay_doi_gia_danh_muc_khong_lam_doi_lich_su` | [x] |
| B8 | Không thu vượt tổng hóa đơn | Nhóm thanh toán | [x] |
| B9 | Xoá khách/xe đã có giao dịch bị chặn | Nhóm bảo vệ lịch sử | [x] |

## C. Ứng dụng web

| # | Hạng mục | Cách kiểm | Kết quả |
|---|---|---|---|
| C1 | Không lỗi 500 ở bất kỳ màn hình nào, kể cả dữ liệu sai | `test_danh_sach_ca_khong_tra_ve_loi_500` | [x] |
| C2 | Chưa đăng nhập bị chuyển về trang đăng nhập | Nhóm đăng nhập | [x] |
| C3 | Sai mật khẩu không lộ thông tin tài khoản | Nhóm đăng nhập | [x] |
| C4 | Bốn vai trò đúng ma trận quyền | `test_ma_tran_dung_theo_vai_tro` | [x] |
| C5 | CSS tải được, trang không hiển thị chữ không định dạng | `GET /static/style.css` = 200 | [x] |
| C6 | Tìm kiếm, lọc, sắp xếp đúng | Nhóm tìm kiếm lọc sắp xếp | [x] |
| C7 | Truy vấn độc hại không làm hỏng dữ liệu | Nhóm SQL injection | [x] |
| C8 | Trạng thái phiếu chuyển đúng luồng nghiệp vụ | Nhóm nghiệp vụ phiếu | [x] |
| C9 | Hóa đơn và thanh toán đúng số liệu, không thu vượt | Nhóm tiền (kể cả chạy đồng thời) | [x] |
| C10 | Có `/healthz` và `/readyz` không cần đăng nhập | `test_he_thong_bao_suc_khoe` | [x] |
| C11 | Thiếu hoặc sai mã CSRF bị từ chối (403) | `test_csrf_sai_bi_tu_choi` | [x] |
| C12 | Nguồn gửi đi khác gốc bị từ chối | `kiem_tra_origin` trong `app/core/security.py` | [x] |
| C13 | Giới hạn tân suất đăng nhập sai theo tài khoản | `test_gioi_han_so_lan_dang_nhap` | [x] |
| C14 | Thông báo thành công/lỗi hiển thị một lần rồi hết | Nhóm thông báo | [x] |
| C15 | Danh sách có phân trang, số trang vượt biên bị ép lại | Nhóm phân trang | [x] |
| C16 | Mọi thao tác ghi là POST; không còn đường GET xoá dữ liệu | `test_xo_bang_get_bi_tu_choi` | [x] |
| C17 | Mật khẩu lưu dạng băm (Argon2id, fallback PBKDF2) | Nhóm đăng nhập | [x] |
| C18 | Đổi mật khẩu làm mất hiệu phiên đang đăng nhập | `auth_version` trong `app/core/db.py` | [x] |
| C19 | Security headers (nosniff, frame deny, referrer, cache) | Middleware `ve_bia_an` | [x] |
| C20 | Tài liệu OpenAPI bị tắt, không lộ cấu trúc | `test_khong_co_route_bao_danh_thu` | [x] |

## D. AI và Human Review

| # | Hạng mục | Cách kiểm | Kết quả |
|---|---|---|---|
| D1 | Cả ba chức năng chạy được với `AI_PROVIDER=mock` | Nhóm chức năng AI | [x] |
| D2 | Dữ liệu thiếu vẫn ra kết quả, không lỗi 500 | `test_ai02_dich_vu_thieu_mo_ta_van_tao_duoc_ket_qua` | [x] |
| D3 | Phiếu rỗng không bị AI bịa thêm hạng mục | `test_ai03_bao_gia_khong_tao_hang_muc_that` | [x] |
| D4 | Kết quả mới luôn `PENDING` | `test_human_review_duyet` | [x] |
| D5 | Duyệt ghi đủ người duyệt và thời điểm | `test_human_review_duyet` | [x] |
| D6 | Không duyệt lại được kết quả đã xử lý | `test_khong_duoc_duyet_lai_ket_qua_da_xu_ly` | [x] |
| D7 | Người thiếu quyền bị chặn | `test_khong_duoc_duyet_khi_khong_co_quyen` | [x] |
| D8 | Mô tả ranh giới "AI không tự quyết tiền" hiện rõ trên giao diện | Xem màn hình `/ai` | [x] |
| D9 | Có ca kiểm thử cho timeout, phản hồi rỗng, phản hồi sai định dạng | `app/ai_gateway.py` | [ ] |

> **D9 chưa đạt.** Xem ghi chú phạm vi ở cuối phiếu.

## E. Tài liệu và minh chứng

| # | Hạng mục | Kết quả |
|---|---|---|
| E1 | `README.md` mô tả đúng trạng thái thật | [x] |
| E2 | `TEST_REPORT.md` sinh từ kết quả chạy thật | [x] |
| E3 | Ảnh chụp màn hình lấy từ ứng dụng đang chạy | [x] |
| E4 | `KT3_PROMPT_EXPERIMENTS.md` mô tả đúng cách thử | [x] |
| E5 | `USER_ACCEPTANCE_TEST.md` không đánh dấu ca chưa chạy | [x] |
| E6 | Báo cáo đã cập nhật theo trạng thái thật | [ ] |
| E7 | Ma trận 40 tiêu chí còn khớp | [ ] |

## F. Triển khai

| # | Hạng mục | Kết quả |
|---|---|---|
| F1 | Có `Dockerfile` và `docker-compose.yml` | [x] |
| F2 | `docker compose up` tạo được ứng dụng chạy được | [ ] |
| F3 | Có kiểm tra sức khoẻ container | [x] |

> **F2 chưa kiểm** vì máy dựng bài chưa cài Docker. Cần chạy
> `docker compose up --build` ít nhất một lần trước khi nộp.

---

## Kết luận

Số mục đạt: *(điền)* / *(tổng)*

**Các mục chưa đạt cần xử lý trước khi nộp:** D9, E6, E7, F2.

### Ghi chú phạm vi

- D9: `app/ai_gateway.py` đã có đường xử lý timeout, phản hồi rỗng và phản hồi
  sai định dạng nhưng **chưa** có ca kiểm thử tự động. Chỉ có thể kiểm thử được khi
  dùng `AI_PROVIDER=openai` với khoá thật.
- Toàn bộ ca kiểm thử AI chạy ở chế độ `mock`, nên chứng minh logic và quy tắc
  duyệt, không đo chất lượng sinh văn bản của mô hình ngôn ngữ.
- Các mục đánh dấu `[ ]` trong `USER_ACCEPTANCE_TEST.md` cần người dùng thực tế
  thực hiện.