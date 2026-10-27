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
| **CI/CD & Đóng gói** | [`.github/workflows/ci.yml`](./.github/workflows/ci.yml) | GitHub Actions CI tự động chạy 231 ca kiểm thử Backend + `lint`/`typecheck`/`test`/`build` Frontend; Docker & Docker Compose (`8010:8000`) |

---

## 2. Khởi chạy nhanh (Quick Start)

### Bước 1: Khởi chạy Backend FastAPI (cổng `8000`)

```powershell
cd GarageAI_Project
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Khởi tạo CSDL mẫu lần đầu (tạo garage.db với 21 bảng & dữ liệu mẫu)
python database/init_db.py

# (Tuỳ chọn) Cấu hình AI thật miễn phí bằng Groq hoặc Gemini:
# Copy-Item .env.example .env
# Mặc định không cần tạo .env hệ thống vẫn chạy ngay ở chế độ AI_PROVIDER=mock.
# Nếu muốn gọi LLM thật miễn phí (Groq), mở GarageAI_Project/.env và đặt:
#   AI_PROVIDER=groq
#   AI_MODEL=openai/gpt-oss-120b
#   AI_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx

# Chạy máy chủ FastAPI (tự động áp migrations 001 -> 005)
python -m uvicorn app.main:app --reload --port 8000
```

### Bước 2: Khởi chạy Giao diện React (Frontend — cổng `3000`)

Mở một cửa sổ terminal thứ hai:

```powershell
cd frontend
npm install
npm run dev
```

Mở trình duyệt tại **`http://localhost:3000`** (hoặc `http://127.0.0.1:8000` cho giao diện SSR dự phòng). Vite dev server tự động chuyển tiếp (proxy) mọi yêu cầu `/api/*` sang `http://127.0.0.1:8000`.

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

1. **Kiểm thử tự động Backend (`231/231 đạt`):**
   ```powershell
   cd GarageAI_Project
   python -X utf8 tests/run_all.py
   ```
   - `tests/test_schema_constraints.py`: **37/37** ca ràng buộc CSDL & dữ liệu mẫu
   - `tests/test_backup_restore.py`: **6/6** ca sao lưu & khôi phục
   - `tests/test_backend.py`: **136/136** ca ứng dụng web & `TestAiGateway` (timeout, 429, 500, JSON sai định dạng, ẩn danh PII, chống lặp dòng AI03)
   - `tests/test_api.py`: **52/52** ca tầng API JSON `/api/*` (bao gồm cô lập dữ liệu KTV & chống trùng hạng mục báo giá)

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

- [`de-tai.txt`](./de-tai.txt) & [`yeu-cau-mon-hoc.txt`](./yeu-cau-mon-hoc.txt) — Đặc tả đề tài gốc số **80277** (GarageTools AI) và Khung yêu cầu học phần **AIA331** (Chuẩn đầu ra, Rubric chấm điểm, 28 tiêu chí kiểm định)
- [`Báo cáo.pdf`](./Báo%20cáo.pdf) — Báo cáo Dự án Kết thúc Học phần hoàn thiện biên dịch bằng **XeLaTeX** (`ictu_v8_style.sty`, 56 trang, 8 chương & 3 phụ lục, đầy đủ sơ đồ và ảnh minh chứng thực tế)
- [`Slide_Thuyet_Trinh_Nhom23.html`](./Slide_Thuyet_Trinh_Nhom23.html) & [`KICH_BAN_THUYET_TRINH_VA_HOI_DAP.md`](./KICH_BAN_THUYET_TRINH_VA_HOI_DAP.md) — Bộ slide trình chiếu tương tác **Reveal.js 5.1** (12 slide, phông chữ Be Vietnam Pro, có Logo ICTU) và kịch bản thuyết trình chi tiết kèm cẩm nang hỏi đáp
- [`GarageAI_Project/docs/latex_report/`](./GarageAI_Project/docs/latex_report/) — Mã nguồn LaTeX học thuật (`main.tex`, `ictu_v8_style.sty`, `chapters/*.tex`, `figures/*.tex`)
- [`GarageAI_Project/README.md`](./GarageAI_Project/README.md) — Hướng dẫn cài đặt, kiến trúc tầng, cấu hình `.env` và Docker của Backend
- [`frontend/README.md`](./frontend/README.md) — Hướng dẫn cài đặt và danh sách 16 màn hình của Frontend React 19
- [`GarageAI_Project/TEST_REPORT.md`](./GarageAI_Project/TEST_REPORT.md) — Báo cáo kết quả kiểm thử tự động (231/231) và E2E
- [`GarageAI_Project/FINAL_ACCEPTANCE_CHECKLIST.md`](./GarageAI_Project/FINAL_ACCEPTANCE_CHECKLIST.md) — Phiếu kiểm tra hoàn thành trước khi nộp (54/54 đạt)
- [`GarageAI_Project/USER_ACCEPTANCE_TEST.md`](./GarageAI_Project/USER_ACCEPTANCE_TEST.md) — Biên bản kiểm thử chấp nhận người dùng (35/35 đạt)
- [`GarageAI_Project/KT1_KT2_AI_USAGE.md`](./GarageAI_Project/KT1_KT2_AI_USAGE.md) — Nhật ký sử dụng AI trong phân tích, thiết kế và lập trình
- [`GarageAI_Project/KT3_PROMPT_EXPERIMENTS.md`](./GarageAI_Project/KT3_PROMPT_EXPERIMENTS.md) — Nhật ký thử nghiệm & tối ưu prompt (AI01, AI02, AI03)
- [`GarageAI_Project/KT3_AI_REVIEW.md`](./GarageAI_Project/KT3_AI_REVIEW.md) — Minh chứng sử dụng AI review mã nguồn & bảo mật
