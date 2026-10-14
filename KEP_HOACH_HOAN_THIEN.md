# GarageTools AI — Kế hoạch hoàn thiện hệ thống (Autopilot)

Ngày lập: 13/10/2026. Branch: `feature/api-thuc-frontend-thuc`.
Phạm vi: rà soát + khắc phục toàn bộ vấn đề nghiệp vụ, dữ liệu, RBAC, UX/UI,
kiểm thử, CI, vận hành. Tài liệu này vừa là kế hoạch, vừa là checklist, vừa là
nhật ký quyết định để tiếp tục khi phiên làm việc bị giới hạn.

## Nguyên tắc bất di bất dịch

- Không mất dữ liệu thật; mọi thay đổi schema qua migration idempotent.
- Không test chạm database vận hành (tests tự dựng DB tạm).
- Không merge PR, không deploy production, không đổi secrets.
- Tiền và kho chỉ đi qua transaction `BEGIN IMMEDIATE`; điều kiện nằm trong
  câu `UPDATE`, không kiểm tra rồi mới ghi.

---

## Giai đoạn 1 — Sửa lỗi dữ liệu nghiêm trọng (backend, P0)

| # | Vấn đề | Vị trí | Sửa | Trạng thái |
|---|--------|--------|-----|-----------|
| P0-1 | Áp dụng báo giá **không idempotent**: chạy 2 lần nhân đôi hạng mục/doanh thu | `services/quotations.py:ap_dung_vao_phieu` | Thêm cột `applied_at`/`applied_by` (migration 005); chặn trong transaction; set trong cùng transaction | ☑ |
| P0-2 | Áp dụng báo giá **không trừ kho** phụ tùng → lệch sổ cái, huỷ phiếu trả kho "ma" | `quotations.py:ap_dung_vao_phieu` | Ghi ledger `USAGE` qua `stock.ghi_giao_dich` cho mọi dòng phụ tùng, cùng transaction | ☑ |
| P0-3 | Thêm hạng mục: dịch vụ **không kiểm tra `is_active`** | `services/orders.py:them_hang_muc` | Bỏ kiểm tra như phụ tùng | ☑ |
| P0-4 | `tao_phieu`: check "xe đang có phiếu mở" **ngoài transaction** (TOCTOU) | `orders.py:tao_phieu` | Chuyển kiểm tra vào trong `transaction()` | ☑ |
| P0-5 | `nghiem_thu`: `UPDATE` **không có guard** (acceptance_at IS NULL, status=COMPLETED) → chập chờn 2 click | `orders.py:nghiem_thu` | UPDATE có điều kiện; rowcount=0 → XungDdot | ☑ |
| P0-6 | Thêm/gỡ dòng báo giá: check trạng thái **ngoài transaction** | `quotations.py:them_hang_muc/go_hang_muc` | Đọc trạng thái + UPDATE trong transaction | ☑ |
| P0-7 | Lỗi chính tả "cáy" trong log huỷ phiếu | `orders.py:_hoan_tra_ton_kho` | Sửa "cái" | ☑ |
| P0-8 | `het_kho=1` lọc `stock > 1` (lệch 1) | `services/catalog.py:danh_sach_phu_tung` | `stock = 0` cho het_kho=1, `stock > 0` cho het_kho=0 | ☑ |
| P0-9 | Migration runner chỉ chống `ALTER parts`; bảng khác có thể fail khi chạy lại | `database/migrations/run_missing.py` | Generalize: bỏ mọi `ALTER TABLE ... ADD COLUMN` đã tồn tại cột | ☑ |
| P0-10 | `xoa_phieu` không kiểm quyền trong service | `orders.py:xoa_phieu` | Thêm kiểm quyền `order.create`; wire API DELETE | ☑ |
| P0-11 | `huy_thanh_toan` không có route (thu ngân ghi nhầm không sửa được) | `billing.py:huy_thanh_toan` | Wire `POST /api/invoices/{id}/payments/{pid}/cancel`, quyền `payment.record` | ☑ |

Test chống tái phát backend: áp dụng báo giá 2 lần (409, không nhân đôi), áp
dụng báo giá có phụ tùng (kho trừ đúng, sổ khớp), huỷ phiếu sau áp dụng (trả
kho đúng 1 lần), dịch vụ ngừng kinh doanh, nghiệm thu 2 lần, het_kho filter,
huy_thanh_toan.

## Giai đoạn 2 — Backend P1 (quyền, HTTP, AI, admin)

| # | Vấn đề | Sửa | Trạng thái |
|---|--------|-----|-----------|
| P1-1 | Thu ngân **không đọc được hoá đơn** nhưng lại ghi được tiền (`GET /api/invoices` = report.view) | Cho phép `report.view` HOẶC `payment.record` trên GET invoices; frontend area finance cũng vậy | ☑ |
| P1-2 | Cập nhật tài khoản **im lặng bỏ qua `password`** | `auth.sua_tai_khoan` nhận mật khẩu mới (hash Argon2id) khi có | ☑ |
| P1-3 | AI "không tìm thấy xe/dịch vụ" trả 502 thay vì 404/400 | `services/ai.py:_chay` phân biệt `KhongTimThay` với `AiError` | ☑ |
| P1-4 | `POST /api/users` self-edit/self-lock trả 400 → nên 403 | Sửa thành `KhongCoQuyen` | ☑ |
| P1-5 | `POST /api/ai/run` chặn event loop tới 15–30s (httpx đồng bộ) | Chuyển endpoint sang `def` (threadpool) + đọc body đồng bộ | ☑ |
| P1-6 | Body JSON sai schema không có handler chuẩn (`RequestValidationError`) | Thêm handler trả `{loi, thong_diep, truong}` 400 | ☑ |
| P1-7 | `POST /api/orders/{id}/status` trạng thái lạ → 409 thay vì 400; message dùng giá trị gốc | Validate Literal trong model; chuẩn hoá message | ☑ |
| P1-8 | `logout` không check gì | Vô hại nhưng cho nhất quán: dùng `deps.nguoi_dung`? → giữ nguyên (logout thất bại khi chưa đăng nhập là OK), ghi lý do | ☑ |
| P1-9 | `intake` double-submit race → 400 thay vì 409 | Bắt `IntegrityError` → `XungDdot` (handler 409 đã có) | ☑ |

## Giai đoạn 3 — Frontend: hoàn thiện hành trình nghiệp vụ

Thứ tự theo依赖: api client → trang mới → trang có sẵn.

| # | Màn hình / sửa lỗi | Chi tiết | Trạng thái |
|---|--------------------|---------|-----------|
| FE-0 | Mở rộng `services/api.ts` + `types` | customers, vehicles, appointments, quotations (list/detail/create/items/send/review/cancel/apply), warranties, accept, catalog services/parts CRUD, users | ☑ |
| FE-1 | Trang **Lịch hẹn** `/appointments` | list + filter trạng thái + tạo/sửa (chọn khách, xe của khách, ngày giờ) | ☑ |
| FE-2 | Trang **Khách hàng & Xe** `/customers` | tab Khách hàng (CRUD) + tab Phương tiện (CRUD, gắn khách) | ☑ |
| FE-3 | Trang **Báo giá** `/quotations` + nhúng vào chi tiết phiếu | tạo nháp → thêm dòng → gửi khách → quản lý duyệt/từ chối → **Áp dụng vào phiếu** (kèm chặn lặp, trừ kho backend); badge trên phiếu | ☑ |
| FE-4 | **Nghiệm thu** trên chi tiết phiếu | nút "Nghiệm thu (khách ký nhận)" gọi `POST /orders/{id}/accept` | ☑ |
| FE-5 | Trang **Bảo hành** `/warranties` | danh sách, lọc, tạo từ hạng mục đủ điều kiện của phiếu COMPLETED, huỷ | ☑ |
| FE-6 | Trang **Danh mục DV/PT** `/catalog` | CRUD dịch vụ + phụ tùng (quản lý) — cần để chọn `ma` khi làm báo giá | ☑ |
| FE-7 | Sửa lỗi bộ lọc Select (`finance`, `users`) | Dùng `value="all"` cho `SelectItem` mặc định (tránh crash Radix Select khi `value=""`) và chuyển thành `undefined` khi gọi API | ☑ |
| FE-8 | **Lệch giờ UTC** | `fmtTime`/`fmtNgay` thiếu `Z` → UTC bị hiển thị như giờ VN. Thêm `Z` | ☑ |
| FE-9 | Thu ngân không vào được `/finance` | area gate: `report.view` ∨ `payment.record` | ☑ |
| FE-10 | Board workflow khoá 100 phiếu im lặng | hiển thị "đang hiển thị 100/n, xem danh sách đầy đủ" | ☑ |
| FE-11 | Trang **Người dùng** `/users` (quản lý) + **Đổi mật khẩu** | CRUD tài khoản, bật/tắt, đổi mật khẩu cá nhân | ☑ |
| FE-12 | Trang **Báo cáo** `/reports` | doanh thu, công nợ, tồn kho, lịch sử (dùng `/api/reports/*`, `/api/history`) | ☑ |
| FE-13 | Lint/typecheck | thêm script `typecheck`; sửa mọi warning eslint; lỗi 404/405 ngôn ngữ Việt | ☑ |
| FE-14 | Test frontend | thêm test route tree đủ 16 routes; test rbac/format; giữ lint + build xanh | ☑ |
| FE-15 | Tài liệu | cập nhật `README_AI_HANDOFF.md` (hết mock, đúng auth cookie+CSRF, đúng endpoint) | ☑ |

## Giai đoạn 4 — Vận hành: CI, backup, migration, Docker, smoke

| # | Việc | Trạng thái |
|---|------|-----------|
| OP-1 | `.github/workflows/ci.yml`: backend `tests/run_all.py` + frontend `lint`/`typecheck`/`test`/`build` | ☑ |
| OP-2 | `scripts/backup.ps1` + `scripts/restore` tham khảo; backup trước migrate đã có sẵn | ☑ |
| OP-3 | Wire `run_missing.py` vào startup (flag `AUTO_MIGRATE`, mặc định bật ở dev; idempotent, không xoá gì) | ☑ |
| OP-4 | `docker-entrypoint.sh`: chạy migration trước khi start | ☑ |
| OP-5 | `scripts/smoke.ps1`: base URL mặc định 8000, tham số hoá; bổ sung case báo giá lặp, nghiệm thu | ☑ |
| OP-6 | `.env.example` đầy đủ biến (AI_*, AUTO_MIGRATE, TZ) | ☑ |
| OP-7 | Kiểm chứng docker build (nếu Docker khả dụng) | ☑ |

## Giai đoạn 5 — Nghiệm thu tổng hợp

| Việc | Trạng thái |
|------|-----------|
| Chạy đủ backend suite (`tests/run_all.py`) — 0 fail (226/226 ngày 14/10) | ☑ |
| Frontend: `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build` — 0 fail | ☑ |
| E2E nghiệp vụ qua HTTP thật (uvicorn + script `scripts/e2e.ps1`): tiếp nhận → báo giá → áp dụng ×2 → sửa chữa → nghiệm thu → hoá đơn → thu tiền → bảo hành — 32/32 | ☑ |
| Kiểm tra sổ cái kho sau E2E: `GET /api/stock/audit` rỗng | ☑ |
| Cập nhật TEST_REPORT.md + báo cáo nghiệm thu cuối | ☑ |

---

## Nhật ký quyết định (ADR)

| ID | Quyết định | Lý do |
|----|-----------|-------|
| ADR-1 | Đánh dấu báo giá đã áp dụng bằng cột `applied_at`/`applied_by` thay vì đổi status sang `APPLIED` | Giữ status `APPROVED` để lịch sử/báo cáo không vỡ; CHECK constraint cũ chỉ cho 5 status; thêm cột nullable là migration an toàn, không đụng dữ liệu cũ |
| ADR-2 | Trừ kho ngay lúc **áp dụng** báo giá (không phải lúc thêm dòng báo giá) | Báo giá chỉ là đề xuất, chưa lấy hàng; kho chỉ trừ khi hàng thực sự rời kho khi áp vào phiếu. Như vậy `them_hang_muc` và `ap_dung` đồng nhất: both write ledger |
| ADR-3 | Huỷ phiếu trả kho đúng **một lần** qua ledger RETURN | Bất biến `stock == SUM(ledger)`; kiểm thử audit rỗng sau luồng áp dụng + huỷ |
| ADR-4 | GET /api/invoices mở cho `payment.record` (thu ngân) | Thu ngân cần xem hoá đơn để thu tiền; hiện tại 403 vô lý. Vẫn chặn kỹ thuật viên |
| ADR-5 | Chỉ `POST /api/ai/run` chuyển `def` (threadpool); các route JSON khác giữ `async def` | AI gọi httpx đồng bộ 15–30s có thể chặn event loop; SQLite thao tác ms-scale. Đổi toàn bộ 27 route sang body-không-dọn-dõi là rủi ro không cần thiết |
| ADR-6 | Không nhúng frontend SSR vào Docker image backend | TanStack Start chạy Nitro server riêng; tích hợp nhiều tầng không cần cho nghiệm thu. Ghi rõ trong README: backend compose + vite dev proxy |
| ADR-7 | `AUTO_MIGRATE` mặc định bật, chỉ chạy migration thiếu, có backup `garage.db.bak-pre-migrate` | migration idempotent; tự động chạy khi start an toàn và loại bỏ bước thủ công dễ quên |
| ADR-8 | Board workflow hiển thị tối đa 100 + cảnh báo tổng | API giới hạn `moi_trang ≤ 100`; thêm điều hướng sang trang danh sách phân trang đầy đủ thay vì load toàn bộ |
| ADR-9 | Ngữ cảnh "khách mới/xe mới" đặt ở màn Tiếp nhận (`/inspection`) và Lịch hẹn: tạo khách → tạo xe → tạo phiếu theo thứ tự, form liên động | Backend không có endpoint gộp; 3 bước tạo liên tiếp là chuẩn REST, giữ nguyên API |

Tiếp tục phiên sau: mở file này, xem cột Trạng thái — mục nào còn ☐ là việc
còn phải làm.
