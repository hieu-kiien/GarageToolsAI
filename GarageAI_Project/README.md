# GarageTools AI

Hệ thống quản lý garage sửa chữa ô tô có tích hợp AI — Học phần *Ứng dụng Trí tuệ
Nhân tạo (AIA331)*, Mã số 80277, Nhóm 23.

> **Tình trạng hiện tại:** Ứng dụng đã hoàn thiện toàn diện cả **Backend FastAPI**
> lẫn **Frontend React 19 + TanStack Start** (16 màn hình nghiệp vụ kết nối API
> thật `/api/*`, kèm giao diện Jinja2 tại gốc): đăng nhập, phân quyền bốn vai trò,
> CRUD khách hàng/xe/lịch hẹn/danh mục, phiếu sửa chữa (tiếp nhận – sửa chữa –
> nghiệm thu), báo giá chính thức (áp dụng idempotent trừ tồn kho qua sổ cái),
> sổ cái tồn kho (`stock_transactions`), bảo hành, hóa đơn và thanh toán chống
> đua (`BEGIN IMMEDIATE`), báo cáo thống kê, và ba chức năng AI kèm **Human Review**
> (hỗ trợ `mock`, `groq`, `openrouter`, `gemini`, `openai`, `9router`, `custom`).
> Bộ kiểm thử tự động đạt **226/226 ca** (`tests/run_all.py`), kèm kiểm thử
> Smoke (**31/31**) và E2E nghiệp vụ (**32/32**).

---

## 1. Yêu cầu môi trường

| Thành phần | Yêu cầu |
|---|---|
| Python | 3.10 trở lên (khuyến nghị 3.12+) |
| Node.js | 20 trở lên (để chạy giao diện React `frontend/`) |
| Cơ sở dữ liệu | SQLite (tích hợp sẵn trong Python, bật WAL + `foreign_keys=ON`) |
| Trình duyệt | Bản mới của Chrome, Edge hoặc Firefox |
| Mạng | Không bắt buộc nếu dùng `AI_PROVIDER=mock` |

Docker là tuỳ chọn, dùng khi muốn đóng gói và chạy bằng container.

## 2. Cài đặt

### 2.1. Backend (`GarageAI_Project/`)

```bash
git clone <địa-chỉ-kho-mã-nguồn>
cd GarageAI_Project

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

### 2.2. Frontend React (`frontend/`)

```bash
cd ../frontend
npm install
```

## 3. Tạo cơ sở dữ liệu và kiểm thử

```bash
cd GarageAI_Project
python database/init_db.py
```

Lệnh này đọc `database/schema.sql` rồi `database/seed_data.sql`, tạo ra tệp
`garage.db` ở thư mục gốc với 21 bảng (17 bảng nghiệp vụ lõi + 4 bảng mở rộng),
37 chỉ mục và 171 dòng dữ liệu mẫu. Khi khởi động ứng dụng với `AUTO_MIGRATE=true`
(mặc định), các bản nâng cấp trong `database/migrations/` (`001` → `005`) sẽ tự động
được áp một cách idempotent.

Chạy toàn bộ bộ kiểm thử tự động Backend:

```bash
python -X utf8 tests/run_all.py
```

Kết quả mong đợi: **226/226 đạt** (37 ca ràng buộc CSDL + 6 ca sao lưu/khôi phục +
133 ca ứng dụng web + 50 ca API JSON `/api/*`), tự sinh lại `TEST_REPORT.md`.

Kiểm tra chất lượng Frontend (`frontend/`):

```bash
cd ../frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

## 4. Cấu hình biến môi trường

```bash
cd GarageAI_Project
cp .env.example .env        # Windows: copy .env.example .env
```

Mở `.env` và điền giá trị phù hợp:

- `SECRET_KEY` — bắt buộc đổi khi triển khai thật (`APP_ENV=production`).
  Sinh bằng: `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- `AI_PROVIDER` — chọn nhà cung cấp AI: `mock` (mặc định, không cần mạng),
  `groq` (free tier nhanh, khuyến nghị demo), `openrouter`, `gemini`, `openai`,
  `9router` hoặc `custom`.
- `AI_API_KEY` (hoặc `GROQ_API_KEY` / `OPENROUTER_API_KEY` / `GOOGLE_API_KEY` /
  `OPENAI_API_KEY`) — khoá API tương ứng khi gọi mô hình ngôn ngữ thật.

> Tệp `.env` đã nằm trong `.gitignore`. **Không bao giờ** commit tệp này.

## 5. Chạy ứng dụng

### Cách 1: Chạy đầy đủ Backend FastAPI + Frontend React (Khuyến nghị khi demo)

Terminal 1 — Chạy Backend tại cổng `8000`:

```bash
cd GarageAI_Project
python -m uvicorn app.main:app --reload --port 8000
```

Terminal 2 — Chạy Frontend React (Vite tự proxy `/api` về `http://127.0.0.1:8000`):

```bash
cd frontend
npm run dev
```

Mở trình duyệt tại địa chỉ Vite hiển thị (mặc định <http://localhost:3000> hoặc <http://localhost:5173>).

### Cách 2: Chạy giao diện Jinja2 tích hợp sẵn trên Backend

Chỉ cần chạy Terminal 1 ở trên và mở trình duyệt tại <http://127.0.0.1:8000>.

## 6. Tài khoản demo

| Vai trò | Tên đăng nhập | Mật khẩu |
|---|---|---|
| Quản lý (`MANAGER`) | `quan_ly` | `Garage@2026` |
| Lễ tân (`RECEPTIONIST`) | `le_tan` | `Garage@2026` |
| Kỹ thuật viên (`TECHNICIAN`) | `ky_thuat_vien` | `Garage@2026` |
| Thu ngân (`CASHIER`) | `thu_ngan` | `Garage@2026` |

Mật khẩu được lưu dạng băm **Argon2id** (thư viện `argon2-cffi`). Nếu môi trường
không cài được thư viện này, ứng dụng tự chuyển sang PBKDF2-SHA256 với 200.000
vòng lặp để không dừng đột ngột, và mỗi tài khoản vẫn có muối riêng.

Đổi mật khẩu hoặc khoá tài khoản sẽ làm mất hiệu lực mọi phiên đang đăng nhập
nhờ cột `auth_version`.

> Đây là tài khoản dùng cho học tập và demo. Khi triển khai thật phải đổi toàn bộ
> mật khẩu và tạo tài khoản riêng cho từng nhân viên.

## 7. Cấu trúc dự án

```
Nhom23_GarageToolsAI/
├── GarageAI_Project/           # Backend FastAPI + CSDL + Kiểm thử + Tài liệu
│   ├── app/
│   │   ├── main.py             # create_app(): auto-migrate, middleware, exception handlers, routers
│   │   ├── models.py           # Pydantic v2: kiểm tra dữ liệu đầu vào/ra
│   │   ├── crud.py             # Tầng truy cập: tham số hoá, whitelist, phân trang
│   │   ├── ai_gateway.py       # AI Gateway đa provider (mock/groq/openrouter/gemini/openai/9router)
│   │   ├── core/               # Nền tảng chung (config, db BEGIN IMMEDIATE, security, ratelimit, flash...)
│   │   ├── services/           # Nghiệp vụ thuần (auth, security_matrix, orders, quotations, stock,
│   │   │                       #   warranties, billing, parties, catalog, ai, reports)
│   │   ├── routes/             # Route HTML Jinja2 + nhánh routes/api/ (JSON API cho React FE)
│   │   ├── templates/          # Giao diện Jinja2
│   │   └── static/             # CSS tĩnh
│   ├── config/prompts/         # 4 tệp prompt: system.txt, history.txt, explain.txt, quote.txt
│   ├── database/
│   │   ├── schema.sql          # 21 bảng (17 bảng lõi + 4 bảng mở rộng) kèm CHECK/FK và 37 chỉ mục
│   │   ├── seed_data.sql       # 171 dòng dữ liệu mẫu
│   │   ├── migrations/         # 001 → 005 + run_missing.py (idempotent auto-migrate)
│   │   ├── generate_seed.py    # Sinh lại seed_data.sql
│   │   └── init_db.py          # Khởi tạo garage.db từ đầu
│   ├── docs/                   # 16 sơ đồ thiết kế (diagrams_final/) + script chụp màn hình
│   ├── screenshots/            # 18 ảnh màn hình thực tế (giao diện React 19 + TanStack Start)
│   ├── tests/
│   │   ├── test_schema_constraints.py   # 37 ca ràng buộc CSDL
│   │   ├── test_backup_restore.py       # 6 ca sao lưu/khôi phục
│   │   ├── test_backend.py              # 133 ca ứng dụng web & AI Gateway
│   │   ├── test_api.py                  # 50 ca tầng JSON API (/api/*)
│   │   └── run_all.py                   # Chạy toàn bộ 226 ca, sinh TEST_REPORT.md
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-entrypoint.sh
│   ├── .env.example
│   └── requirements.txt
├── frontend/                   # Giao diện React 19 + TanStack Start + Tailwind v4 + shadcn/ui
│   ├── src/
│   │   ├── components/         # AppShell (Sidebar, Đăng nhập, Đổi mật khẩu) + bộ UI shadcn
│   │   ├── lib/rbac.tsx        # RoleProvider, ma trận quyền AREA_QUYEN, định dạng tiền/giờ VN
│   │   ├── routes/             # 16 màn hình nghiệp vụ đầy đủ
│   │   ├── services/api.ts     # Khách HTTP duy nhất kèm CSRF + TanStack Query options
│   │   ├── test/               # Kiểm thử Vitest cho routing và RBAC/định dạng
│   │   └── types/index.ts      # Kiểu TypeScript đồng bộ với backend
│   ├── README.md
│   └── README_AI_HANDOFF.md    # Hợp đồng giao tiếp Frontend ↔ Backend API
├── scripts/                    # Kịch bản vận hành & kiểm thử thực tế (PowerShell)
│   ├── smoke.ps1               # 31 ca kiểm thử nhanh HTTP + RBAC + CSRF
│   ├── e2e.ps1                 # 32 ca kiểm thử E2E xuyên suốt quy trình garage
│   ├── backup.ps1              # Sao lưu trực tuyến an toàn qua sqlite3 .backup
│   └── restore.ps1             # Khôi phục kèm kiểm tra PRAGMA integrity_check
└── .github/workflows/ci.yml    # GitHub Actions CI cho cả Backend (226 ca) và Frontend
```

### Hợp đồng ngữ cảnh cho giao diện

- **Giao diện React (`frontend/`)**: Gọi trực tiếp các endpoint `/api/*`, xác thực qua cookie `garage_session` (HttpOnly) và gửi kèm header `X-CSRF-Token` đọc từ cookie `garage_csrf`. Chi tiết đầy đủ nằm tại `../frontend/README_AI_HANDOFF.md`.
- **Giao diện Jinja2 (`app/templates/`)**: Mọi trang đi qua `app/routes/__init__.py: render()` luôn có sẵn `user`, `csrf_token`, `quyen[...]`, `flash.loi`/`flash.thong_bao`, `loi`, `dong`/`tong_so_ban_ghi`/`trang`/`tong_trang`, cùng các hàm định dạng `format_tien`, `format_ngay`, `ten_trang_thai`, `vai_tro_ten`.

## 8. Ba chức năng AI

| Mã | Chức năng | File prompt | Biến đầu vào |
|---|---|---|---|
| AI01 | Tóm tắt lịch sử sửa chữa | `config/prompts/history.txt` | `{{repair_history}}` |
| AI02 | Giải thích dịch vụ cho khách | `config/prompts/explain.txt` | `{{service}}` |
| AI03 | Báo giá nháp | `config/prompts/quote.txt` | `{{items}}`, `{{backend_total}}` |

Nguyên tắc bất di bất dịch: **AI không phải nguồn của dữ liệu nghiệp vụ.** Giá,
số lượng và tổng tiền đều do backend đọc từ CSDL và tự tính. Kết quả AI luôn
lưu ở trạng thái `PENDING` và phải được nhân viên có quyền `ai.review` duyệt
trước khi sử dụng.

## 9. Sao lưu và khôi phục

Có thể sử dụng script tự động ở thư mục gốc của kho mã nguồn (sao lưu an toàn kể cả khi đang bật WAL và tự động kiểm tra `PRAGMA integrity_check`):

```powershell
# Từ thư mục gốc Nhom23_GarageToolsAI:
.\scripts\backup.ps1
.\scripts\restore.ps1 -File backups\garage-<timestamp>.db
```

Hoặc sao lưu thủ công khi đã dừng ứng dụng:

```bash
copy garage.db ..\backups\garage_2026-10-16.db     # Windows
cp garage.db ../backups/garage_2026-10-16.db       # macOS / Linux
```

## 10. Trạng thái triển khai

| Hạng mục | Trạng thái |
|---|---|
| Schema cơ sở dữ liệu (21 bảng: 17 bảng lõi + 4 bảng mở rộng, 37 chỉ mục) | Hoàn thành |
| Dữ liệu mẫu (171 dòng) & Auto-migration (`001` → `005`) | Hoàn thành |
| 16 sơ đồ thiết kế (`docs/diagrams_final/`) | Hoàn thành |
| Prompt ba chức năng AI (`config/prompts/`) | Hoàn thành |
| Đăng nhập, phiên ký, phân quyền bốn vai trò (RBAC) | Hoàn thành |
| CRUD nghiệp vụ + tìm kiếm, lọc, sắp xếp, phân trang | Hoàn thành |
| Tiếp nhận xe (`intake_records`), phiếu sửa chữa, nghiệm thu (`acceptance_at`) | Hoàn thành |
| Báo giá chính thức (`quotations`) & áp dụng idempotent trừ tồn kho | Hoàn thành |
| Sổ cái tồn kho (`stock_transactions`) & đối soát `SUM(ledger) == stock` | Hoàn thành |
| Bảo hành (`warranties`) theo hạng mục phiếu đã hoàn thành | Hoàn thành |
| Hóa đơn và thanh toán chống đua (`BEGIN IMMEDIATE`), huỷ khoản thu nhầm | Hoàn thành |
| Dashboard và 5 báo cáo thống kê | Hoàn thành |
| Ba chức năng AI và Human Review (cả `mock` lẫn model thật qua Groq/OpenAI-compat) | Hoàn thành |
| Ca kiểm thử timeout, lỗi 429/500, phản hồi rỗng / sai định dạng AI (`TestAiGateway`) | Hoàn thành |
| Giao diện chính thức React 19 + TanStack Start (16 màn hình kết nối API thật) | Hoàn thành |
| Kiểm thử tự động Backend (**226/226 ca**) + Frontend (`lint`/`typecheck`/`test`/`build`) | Hoàn thành |
| Kịch bản Smoke (**31/31**), E2E (**32/32**) và UAT (**35/35**) | Hoàn thành |
| Dockerfile, `docker-compose.yml` (cổng `8010`) và GitHub Actions CI | Hoàn thành |

Chi tiết nghiệm thu nằm ở `FINAL_ACCEPTANCE_CHECKLIST.md` và `TEST_REPORT.md`.

## 11. Chạy bằng Docker

```bash
cd GarageAI_Project
docker compose up --build -d
```

Mở trình duyệt tại <http://127.0.0.1:8010> (`docker-compose.yml` ánh xạ cổng
`8010:8000` và gắn volume `du-lieu-garage:/data` để bảo toàn dữ liệu khi rebuild).
Kiểm tra sức khoẻ container tại <http://127.0.0.1:8010/healthz>.

## 12. Chụp lại ảnh màn hình

```bash
python -m uvicorn app.main:app --port 8010
python docs/chup_man_hinh.py
```

Tệp ảnh nằm ở `screenshots/` và `docs/screenshots/`, bảng mô tả nằm ở `docs/BANG_ANH.md`.

## 13. Tài liệu liên quan

| Tài liệu | Nội dung |
|---|---|
| `KT3_PROMPT_EXPERIMENTS.md` | Nhật ký thử nghiệm và tối ưu prompt ba chức năng AI |
| `KT1_KT2_AI_USAGE.md` | Nhật ký sử dụng AI trong phân tích, thiết kế và lập trình |
| `KT3_AI_REVIEW.md` | Minh chứng sử dụng AI review mã nguồn và cải thiện bảo mật |
| `TEST_REPORT.md` | Báo cáo kết quả 226/226 ca kiểm thử tự động + Smoke/E2E |
| `USER_ACCEPTANCE_TEST.md` | Kết quả 35/35 ca kiểm thử chấp nhận người dùng (UAT) |
| `FINAL_ACCEPTANCE_CHECKLIST.md` | Phiếu kiểm tra hoàn thành toàn bộ tiêu chí trước khi nộp |