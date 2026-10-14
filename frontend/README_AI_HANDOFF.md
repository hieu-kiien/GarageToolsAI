# GarageTools AI — Frontend ↔ Backend Handoff

## Hiện trạng

Frontend **không còn mock**: toàn bộ dữ liệu lấy thật từ FastAPI qua `src/services/api.ts`
(`goi()` = `fetch` + ném `ApiError`). Types mirror backend tại `src/types/index.ts`
(khớp JSON của `GarageAI_Project/app/services/*.py` — backend là nguồn duy nhất).

## Auth & CSRF

- Đăng nhập `POST /api/auth/login` → backend đặt cookie phiên **`garage_session`**
  (httOnly). Không dùng bearer token.
- Mọi POST/PUT/DELETE kèm header **`X-CSRF-Token`** đọc từ cookie **`garage_csrf`**
  (backend cấp kèm trang). Client gửi `credentials: "same-origin"` — cùng origin
  qua Vite proxy `/api → http://127.0.0.1:8000` (không cần CORS).
- Response 401 phát event `SU_KIEN_HET_PHIEN` → quay về màn đăng nhập.
- `POST /api/auth/password { mat_khau_cu, mat_khau_moi }` đổi mật khẩu cá nhân;
  backend tăng phiên bản → mọi phiên đang mở bị đăng xuất.

## Quy ước

- JSON, tiền = số nguyên VND, ngày giờ backend = `YYYY-MM-DD HH:MM:SS` **UTC**
  (giao diện gắn `Z` trước khi hiển thị — xem `fmtTime`/`fmtNgay` trong `lib/rbac.tsx`).
- Phân trang: `{ dong, tong, trang, tong_trang }` với query `?trang=&moi_trang=&q=`.
- Lỗi backend: `{ loi, thong_diep, truong? }` → `ApiError(status, loi, thong_diep)`.
  Validate body lỗi 400 `dau_vao_khong_hop_le` kèm bản đồ `truong`.

## Phân quyền

Vai trò: `MANAGER` (Quản lý), `RECEPTIONIST` (Lễ tân), `TECHNICIAN` (Kỹ thuật viên),
`CASHIER` (Thu ngân). Ma trận duy nhất: `security_matrix.py`; giao diện ánh xạ
màn hình → quyền qua `AREA_QUYEN` (`lib/rbac.tsx`), server vẫn kiểm lại từng route.

## Endpoint chính (prefix `/api`)

| Nhóm | Method & path | Quyền |
|---|---|---|
| Phiếu | `GET/POST /orders`, `GET/DELETE /orders/{id}`, `POST /orders/{id}/status`, `POST /orders/{id}/assign` | `order.view`, `order.create` (tạo/xoá), `order.progress`, `order.assign` |
| Tiếp nhận | `POST /orders/{id}/intake`, `POST /orders/{id}/accept` (nghiệm thu) | `order.create` ∨ `order.progress`, `order.accept` |
| Hạng mục | `POST /orders/{id}/items`, `POST /orders/{id}/items/{iid}/remove`, `POST /orders/{id}/logs` | `order.item`, `order.progress` |
| Báo giá | `GET/POST /quotations`, `GET /quotations/{id}`, `POST …/items`, `…/items/{iid}/remove`, `…/send`, `…/review`, `…/cancel`, `…/apply` | `quote.manage` (duyệt: `quote.approve`) |
| Hoá đơn | `GET /invoices`, `GET /invoices/{id}`, `POST …/payments`, `POST …/payments/{khoan_id}/cancel` | `report.view` ∨ `payment.record` (xem), `payment.record` (ghi/huỷ) |
| Khách/Xe/Lịch | `GET/POST/PUT/DELETE /customers`, `/vehicles`, `/appointments` | `customer.view`/`vehicle.view`/`appointment.view`, sửa: `*.edit` |
| Kho | `GET /stock`, `/stock/warnings`, `POST /stock/receipt`, `/stock/adjust` | `stock.manage` ∨ `order.view` (xem), `stock.manage` (ghi) |
| Danh mục | `GET/POST/PUT/DELETE /services`, `/parts` | `catalog.view`, ghi: `catalog.edit` |
| Bảo hành | `GET /warranties`, `GET /orders/{id}/warranty-eligible`, `POST /warranties`, `POST /warranties/{id}/cancel` | `warranty.manage` |
| AI | `POST /ai/run { kind, … }`, `GET /ai/results`, `/ai/recent`, `POST /ai/results/{id}/review` | `ai.*`, duyệt: `ai.review` |
| Tài khoản | `GET/POST /users`, `POST /users/{id}/toggle` | `user.manage` / `user.edit` |
| Báo cáo | `GET /reports/{kind}` (kind: `doanh-thu`, `dich-vu`, `phu-tung`, `khach-hang`, `trang-thai`), `GET /history`, `GET /lookups`, `GET /meta` | `report.view` / `history.view` |
| Phiên | `GET /auth/session`, `POST /auth/login`, `POST /auth/logout`, `POST /auth/password` | — |

## Quy tắc nghiệp vụ (backend đã enforce, UI chỉ hiển thị)

- AI không tự duyệt báo giá, không tính tổng quyết định — tổng do backend tính.
- `APPROVED → áp dụng` (`POST /quotations/{id}/apply`) trừ kho theo ledger `USAGE`,
  idempotent (áp lần 2 → 409); báo giá chỉ áp 1 lần (`applied_at`).
- Nghiệm thu chỉ từ `COMPLETED`, `POST /orders/{id}/accept` 409 nếu chạy 2 lần.
- Chuyển trạng thái theo bảng `meta.chuyen_trang_thai`; trạng thái terminal
  (`COMPLETED`, `CANCELLED`) không nhận chuyển tiếp.
- Huỷ khoản thu xoá bản ghi trong `payments` và tính lại trạng thái hoá đơn; huỷ bảo hành 1 lần.
- Đơn vị tiền VND nguyên; tổng tiền hoá đơn bằng tổng các hạng mục phiếu.
