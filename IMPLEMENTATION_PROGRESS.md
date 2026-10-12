# GarageTools AI — Tiến độ triển khai (Autopilot Phase 0→6 + Free AI + Docker)

Cập nhật: 12/10/2026  
Repo: `D:\1. LapTrinh\Nhom23_GarageToolsAI` (branch `main`)

## 0. Tổng quan

| Phase | Nội dung | Trạng thái |
|-------|----------|------------|
| 0 | Git init/branch + backup `garage.db` | ✅ |
| 1 | Sửa P2/P3 (permission forms, env, wording, typo, base URL, async) | ✅ |
| 2 | Xe (VIN/km/màu) + tiếp nhận + nghiệm thu | ✅ |
| 3 | Báo giá chính thức (quotations) | ✅ |
| 4 | Kho ledger (stock_transactions) | ✅ |
| 5 | Bảo hành (warranties) | ✅ |
| 6 | AI gateway multi-provider free (Groq/OpenRouter/Gemini) + mock tests | ✅ |
| 6b | Docker Compose: build + healthcheck + volume CSDL | ✅ (cổng **8010**) |
| 7 | AI nâng cao chẩn đoán | ⛔ Loại theo KT1_KT2 |

**Test hiện tại: 176/176** (`tests/run_all.py` → `TEST_REPORT.md`).

### Đo latency AI thật (B3) — 12/10/2026, Groq free `openai/gpt-oss-120b`

| Chức năng | Latency (ms) |
|-----------|--------------|
| goi thô | min 922 · avg **1198** · max 1606 |
| Lịch sử xe | min 1852 · avg **2457** · max 2858 |
| Giải thích dịch vụ | min 3833 · avg **3992** · max 4243 |
| Báo giá nháp | min 2905 · avg **2976** · max 3110 |

→ Đủ nhanh cho demo (CK-07: phản hồi < 10s). Timeout cấu hình 30s.

**AI thật đã smoke test (12/10/2026, Groq free `openai/gpt-oss-120b`):**
- `goi()` thô → OK ~1.2s avg
- Lịch sử xe (order 1) → valid, tổng hợp 5 lần sửa
- Giải thích dịch vụ (order 1) → valid
- Báo giá nháp (order 5) → valid, tổng 2.005.000 đồng

Không cần 9Router local — chỉ tham khảo. Key free trong `.env` (không commit).

Backup DB: `backups\garage.db.pre-phase1.20261011_194251`.

---

## 1. AI multi-provider (free-tier)

Mọi provider đều đi qua giao thức **OpenAI-compatible** `chat/completions`:

| AI_PROVIDER | Base URL | Model mặc định | Biến khoá | Free |
|-------------|----------|----------------|-----------|------|
| `mock` | — | — | — | ✅ |
| `openai` | `https://api.openai.com/v1` | `gpt-4o-mini` | `OPENAI_API_KEY` | ❌ |
| `groq` | `https://api.groq.com/openai/v1` | `openai/gpt-oss-120b` | `GROQ_API_KEY` | ✅ |
| `openrouter` | `https://openrouter.ai/api/v1` | `meta-llama/llama-3.3-70b-instruct:free` | `OPENROUTER_API_KEY` | ✅ |
| `gemini` | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.0-flash` | `GOOGLE_API_KEY` | ✅ |
| `custom` | `AI_BASE_URL` | `AI_MODEL` | `AI_API_KEY` | tuỳ |

Biến chung: `AI_API_KEY`, `AI_BASE_URL`, `AI_MODEL` (ưu tiên hơn preset).  
Dev/test thiếu khoá → tự hạ về `mock` (không crash). Production thiếu khoá → fail-fast.

**Cách bật AI thật (ví dụ Groq free):**
```bash
AI_MODEL=openai/gpt-oss-120b
```

---

## 2. Docker (B2 đã xong)

```bash
cd GarageAI_Project
docker compose up -d          # app: http://127.0.0.1:8010
docker compose logs -f app
docker compose down
```

- Image: `garagetools-ai:1.0.0` (Python 3.12-slim)
- Volume `du-lieu-garage` → `/data/garage.db` (không mất dữ liệu khi rebuild)
- Entrypoint seed CSDL lần đầu từ image
- Healthcheck: `GET /healthz` → `{"trang_thai":"ok",...}`
- Đã build + chạy thử: container **healthy**, healthz **200**

Lưu ý: host 8000 đang bị chiếm → map **8010→8000**.

---

## 3. Phase 7 — ĐÃ LOẠI (không làm)

`KT1_KT2_AI_USAGE.md`: loại “AI chẩn đoán lỗi xe”. Prompt `system.txt` cấm chẩn đoán.

---

## 4. Việc còn lại (cần người dùng)

| ID | Việc | Trạng thái |
|----|------|------------|
| B3 | Gọi AI thật + đo latency | ✅ Groq free `openai/gpt-oss-120b` — xem §0 |
| B2 | Docker Compose | ✅ cổng 8010, healthy |
| B1 | Thiết kế FE đẹp | ⬜ Bạn đang nghiên cứu |
| B4 | Ký UAT | 35/35 ca — UAT-34 (mobile) + UAT-35 (XSS escape) đã minh chứng 12/10; còn ký tay |
| B5 | Đo latency CK-07 | ✅ AI avg 1.2–4.0s (< 10s) |
| B6 | Demo CK-10 | ⬜ Cần bạn chạy demo |
| B7 | Lịch sử commit git | ✅ `git log --oneline` |

### E2E UI AI qua browser thật (12/10/2026)

App local `http://127.0.0.1:8011` + Groq thật:
- Trang `/ai` hiển thị **“Chế độ đang chạy: groq”**
- AI01 lịch sử / AI02 giải thích / AI03 báo giá → flash “đang chờ duyệt”, nội dung LLM thật
- `/ai/results` → Duyệt #7 → “Đã ghi nhận quyết định” + tên người duyệt
- Mobile 390×844: UI dùng được (`docs/screenshots/ui_ai_mobile_20261012.png`)
- Ảnh desktop duyệt AI: `docs/screenshots/ui_ai_duyet_20261012.png`

Lưu ý: Docker `:8010` **không** có `.env` key → AI fallback mock. Demo AI thật
dùng uvicorn local với `.env` Groq, hoặc copy `.env` vào container.

---

## 5. Test

```bash
cd GarageAI_Project
python -X utf8 tests/run_all.py   # 176/176
```
