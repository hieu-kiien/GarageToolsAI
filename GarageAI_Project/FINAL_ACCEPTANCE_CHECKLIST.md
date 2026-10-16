# PHIẾU KIỂM TRA HOÀN THÀNH — GarageTools AI

Phiếu tự kiểm tra trước khi nộp. Mỗi mục phải **ĐẠT** mới được ký.

Ngày kiểm tra: **16/10/2026** — Người kiểm tra: **Nhóm 23 (AIA331 - Mã số 80277)**

---

## A. Mã nguồn

| # | Hạng mục | Cách kiểm | Kết quả |
|---|---|---|---|
| A1 | Mọi tệp Python biên dịch được | `python -m compileall app database tests` | [x] |
| A2 | Ứng dụng nạp được | `from app.main import create_app` | [x] |
| A3 | Không còn biến chết, import thừa hay đoạn mã rác | Rà soát thủ công `app/` & `frontend/src/` (`npm run lint` + `typecheck`) | [x] |
| A4 | Không ghi thẳng `SECRET_KEY` hay khoá API trong mã | Đọc `app/core/config.py` | [x] |
| A5 | Mọi giá trị truy vấn đều qua tham số | Rà soát `app/crud.py`, `app/services/` | [x] |
| A6 | Tên bảng/tên cột sắp xếp qua danh sách cho phép | `crud._kiem_tra_bang`, whitelist `SAP_XEP_CHO_PHEP` | [x] |

## B. Cơ sở dữ liệu

| # | Hạng mục | Cách kiểm | Kết quả |
|---|---|---|---|
| B1 | Dựng lại CSDL từ đầu không lỗi | `python database/init_db.py` + `database/migrations/run_missing.py` | [x] |
| B2 | Đủ 21 bảng (17 bảng nghiệp vụ lõi + 4 bảng mở rộng, 37 chỉ mục) theo mục 4.2 | `python tests/test_schema_constraints.py` (37/37 đạt) | [x] |
| B3 | Đạt số lượng dữ liệu mẫu tối thiểu ở mục 4.5 | `test_so_luong_theo_muc_4_5` | [x] |
| B4 | `PRAGMA foreign_keys = ON` mọi lần kết nối | `app/core/db.py` | [x] |
| B5 | `integrity_check` đạt | `test_kiem_tra_toan_ven` + `GET /readyz` | [x] |
| B6 | Mỗi hạng mục đúng một trong `service_id` / `part_id` | Nhóm ràng buộc XOR trên `repair_order_items`, `quotation_items`, `warranties` | [x] |
| B7 | Đổi giá danh mục không làm đổi hạng mục đã chốt | `test_thay_doi_gia_danh_muc_khong_lam_doi_lich_su` | [x] |
| B8 | Không thu vượt tổng hóa đơn | Nhóm thanh toán (`BEGIN IMMEDIATE`) | [x] |
| B9 | Xoá khách/xe/danh mục đã có giao dịch bị chặn | Nhóm bảo vệ lịch sử (`ban_ghi_da_bi_tham_chieu`) | [x] |

## C. Ứng dụng web & API JSON

| # | Hạng mục | Cách kiểm | Kết quả |
|---|---|---|---|
| C1 | Không lỗi 500 ở bất kỳ màn hình nào, kể cả dữ liệu sai | `test_backend.py` (133/133) + `test_api.py` (50/50) | [x] |
| C2 | Chưa đăng nhập bị chuyển về trang đăng nhập (HTML 303 / API 401) | Nhóm đăng nhập | [x] |
| C3 | Sai mật khẩu không lộ thông tin tài khoản | Nhóm đăng nhập | [x] |
| C4 | Bốn vai trò đúng ma trận quyền | `test_ma_tran_dung_theo_vai_tro` + `AREA_QUYEN` trên React FE | [x] |
| C5 | Giao diện tải đầy đủ, không vỡ định dạng | `GET /static/style.css` = 200 + `frontend` build thành công | [x] |
| C6 | Tìm kiếm, lọc, sắp xếp đúng | Nhóm tìm kiếm lọc sắp xếp | [x] |
| C7 | Truy vấn độc hại không làm hỏng dữ liệu | Nhóm SQL injection & XSS escape | [x] |
| C8 | Trạng thái phiếu chuyển đúng luồng nghiệp vụ | Nhóm nghiệp vụ phiếu + nghiệm thu + báo giá idempotent | [x] |
| C9 | Hóa đơn và thanh toán đúng số liệu, không thu vượt | Nhóm tiền (kể cả chạy đồng thời `BEGIN IMMEDIATE`) | [x] |
| C10 | Có `/healthz` và `/readyz` không cần đăng nhập | `test_health_va_readiness` | [x] |
| C11 | Thiếu hoặc sai mã CSRF bị từ chối (403) | `test_csrf_sai_bi_tu_choi` + `scripts/smoke.ps1` | [x] |
| C12 | Nguồn gửi đi khác gốc bị từ chối | `kiem_tra_origin` trong `app/core/security.py` | [x] |
| C13 | Giới hạn tần suất đăng nhập sai theo tài khoản | `test_gioi_han_so_lan_dang_nhap` | [x] |
| C14 | Thông báo thành công/lỗi hiển thị một lần rồi hết | Nhóm thông báo (`flash.py` + toast `sonner`) | [x] |
| C15 | Danh sách có phân trang, số trang vượt biên bị ép lại | Nhóm phân trang | [x] |
| C16 | Mọi thao tác ghi là POST/PUT/DELETE kèm CSRF; không xoá bằng GET | `test_xo_bang_get_bi_tu_choi` | [x] |
| C17 | Mật khẩu lưu dạng băm (Argon2id, fallback PBKDF2) | Nhóm đăng nhập | [x] |
| C18 | Đổi mật khẩu làm mất hiệu lực phiên đang đăng nhập | `auth_version` trong `users` | [x] |
| C19 | Security headers (nosniff, frame deny, referrer, cache) | Middleware `ve_bia_an` trong `app/main.py` | [x] |
| C20 | Tài liệu OpenAPI bị tắt, không lộ cấu trúc | `test_khong_co_route_bao_danh_thu` | [x] |

## D. AI và Human Review

| # | Hạng mục | Cách kiểm | Kết quả |
|---|---|---|---|
| D1 | Cả ba chức năng chạy được với `AI_PROVIDER=mock` và provider thật (`groq`) | Nhóm chức năng AI + E2E UI với `openai/gpt-oss-120b` | [x] |
| D2 | Dữ liệu thiếu vẫn ra kết quả, không lỗi 500 | `test_ai02_dich_vu_thieu_mo_ta_van_tao_duoc_ket_qua` | [x] |
| D3 | Phiếu rỗng không bị AI bịa thêm hạng mục | `test_ai_khong_tao_hang_muc_hoac_hoa_don` | [x] |
| D4 | Kết quả mới luôn `PENDING` | `test_duyet_va_khong_duoc_duet_lai` | [x] |
| D5 | Duyệt ghi đủ người duyệt và thời điểm | `test_duyet_va_khong_duoc_duet_lai` | [x] |
| D6 | Không duyệt lại được kết quả đã xử lý | `test_duyet_va_khong_duoc_duet_lai` | [x] |
| D7 | Người thiếu quyền bị chặn | `test_khong_duoc_duet_khi_thieu_quyen` | [x] |
| D8 | Mô tả ranh giới "AI không tự quyết tiền" hiện rõ trên giao diện | Xem màn hình `/ai` (Jinja2) và `/ai-review` (React) | [x] |
| D9 | Có ca kiểm thử cho timeout, lỗi 429/500, phản hồi rỗng, phản hồi sai định dạng | `TestAiGateway` trong `tests/test_backend.py` (15 ca kiểm thử) | [x] |

## E. Tài liệu và minh chứng

| # | Hạng mục | Kết quả |
|---|---|---|
| E1 | `README.md` và `frontend/README.md` mô tả đúng trạng thái thật | [x] |
| E2 | `TEST_REPORT.md` sinh từ kết quả chạy thật (**226/226 đạt**) | [x] |
| E3 | Ảnh chụp màn hình lấy từ ứng dụng đang chạy (`screenshots/` & `docs/screenshots/`) | [x] |
| E4 | `KT3_PROMPT_EXPERIMENTS.md` mô tả đầy đủ thử nghiệm mock và mô hình thật | [x] |
| E5 | `USER_ACCEPTANCE_TEST.md` hoàn thành đủ **35/35 ca** | [x] |
| E6 | Báo cáo và tài liệu tiến độ (`KEP_HOACH_HOAN_THIEN.md`, `IMPLEMENTATION_PROGRESS.md`) đã đồng bộ | [x] |
| E7 | Ma trận 40 tiêu chí môn học (KT1, KT2, KT3, Cuối kỳ) khớp đầy đủ | [x] |

## F. Triển khai

| # | Hạng mục | Kết quả |
|---|---|---|
| F1 | Có `Dockerfile`, `docker-entrypoint.sh` và `docker-compose.yml` | [x] |
| F2 | `docker compose up --build` tạo được container chạy ổn định (cổng `8010:8000`, `healthy`) | [x] |
| F3 | Có kiểm tra sức khoẻ container (`healthcheck` gọi `/healthz`) và CI (`.github/workflows/ci.yml`) | [x] |

---

## Kết luận

Số mục đạt: **54 / 54 (100%)**

**Trạng thái:** Hệ thống đã hoàn thành toàn bộ các tiêu chí kỹ thuật, nghiệp vụ, kiểm thử tự động (**226/226**), kiểm thử vận hành Smoke (**31/31**), E2E (**32/32**) và UAT (**35/35**). Sẵn sàng nộp bài và bảo vệ đồ án.