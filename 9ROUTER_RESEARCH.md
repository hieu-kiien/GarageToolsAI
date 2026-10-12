# 9Router — Nghiên cứu & Tích hợp GarageTools AI

Cập nhật: 12/10/2026

## 1. 9Router là gì?

**9Router** (https://9router.com, npm: `9router`, GitHub: `decolua/9router`, MIT) là **proxy/router AI chạy trên máy bạn** — không phải dịch vụ cloud lấy API key “hack”.

| Đặc điểm | Chi tiết |
|-----------|----------|
| Cài đặt | `npm install -g 9router` → `9router` |
| Dashboard | `http://localhost:20128/dashboard` |
| Endpoint AI | **OpenAI-compatible** `http://localhost:20128/v1` |
| Cổng mặc định | `20128` |
| Giá | **$0** (phần mềm free, MIT) |
| Bạn trả | Tiền cho provider (nếu có); free tier = $0 |
| Dữ liệu | SQLite cục bộ `%APPDATA%/9router` (Win) / `~/.9router` |

**Không phải** “trang web phát key AI free vĩnh viễn”. 9Router **gom** key/OAuth/free-tier bạn đã có (hoặc free provider built-in) thành **một endpoint** + **fallback tự động**.

## 2. Hỗ trợ model AI (đã nghiên cứu)

### 2.1. 9 loại dịch vụ — đều OpenAI-compatible

1. **Chat/LLM** (phần GarageTools dùng)
2. Embeddings
3. TTS · STT
4. Image gen · Vision
5. Video (Runway, Topaz)
6. Web Search (Tavily, Brave, Exa…)
7. Web Fetch

### 2.2. 60+ nhà cung cấp (nhóm)

| Tier | Ví dụ | Ghi chú |
|------|-------|---------|
| **Subscription** | Claude Code, Codex, Gemini CLI, Copilot, Cursor | OAuth; max quota đã trả |
| **Cheap** | GLM (~$0.6/1M), MiniMax (~$0.2/1M), Kimi | Rẻ, làm backup |
| **FREE** | Kiro, OpenCode Free, Vertex AI, OpenRouter free, NVIDIA NIM, Cloudflare AI, Gemini, Groq… | Free tier / free model |

**Lưu ý free tier 2026** (theo README GitHub):
- iFlow / Qwen Code / Gemini CLI free **đã discontinued**.
- **Kiro**: ~50 credits/tháng (trial 500 credits 30 ngày đầu).
- **OpenCode Free**: không cần auth, danh sách model **dao động**.
- **Vertex AI**: $300 credit GCP mới; dùng **Vertex AI Studio endpoint** (không còn trừ credit qua Gemini API endpoint).
- OpenRouter: model hậu tố `:free` + router `openrouter/free`.

### 2.3. Prefix model (ví dụ)

| Prefix | Provider |
|--------|----------|
| `kr/` | Kiro |
| `oc/` | OpenCode |
| `if/` | iFlow (có thể đã discontinued) |
| `cc/` | Claude Code |
| `openrouter/` | OpenRouter |
| `gemini/` | Gemini |
| `groq/` | Groq |
| `nvidia/` | NVIDIA NIM |
| `vertex/` | Vertex AI |
| `my9model-free` / `my9model-smart` / `my9model-fast` | Combo free / thông minh / nhanh (có repo `9router-auto-free`) |

Danh sách model thật: `GET http://localhost:20128/v1/models` (cần key nếu bật auth).

### 2.4. 3-tier fallback

```
Tier 1 Subscription → hết quota →
Tier 2 Cheap        → hết budget →
Tier 3 FREE         → vẫn chạy
```

### 2.5. Tính năng khác

- Multi-account round-robin / priority
- Format translator OpenAI ↔ Anthropic ↔ Gemini
- Quota dashboard realtime
- RTK token saver (−20–40%) + Caveman mode
- Docker: `decolua/9router:latest`
- CLI: `npx 9router connect http://host:20128 --tools claude,codex`

## 3. Cách nối GarageTools AI → 9Router

### Bước 1 — Cài & chạy 9Router

```bash
npm install -g 9router
9router --no-browser
# Dashboard: http://localhost:20128/dashboard
```

### Bước 2 — Kết free provider trên Dashboard

**Providers** → ví dụ:
1. **OpenCode Free** (không auth)
2. **Kiro** (OAuth AWS/Google/GitHub)
3. **OpenRouter** (dán key free từ openrouter.ai)
4. **Groq** (key free console.groq.com)

### Bước 3 — Lấy API key 9Router (nếu server bật auth)

Dashboard → **API Keys** → tạo key (ví dụ `garage`).

### Bước 4 — `.env` của GarageTools

```bash
AI_PROVIDER=9router
# Nếu 9router yêu cầu key:
NINEROUTER_KEY=sk_...
# Model combo free (hoặc model cụ thể):
AI_MODEL=my9model-free
# Hoặc: AI_MODEL=kr/claude-sonnet-4.5
```

### Bước 5 — Khởi động app

```bash
cd GarageAI_Project
python -X uvicorn app.main:app --reload
```

Đã code sẵn:
- Preset `9router` trong `app/core/config.py` (`AI_PROVIDERS['9router']`)
- Gateway **không bắt buộc API key** cho provider `9router` (local often `requireApiKey=false`)
- Không gửi header `Authorization` khi key rỗng

## 4. So sánh nhanh: 9Router vs gọi thẳng Groq/OpenRouter

| | Gọi thẳng | Qua 9Router |
|--|-----------|-------------|
| Cấu hình | 1 key | 1 key/dashboard + cài npm |
| Fallback free | Tay | Tự |
| Offline local | Không | Proxy local |
| Phức tạp | Thấp | Trung bình |
| Phù hợp GarageTools | Đủ (1 free provider) | Khi muốn gom nhiều free + không dính rate limit |

**Khuyến nghị GarageTools:**  
- **Đơn giản:** `AI_PROVIDER=groq` + 1 key free.  
- **Muốn “không lo 429”:** cài 9Router, ghép Groq + OpenRouter free + OpenCode, trỏ `AI_PROVIDER=9router`.

## 5. An toàn

- 9Router **open source MIT**, chạy local — không gửi hoá đơn.
- Key vẫn nằm trên máy bạn (SQLite local).
- Không commit key vào git.
- MITM bridge / intercept subscription IDE: **đọc policy từng tool** trước khi dùng.

## 6. Kết luận: không cần 9Router chạy local

**Tóm tắt:** 9Router chỉ tham khảo. GarageTools AI dùng **trực tiếp Groq** (`AI_PROVIDER=groq` + `GROQ_API_KEY` trong `.env`). Đã smoke test thật 12/10/2026: lịch sử / giải thích / báo giá đều OK (~1.6–3.1s) với model free `openai/gpt-oss-120b`.

Nếu sau này muốn 9Router làm fallback multi-provider thì preset `9router` đã có sẵn trong config — chỉ cần mở Dashboard và lấy key API.

