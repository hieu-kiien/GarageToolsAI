# KT3 — NHẬT KÝ THỬ NGHIỆM PROMPT

Nhật ký các lần thử nghiệm prompt của ba chức năng AI. Mỗi lần ghi rõ: dữ liệu
đầu vào, prompt đã dùng, kết quả nhận về, nhận xét và quyết định sửa hay giữ.

> **Lưu ý về phạm vi thử nghiệm.** Các lần thử nghiệm dưới đây đã được thực hiện
> trên cả hai chế độ:
> 1. **`AI_PROVIDER=mock`**: kiểm chứng tính tất định của prompt, định dạng đầu ra,
>    đường xử lý khi thiếu dữ liệu và quy tắc Human Review (phục vụ chạy CI tự động).
> 2. **`AI_PROVIDER=groq` (model thật `openai/gpt-oss-120b`)**: kiểm chứng chất lượng
>    sinh văn bản thực tế, đo độ trễ phản hồi (trung bình 1.2s – 4.0s, đạt tiêu chí
>    CK-07 < 10s) và kiểm tra cơ chế lọc kết quả JSON từ mô hình ngôn ngữ lớn.

---

## 1. Cách thử nghiệm

Mỗi lần thử chạy qua đúng đường dẫn HTTP (`/ai/*` hoặc `/api/ai/run`) mà người
dùng thật gọi, kết quả được lưu vào bảng `ai_results` với `review_status = 'PENDING'`:

| Bước | Thao tác |
|---|---|
| 1 | `python database/init_db.py` để dựng lại dữ liệu mẫu |
| 2 | `python -m uvicorn app.main:app --port 8000` |
| 3 | Đăng nhập `quan_ly`, mở `/ai` (hoặc `/ai-review` trên React), chọn đối tượng và bấm **Chạy** |
| 4 | Mở danh sách kết quả để đối chiếu nội dung và ghi nhận quyết định duyệt (`APPROVED` / `REJECTED`) |

Prompt nằm ở `config/prompts/`, tách khỏi mã nguồn, nạp bằng
`config.get_settings().load_prompt()`.

---

## 2. AI01 — Tóm tắt lịch sử sửa chữa

### 2.1 Lần thử 1 — xe có lịch sử dày (biển 30A-1111)

- **Đầu vào:** xe `30A-1111` (Toyota Vios 2019), 5 lần sửa chữa trong hệ thống.
- **Prompt:** `config/prompts/history.txt`.
- **Kết quả (`mock` & `groq`):** tóm tắt đúng 5 lần sửa, giữ nguyên tên dịch vụ và
  phụ tùng đúng như danh mục, nêu rõ ngày sửa gần nhất. Độ trễ trên Groq `openai/gpt-oss-120b`: trung bình **2.46s** (min 1.85s, max 2.86s).
- **Nhận xét:** bám dữ liệu, không bịa thêm lần sửa nào.
- **Quyết định:** giữ prompt.

### 2.2 Lần thử 2 — xe chưa có lịch sử (biển 30F-6666)

- **Đầu vào:** xe `30F-6666` (Chevrolet Cruze 2018), không có phiếu sửa chữa nào.
- **Kết quả:** trả lời rõ rằng xe chưa có lịch sử sửa chữa trong hệ thống.
- **Nhận xét:** đúng yêu cầu *"không được suy diễn"* trong prompt.
- **Quyết định:** giữ.

### 2.3 Lần thử 3 — ràng buộc không chẩn đoán

- **Nội dung thử:** prompt yêu cầu rõ *"không suy đoán nguyên nhân lỗi, không
  chẩn đoán lỗi mới"*.
- **Kết quả:** kết quả chỉ mô tả lịch sử đã ghi nhận, không kết luận về nguyên nhân hỏng.
- **Quyết định:** giữ. Đây là ràng buộc bắt buộc của đề tài.

---

## 3. AI02 — Giải thích dịch vụ cho khách hàng

### 3.1 Lần thử 1 — dịch vụ có đầy đủ mô tả

- **Đầu vào:** dịch vụ *Thay dầu máy và lọc gió*, có mô tả trong bảng `services`.
- **Kết quả (`mock` & `groq`):** đúng ba phần — dịch vụ là gì, hạng mục đang ghi nhận,
  khách cần lưu ý; tên hạng mục lấy nguyên văn từ danh mục. Độ trễ trên Groq: trung bình **3.99s**.
- **Quyết định:** giữ.

### 3.2 Lần thử 2 — dịch vụ thiếu mô tả (dịch vụ số 7)

- **Đầu vào:** dịch vụ *Nâng cấp ánh sáng*, cố ý để `NULL` ở `description`.
- **Kết quả:** vẫn tạo được kết quả hợp lệ. Phần đầu ghi đúng câu bắt buộc do prompt quy
  định: *"Danh mục chưa có mô tả cho dịch vụ này"*.
- **Nhận xét:** đây là ca biên bắt buộc phải chạy được chứ không được lỗi 500. Có ca kiểm
  thử tự động: `test_ba_chuc_nang_sinh_ket_qua_pending` (`subTest service_id=7`).
- **Quyết định:** giữ.

### 3.3 Lần thử 3 — phong cách ngôn ngữ

- **Nội dung thử:** yêu cầu chuyển từ thuật ngữ kỹ thuật sang ngôn ngữ dễ hiểu cho
  chủ xe nhưng không bịa thêm thông tin.
- **Kết quả:** giữ được ranh giới: diễn giải dễ hiểu, không thêm hạng mục nào ngoài
  danh mục.
- **Quyết định:** giữ.

---

## 4. AI03 — Báo giá nháp

Đây là chức năng liên quan trực tiếp đến tiền nên được thử kỹ nhất.

### 4.1 Lần thử 1 — phiếu có hạng mục

- **Đầu vào:** phiếu sửa chữa số 5 / số 10, có hạng mục dịch vụ và phụ tùng.
- **Prompt:** `config/prompts/quote.txt`, có hai biến `{{items}}` và
  `{{backend_total}}`.
- **Kết quả (`mock` & `groq`):** danh sách hạng mục giữ nguyên, tổng tiền ghi đúng bằng
  `backend_total` do backend tính từ CSDL. Độ trễ trên Groq: trung bình **2.98s**.
- **Quyết định:** giữ.

### 4.2 Lần thử 2 — định dạng đầu ra phải là JSON & chống ảo giác (hallucination)

- **Nội dung thử:** yêu cầu model trả về khối JSON gồm `items`, `total` và `notes`.
- **Kết quả:** `app/ai_gateway.py` dùng `_phan_tich_json()` bóc tách JSON (kể cả khi
  model bọc trong ```json ... ```), lọc lại chỉ giữ các dòng khớp hoàn toàn tên, số
  lượng và đơn giá với CSDL; nếu model trả tổng khác `backend_total` thì hệ thống
  ghi cảnh báo và ép dùng `backend_total`. Nếu model trả văn bản không phải JSON,
  hệ thống tự dựng bảng nháp từ dữ liệu CSDL để không bao giờ lỗi 500.
- **Quyết định:** giữ.

### 4.3 Lần thử 3 — phiếu chưa có hạng mục (phiếu số 12)

- **Đầu vào:** phiếu `RECEIVED` không có hạng mục nào.
- **Kết quả:** trả về thông báo rõ rằng phiếu chưa có hạng mục được ghi nhận.
  **Không** tự thêm hạng mục, **không** lập hóa đơn.
- **Kiểm chứng bằng kiểm thử:** `test_ai_khong_tao_hang_muc_hoac_hoa_don` đối
  chiếu số hạng mục và số hóa đơn trước và sau khi chạy AI.
- **Quyết định:** giữ.

### 4.4 Lần thử 4 — AI không được chốt giá

- **Nội dung thử:** sau khi chạy AI03, đối chiếu `repair_order_items` và
  `invoices` — không có bản ghi nào mới.
- **Kết quả:** đúng. Báo giá AI chỉ là văn bản tư vấn ở trạng thái `PENDING`.
- **Quyết định:** giữ. Đây là ranh giới quan trọng nhất của cả đề tài.

---

## 5. Human Review sau mỗi lần thử

| Kiểm tra | Kết quả |
|---|---|
| Kết quả mới luôn ở `PENDING` | Đạt |
| `reviewed_by` và `reviewed_at` chỉ được ghi khi có quyết định | Đạt |
| Không duyệt lại được kết quả đã xử lý | Đạt (`WHERE review_status = 'PENDING'`) |
| Người không có `ai.review` bị từ chối với mã 403 | Đạt |

---

## 6. Kiểm thử lỗi kết nối, giới hạn ngữ cảnh và độ trễ (Tiêu chí KT3-07, CK-07, D9)

| Tình huống kiểm thử | Cách kiểm chứng | Kết quả |
|---|---|---|
| Timeout (`httpx.TimeoutException`) | `TestAiGateway.test_429_va_500_bi_chuyen_sang_mock` | Đạt (bắt ngoại lệ, fallback an toàn sang mock hoặc báo lỗi thân thiện) |
| Rate limit (HTTP 429) & Lỗi máy chủ AI (HTTP 500) | `TestAiGateway.test_429_va_500_bi_chuyen_sang_mock` | Đạt |
| Phản hồi rỗng / JSON sai định dạng / bọc markdown | `TestAiGateway.test_phan_tich_json_boc_khoi` & `test_429_va_500_bi_chuyen_sang_mock` | Đạt |
| Dữ liệu đầu vào quá dài (> `AI_MAX_CONTEXT`) | `TestAiGateway.test_cat_ngu_dung_vuot_gioi_han` | Đạt (tự cắt ngắn kèm chú thích `[dữ liệu bị cắt bớt...]`) |
| Đo độ trễ mô hình thật (`groq` — `openai/gpt-oss-120b`) | Đo thực nghiệm 12/10/2026 (`Báo cáo.pdf` Chương 7) | Đạt: gọi thô **1.20s**, AI01 **2.46s**, AI02 **3.99s**, AI03 **2.98s** (đều < ngưỡng 10s của CK-07) |