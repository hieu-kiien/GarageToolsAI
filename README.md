# GarageTools AI — Hệ thống Quản lý Garage Sửa chữa Ô tô có tích hợp AI

**Học phần:** Ứng dụng Trí tuệ Nhân tạo (AIA331) — **Mã số:** 80277 — **Nhóm 23**  
**Trường Đại học Công nghệ Thông tin và Truyền thông — Đại học Thái Nguyên**

---

## 1. Giới thiệu tổng quan

**GarageTools AI** là hệ thống quản lý quy trình sửa chữa ô tô toàn diện từ khâu đặt lịch, tiếp nhận xe, lập báo giá, điều phối sửa chữa, quản lý sổ cái tồn kho phụ tùng, nghiệm thu, lập hóa đơn/thanh toán, cấp bảo hành cho tới thống kê báo cáo — đồng thời tích hợp **Trợ lý AI (3 chức năng AI01, AI02, AI03)** có kiểm soát qua cơ chế **Human Review**.

| Thành phần | Thư mục | Công nghệ & Quy mô |
|---|---|---|
| **Backend & CSDL** | [`GarageAI_Project/`](./GarageAI_Project/README.md) | Python FastAPI, SQLite (21 bảng: 17 bảng nghiệp vụ lõi + 4 bảng mở rộng, 37 chỉ mục, WAL, `BEGIN IMMEDIATE`), Argon2id, CSRF, RBAC 4 vai trò, AI Gateway đa provider (`mock`, `groq`, `openrouter`, `gemini`, `openai`, `9router`, `custom`) |
| **Frontend chính thức** | [`frontend/`](./frontend/README.md) | React 19, TanStack Start / Router / Query, Tailwind CSS v4, Radix UI (shadcn/ui) — 16 màn hình nghiệp vụ kết nối trực tiếp `/api/*` |
| **Kịch bản vận hành & E2E** | [`scripts/`](./scripts/) | `smoke.ps1` (**31/31 PASS**), `e2e.ps1` (**32/32 PASS**), `backup.ps1` & `restore.ps1` |
| **CI/CD & Đóng gói** | [`.github/workflows/ci.yml`](./.github/workflows/ci.yml) | GitHub Actions CI tự động chạy 226 ca kiểm thử Backend + `lint`/`typecheck`/`test`/`build` Frontend; Docker & Docker Compose (`8010:8000`) |

---

## 2. Khởi chạy nhanh (Quick Start)

### Bước 1: Khởi chạy Backend FastAPI (cổng `8000`)

```powershell
cd GarageAI_Project
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Khởi tạo CSDL mẫu lần đầu (nếu chưa có garage.db)
python database/init_db.py

# Chạy máy chủ FastAPI (tự động áp migrations 001 -> 005)
python -m uvicorn app.main:app --reload --port 8000
```

### Bước 2: Khởi chạy Giao diện React (Frontend)

Mở một cửa sổ terminal thứ hai:

```powershell
cd frontend
npm install
npm run dev
```

Vite dev server tự động chuyển tiếp (proxy) mọi yêu cầu `/api/*` sang `http://127.0.0.1:8000`.

### Tài khoản dùng thử (Demo)

| Vai trò | Tên đăng nhập | Mật khẩu |
|---|---|---|
| **Quản lý (`MANAGER`)** | `quan_ly` | `Garage@2026` |
| **Lễ tân (`RECEPTIONIST`)** | `le_tan` | `Garage@2026` |
| **Kỹ thuật viên (`TECHNICIAN`)** | `ky_thuat_vien` | `Garage@2026` |
| **Thu ngân (`CASHIER`)** | `thu_ngan` | `Garage@2026` |

---

## 3. Bộ kiểm thử & Nghiệm thu

Hệ thống đã vượt qua toàn bộ các cấp độ kiểm thử:

1. **Kiểm thử tự động Backend (`226/226 đạt`):**
   ```powershell
   cd GarageAI_Project
   python -X utf8 tests/run_all.py
   ```
   - `tests/test_schema_constraints.py`: **37/37** ca ràng buộc CSDL & dữ liệu mẫu
   - `tests/test_backup_restore.py`: **6/6** ca sao lưu & khôi phục
   - `tests/test_backend.py`: **133/133** ca ứng dụng web & `TestAiGateway` (timeout, 429, 500, JSON sai định dạng)
   - `tests/test_api.py`: **50/50** ca tầng API JSON `/api/*`

2. **Kiểm thử Frontend (`lint` + `typecheck` + `test` + `build`):**
   ```powershell
   cd frontend
   npm run lint
   npm run typecheck
   npm run test
   npm run build
   ```

3. **Kiểm thử vận hành thực tế (Smoke & E2E):**
   ```powershell
   .\scripts\smoke.ps1   # 31/31 PASS
   .\scripts\e2e.ps1     # 32/32 PASS (sổ cái kho khớp tuyệt đối sau toàn bộ quy trình)
   ```

---

## 4. Danh mục tài liệu trong kho mã nguồn

- [`Báo cáo.pdf`](./Báo%20cáo.pdf) — Báo cáo kỹ thuật hoàn thiện biên dịch bằng **XeLaTeX** (`ictu_v8_style.sty`, 102 trang, 49 bảng, 31 hình/ảnh)
- [`Báo cáo.docx`](./Báo%20cáo.docx) — Báo cáo kỹ thuật chuẩn hóa định dạng Microsoft Word (A4, Times New Roman 12pt, lề chuẩn ICTU)
- [`GarageAI_Project/docs/latex_report/`](./GarageAI_Project/docs/latex_report/) — Mã nguồn LaTeX học thuật (`main.tex`, `ictu_v8_style.sty`, `chapters/*.tex`)
- [`GarageAI_Project/README.md`](./GarageAI_Project/README.md) — Hướng dẫn cài đặt, kiến trúc tầng, cấu hình `.env` và Docker của Backend
- [`frontend/README.md`](./frontend/README.md) — Hướng dẫn cài đặt và danh sách 16 màn hình của Frontend React 19
- [`GarageAI_Project/TEST_REPORT.md`](./GarageAI_Project/TEST_REPORT.md) — Báo cáo kết quả kiểm thử tự động (226/226) và E2E
- [`GarageAI_Project/FINAL_ACCEPTANCE_CHECKLIST.md`](./GarageAI_Project/FINAL_ACCEPTANCE_CHECKLIST.md) — Phiếu kiểm tra hoàn thành trước khi nộp (54/54 đạt)
- [`GarageAI_Project/USER_ACCEPTANCE_TEST.md`](./GarageAI_Project/USER_ACCEPTANCE_TEST.md) — Biên bản kiểm thử chấp nhận người dùng (35/35 đạt)
- [`GarageAI_Project/KT1_KT2_AI_USAGE.md`](./GarageAI_Project/KT1_KT2_AI_USAGE.md) — Nhật ký sử dụng AI trong phân tích, thiết kế và lập trình
- [`GarageAI_Project/KT3_PROMPT_EXPERIMENTS.md`](./GarageAI_Project/KT3_PROMPT_EXPERIMENTS.md) — Nhật ký thử nghiệm & tối ưu prompt (AI01, AI02, AI03)
- [`GarageAI_Project/KT3_AI_REVIEW.md`](./GarageAI_Project/KT3_AI_REVIEW.md) — Minh chứng sử dụng AI review mã nguồn & bảo mật
