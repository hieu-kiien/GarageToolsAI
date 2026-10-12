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

**Test hiện tại: 174/174** (`tests/run_all.py` → `TEST_REPORT.md`).

Backup DB: `backups\garage.db.pre-phase1.20261011_194251`.

---

## 1. AI multi-provider (free-tier)

Mọi provider đều đi qua giao thức **OpenAI-compatible** `chat/completions`:

| AI_PROVIDER | Base URL | Model mặc định | Biến khoá | Free |
|-------------|----------|----------------|-----------|------|
| `mock` | — | — | — | ✅ |
| `openai` | `https://api.openai.com/v1` | `gpt-4o-mini` | `OPENAI_API_KEY` | ❌ |
| `groq` | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` | `GROQ_API_KEY` | ✅ |
| `openrouter` | `https://openrouter.ai/api/v1` | `meta-llama/llama-3.3-70b-instruct:free` | `OPENROUTER_API_KEY` | ✅ |
| `gemini` | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.0-flash` | `GOOGLE_API_KEY` | ✅ |
| `custom` | `AI_BASE_URL` | `AI_MODEL` | `AI_API_KEY` | tuỳ |

Biến chung: `AI_API_KEY`, `AI_BASE_URL`, `AI_MODEL` (ưu tiên hơn preset).  
Dev/test thiếu khoá → tự hạ về `mock` (không crash). Production thiếu khoá → fail-fast.

**Cách bật AI thật (ví dụ Groq free):**
```bash
# GarageAI_Project/.env
AI_PROVIDER=groq
GROQ_API_KEY=gsk_...
# hoặc dùng biến chung:
# AI_API_KEY=gsk_...
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

| ID | Việc | Ghi chú |
|----|------|---------|
| B3 | Gọi AI thật + đo latency | Cần `GROQ_API_KEY` / `OPENROUTER_API_KEY` / `GOOGLE_API_KEY` |
| B1 | Thiết kế FE | Hợp đồng trong README.md |
| B4 | Ký UAT | 33/35 ca đã có minh chứng tự động |
| B5/B6 | Demo CK-07/CK-10 | Người dùng |

---

## 5. Test

```bash
cd GarageAI_Project
python -X utf8 tests/run_all.py   # 174/174
```
