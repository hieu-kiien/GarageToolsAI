# GarageTools AI — Giao diện Web (Frontend)

Giao diện người dùng chính thức của hệ thống **GarageTools AI** (Nhóm 23 — Học phần _Ứng dụng Trí tuệ Nhân tạo AIA331_), xây dựng bằng **React 19**, **TanStack Start / Router / Query**, **Tailwind CSS v4** và **shadcn/ui (Radix UI)**.

Toàn bộ dữ liệu được kết nối trực tiếp với Backend FastAPI qua tầng JSON API `/api/*` (không sử dụng dữ liệu giả lập).

---

## 1. Công nghệ sử dụng

- **Framework & Routing:** React 19, TanStack Start, TanStack Router (file-based routing, 16 routes)
- **Quản lý trạng thái & dữ liệu server:** TanStack React Query v5 (`src/services/api.ts`)
- **Giao diện & Biểu đồ:** Tailwind CSS v4, Radix UI / shadcn/ui, Lucide Icons, Recharts, Sonner (toast)
- **Bảo mật & Phân quyền:** Cookie phiên `garage_session` (HttpOnly) + header `X-CSRF-Token` tự động từ `garage_csrf`, phân quyền giao diện theo ma trận quyền backend (`src/lib/rbac.tsx`)
- **Kiểm thử & Chất lượng mã:** TypeScript 5.8, ESLint 9, Prettier, Vitest + Testing Library

---

## 2. Danh sách 16 màn hình nghiệp vụ (`src/routes/`)

| Đường dẫn            | Màn hình                                                                                       | Quyền truy cập (`AREA_QUYEN`)                          |
| -------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `/`                  | Tổng quan xưởng (KPI, doanh thu, cảnh báo kho, kết quả AI gần đây)                             | `dashboard.view`                                       |
| `/workflow`          | Bảng điều phối Kanban theo trạng thái phiếu sửa chữa                                           | `order.view`                                           |
| `/repair-orders`     | Danh sách phiếu sửa chữa (tìm kiếm, lọc trạng thái, phân trang)                                | `order.view`                                           |
| `/repair-orders/$id` | Chi tiết phiếu sửa chữa (biên bản tiếp nhận, hạng mục, báo giá, nghiệm thu, hoá đơn, nhật ký)  | `order.view`                                           |
| `/inspection`        | Tiếp nhận xe (tạo liên hoàn khách mới → xe mới → phiếu → biên bản tiếp nhận)                   | `order.create`                                         |
| `/appointments`      | Quản lý lịch hẹn (tạo/sửa/xoá, lọc trạng thái)                                                 | `appointment.view`                                     |
| `/customers`         | Quản lý Khách hàng & Phương tiện (2 tab CRUD đầy đủ, biển số/VIN/km/màu)                       | `customer.view` ∨ `vehicle.view`                       |
| `/quotations`        | Danh sách báo giá chính thức                                                                   | `quote.manage`                                         |
| `/quotations/$id`    | Chi tiết báo giá (thêm/gỡ dòng, gửi khách, duyệt/từ chối, áp dụng vào phiếu trừ kho)           | `quote.manage`                                         |
| `/ai-review`         | Trợ lý AI (AI01 Lịch sử, AI02 Giải thích DV, AI03 Báo giá nháp) & Duyệt kết quả (Human Review) | `ai.history` ∨ `ai.explain` ∨ `ai.quote` ∨ `ai.review` |
| `/inventory`         | Kho phụ tùng (sổ cái nhập/xuất/điều chỉnh, cảnh báo chạm ngưỡng tối thiểu)                     | `stock.manage` ∨ `order.view`                          |
| `/catalog`           | Danh mục Dịch vụ & Phụ tùng (CRUD dành cho Quản lý)                                            | `catalog.view`                                         |
| `/warranties`        | Quản lý bảo hành theo hạng mục phiếu đã hoàn thành                                             | `warranty.manage`                                      |
| `/finance`           | Hoá đơn & Thanh toán (thu một phần/thu đủ, huỷ khoản thu nhầm)                                 | `report.view` ∨ `payment.record`                       |
| `/reports`           | Báo cáo thống kê (doanh thu, dịch vụ, phụ tùng, khách hàng, trạng thái) & Tra cứu lịch sử      | `report.view` ∨ `history.view`                         |
| `/users`             | Quản lý tài khoản nhân viên, phân quyền vai trò, khoá/mở khoá & đổi mật khẩu                   | `user.manage`                                          |

---

## 3. Hướng dẫn cài đặt và chạy

### Bước 1: Khởi chạy Backend FastAPI trước (cổng `8000`)

```bash
cd ../GarageAI_Project
python -m uvicorn app.main:app --reload --port 8000
```

### Bước 2: Cài đặt và chạy Frontend

```bash
cd ../frontend
npm install
npm run dev
```

Vite dev server đã cấu hình sẵn proxy `/api` trỏ về `http://127.0.0.1:8000` (trong `vite.config.ts`), đảm bảo cùng nguồn (same-origin) cho cookie phiên và CSRF.

---

## 4. Các lệnh kiểm tra chất lượng

```bash
npm run lint        # Kiểm tra ESLint (0 lỗi, 0 cảnh báo)
npm run typecheck   # Kiểm tra kiểu TypeScript (tsc --noEmit)
npm run test        # Chạy bộ kiểm thử Vitest (routing + RBAC + định dạng tiền/giờ UTC→VN)
npm run build       # Build bản production
```
