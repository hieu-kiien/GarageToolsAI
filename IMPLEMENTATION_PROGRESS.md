# GarageTools AI — Tiến độ triển khai (Autopilot Phase 0→6)

Cập nhật: 12/10/2026  
Repo: `D:\1. LapTrinh\Nhom23_GarageToolsAI` (branch `main`)

## 0. Tổng quan

| Phase | Nội dung | Commit | Trạng thái |
|-------|----------|--------|------------|
| 0 | Git init/branch + backup `garage.db` | baseline | ✅ |
| 1 | Sửa P2/P3 (permission forms, env, wording, typo, base URL, async) | `7be8dba` | ✅ |
| 2 | Xe (VIN/km/màu) + tiếp nhận + nghiệm thu | `43cd74d` | ✅ |
| 3 | Báo giá chính thức (quotations) | `0ecff7b` | ✅ |
| 4 | Kho ledger (stock_transactions) | `5fee9bf` | ✅ |
| 5 | Bảo hành (warranties) | `f1411e2` | ✅ |
| 6 | AI gateway: fix base URL + mock httpx tests | `d2c2431` | ✅ |
| 7 | AI nâng cao (xem §3 — **đã loại khỏi đặc tả**) | — | ⛔ |

**Test hiện tại: 169/169** (`tests/run_all.py` → `TEST_REPORT.md`).

Backup DB: `backups\garage.db.pre-phase1.20261011_194251`.

---

## 1. Đã hoàn thành chi tiết

### Phase 1 — Sửa P2/P3
- 7 form GET → POST + CSRF (`yeu_cau_quyen`)
- `.env.example` đồng bộ `app/core/config.py`
- Wording, typo `XungDpot`→`XungDdot`
- `ai_gateway` base URL
- Test: `TestQuyenBieuMau`

### Phase 2 — Xe / Tiếp nhận / Nghiệm thu
- `vehicles` + VIN, màu sắc, số km
- `intake_records` (tiếp nhận)
- Nghiệm thu (COMPLETED có checklist)
- Migration `001_*`
- Test: `TestXeMoiTruong`, `TestTiepNhanNghiemThu`

### Phase 3 — Báo giá chính thức
- Bảng `quotations` + `quotation_items` (XOR CHECK)
- Quyền `quote.manage` / `quote.approve`
- Service + routes + templates `bao_gia*.html`
- Migration `002_quotations.sql`
- Test: `TestBaoGia` (15)

### Phase 4 — Kho ledger
- Bảng `stock_transactions` (RECEIPT/USAGE/RETURN/ADJUSTMENT)
- Mọi đổi stock qua `services/stock.py.ghi_giao_dich()`
- Invariant: `parts.stock == SUM(stock_transactions.qty)`
- Trang `/stock`, nhập/điều chỉnh tồn, cảnh báo tồn thấp
- Migration `003_stock_ledger.sql`
- Test: `TestKhoLedger` (11)

### Phase 5 — Bảo hành
- Bảng `warranties` (scope SERVICE/PART XOR, end_date tính backend)
- Chỉ phiếu COMPLETED; chặn trùng ACTIVE/CLAIMED
- Quyền `warranty.manage`
- Migration `004_warranties.sql`
- Test: `TestBaoHanh` (15)

### Phase 6 — AI gateway
- **Bug fix:** `OPENAI_BASE_URL` mặc định đã chứa `/chat/completions` → không nối thêm lần 2
- Hỗ trợ cả `https://api.openai.com/v1` và URL đầy đủ
- Test `TestAiGateway` (8) mock `httpx` — không cần key thật
- `.env.example` thêm `OPENAI_BASE_URL`

---

## 2. Số liệu backend

| Hạng mục | Số |
|----------|-----|
| Bảng CSDL | 21 (20 + warranties) |
| Migration | 001–004 |
| Route chính | system, auth, parties, orders, quotations, stock, warranties |
| Test | **169** (37 schema + 6 backup + 126 backend) |
| Demo users | `quan_ly`, `le_tan`, `ky_thuat_vien`, `thu_ngan` / `Garage@2026` |

---

## 3. Phase 7 — ĐÃ LOẠI khỏi đặc tả (không làm)

Tài liệu `KT1_KT2_AI_USAGE.md` ghi rõ:

> **Loại bỏ ý tưởng “AI chẩn đoán lỗi xe”** vì nằm ngoài phạm vi và rủi ro cao;
> giữ lại cơ chế Human Review.

Prompt `system.txt` cũng cấm: *“Không tự chẩn đoán lỗi xe.”*

**Không** triển khai chatbot chẩn đoán / đề suất tự động sửa chữa theo Phase 7
trong bản kế hoạch trước — mâu thuẫn với quyết định đã chốt của nhóm.

---

## 4. Việc còn lại (ngoài phạm vi autopilot backend)

Theo `DANH SACH VIEC CON LAI.txt`:

| ID | Việc | Cần gì |
|----|------|--------|
| B1 | Thiết kế giao diện (FE) | Người dùng |
| B2 | `docker compose up --build` | Có thể tự chạy thử |
| B3 | AI thật `AI_PROVIDER=openai` | **Cần OPENAI_API_KEY** |
| B4 | Ký `USER_ACCEPTANCE_TEST.md` | Người dùng |
| B5/B6 | Đo latency / demo CK-10 | Người dùng |
| B7 | Lịch sử commit git | Có thể tự làm khi được yêu cầu |

---

## 5. Cách chạy & kiểm thử

```bash
# Backend
cd GarageAI_Project
python -X uvicorn app.main:app --reload

# Full test (tạo DB tạm, không đụng garage.db thật)
python -X utf8 tests/run_all.py

# AI thật (cần key)
# .env: AI_PROVIDER=openai, OPENAI_API_KEY=sk-...
```
