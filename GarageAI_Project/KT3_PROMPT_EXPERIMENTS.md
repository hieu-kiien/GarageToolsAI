# KT3 — NHẬT KÝ THỬ NGHIỆM PROMPT

Nhật ký các lần thử nghiệm prompt của ba chức năng AI. Mỗi lần ghi rõ: dữ liệu
đầu vào, prompt đã dùng, kết quả nhận về, nhận xét và quyết định sửa hay giữ.

> **Lưu ý về phạm vi thử nghiệm.** Các lần thử nghiệm dưới đây chạy với
> `AI_PROVIDER=mock`, tức là phần trả lời do `app/ai_gateway.py` sinh ra đúng
> theo cấu trúc mà prompt yêu cầu. Mục đích là kiểm chứng **prompt, định dạng
> đầu ra, đường xử lý khi thiếu dữ liệu và quy tắc Human Review**, không phải
> đo chất lượng sinh văn bản của một mô hình ngôn ngữ cụ thể. Xem mục 6 ghi chú
> phạm vi.

---

## 1. Cách thử nghiệm

Mỗi lần thử chạy qua đúng đường dẫn HTTP mà người dùng thật sẽ gọi, nên kết quả
được lưu vào bảng `ai_results` với `review_status = 'PENDING'`:

| Bước | Thao tác |
|---|---|
| 1 | `python database/init_db.py` để dựng lại dữ liệu mẫu |
| 2 | `python -m uvicorn app.main:app --port 8010` |
| 3 | Đăng nhập `quan_ly`, mở `/ai`, chọn đối tượng và bấm **Chạy** |
| 4 | Mở `/ai/results` để xem kết quả và ghi nhận quyết định duyệt |

Prompt nằm ở `config/prompts/`, tách khỏi mã nguồn, nạp bằng
`config.settings.load_prompt()`.

---

## 2. AI01 — Tóm tắt lịch sử sửa chữa

### 2.1 Lần thử 1 — xe có lịch sử dày (biển 30A-1111)

- **Đầu vào:** xe `30A-1111` (Toyota Vios 2019), 5 lần sửa chữa trong hệ thống.
- **Prompt:** `config/prompts/history.txt`.
- **Kết quả:** tóm tắt đúng 5 lần sửa, giữ nguyên tên dịch vụ và phụ tùng đúng
  như danh mục, nêu rõ ngày sửa gần nhất.
- **Nhận xét:** bám dữ liệu, không thêm lần sửa nào.
- **Quyết định:** giữ prompt.

### 2.2 Lần thử 2 — xe chưa có lịch sử (biển 30F-6666)

- **Đầu vào:** xe `30F-6666` (Chevrolet Cruze 2018), không có phiếu sửa chữa nào.
- **Kết quả:** trả lời rằng xe chưa có lịch sử sửa chữa trong hệ thống.
- **Nhận xét:** đúng yêu cầu "không được suy diễn" trong prompt.
- **Quyết định:** giữ.

### 2.3 Lần thử 3 — ràng buộc không chẩn đoán

- **Nội dung thử:** prompt yêu cầu rõ *"không suy đoán nguyên nhân lỗi, không
  chẩn đoán lỗi mới"*.
- **Kết quả:** kết quả chỉ mô tả lịch sử, không kết luận về nguyên nhân hỏng.
- **Quyết định:** giữ. Đây là ràng buộc bắt buộc của đề tài.

---

## 3. AI02 — Giải thích dịch vụ cho khách hàng

### 3.1 Lần thử 1 — dịch vụ có đầy đủ mô tả

- **Đầu vào:** dịch vụ *Thay dầu máy và lọc gió*, có mô tả trong `services`.
- **Kết quả:** đúng ba phần — dịch vụ là gì, hạng mục đang ghi nhận, khách cần
  lưu ý; tên hạng mục lấy nguyên văn từ danh mục.
- **Quyết định:** giữ.

### 3.2 Lần thử 2 — dịch vụ thiếu mô tả (dịch vụ số 7)

- **Đầu vào:** dịch vụ *Nâng cấp ánh sáng*, cố ý để `NULL` ở `description`.
- **Kết quả:** vẫn tạo được kết quả. Phần đầu ghi đúng câu bắt buộc do prompt quy
  định: *"Danh mục chưa có mô tả cho dịch vụ này"*.
- **Nhận xét:** đây là ca bắt buộc phải chạy được chứ không được lỗi 500. Có ca kiểm
  thử tương ứng: `test_ai02_dich_vu_thieu_mo_ta_van_tao_duoc_ket_qua`.
- **Quyết định:** giữ.

### 3.3 Lần thử 3 — phong cách ngôn ngữ

- **Nội dung thử:** yêu cầu chuyển từ tiếng kỹ thuật sang tiếng dễ hiểu nhưng
  không bịa thêm thông tin.
- **Kết quả:** giữ được ranh giới: diễn giải dễ hiểu, không thêm hạng mục nào ngoài
  danh mục.
- **Quyết định:** giữ.

---

## 4. AI03 — Báo giá nháp

Đây là chức năng liên quan trực tiếp đến tiền nên được thử kỹ nhất.

### 4.1 Lần thử 1 — phiếu có hạng mục

- **Đầu vào:** phiếu sửa chữa số 10, có hạng mục dịch vụ và phụ tùng.
- **Prompt:** `config/prompts/quote.txt`, có hai biến `{{items}}` và
  `{{backend_total}}`.
- **Kết quả:** danh sách hạng mục giữ nguyên, tổng tiền ghi đúng bằng
  `backend_total` do backend tính từ CSDL.
- **Quyết định:** giữ.

### 4.2 Lần thử 2 — định dạng đầu ra phải là JSON

- **Nội dung thử:** yêu cầu model trả về đúng một khối JSON gồm `items` và `notes`.
- **Kết quả:** `app/ai_gateway.py` có đường phân tích JSON; nếu không phân tích
  được thì chuyển sang đối chiếu với danh mục và ghi cờ `is_valid`.
- **Quyết định:** giữ. Kết quả lưu `is_valid` để người duyệt thấy ngay độ tin cậy.

### 4.3 Lần thử 3 — phiếu chưa có hạng mục (phiếu số 12)

- **Đầu vào:** phiếu `RECEIVED` không có hạng mục nào.
- **Kết quả:** trả về `items` rỗng kèm giải thích rằng phiếu chưa có hạng mục
  được ghi nhận. **Không** tự thêm hạng mục, **không** lập hóa đơn.
- **Kiểm chứng bằng kiểm thử:** `test_ai03_bao_gia_khong_tao_hang_muc_that` đối
  chiếu số hàng mục và số hóa đơn trước và sau khi chạy AI.
- **Quyết định:** giữ.

### 4.4 Lần thử 4 — AI không được chốt giá

- **Nội dung thử:** sau khi chạy AI03, đối chiếu `repair_order_items` và
  `invoices` — không có bản ghi nào mới.
- **Kết quả:** đúng. Báo giá AI chỉ là văn bản ở trạng thái `PENDING`.
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

## 6. Ghi chú phạm vi và hướng nâng cấp

- Các lần thử trên dùng `AI_PROVIDER=mock`, nên phần sinh văn bản là **kết quả
  định trước** của `app/ai_gateway.py`. Chúng chứng minh prompt, định dạng đầu
  ra, xử lý thiếu dữ liệu và quy tắc duyệt là đúng; **không** chứng minh chất
  lượng văn bản của một mô hình ngôn ngữ cụ thể.
- Chưa có ca nào chạy với `AI_PROVIDER=openai`, chưa đo độ trễ thật, chưa thử mất
  mạng giữa chừng và chưa thử phản hồi sai định dạng từ mô hình thật.
- Khi chuyển sang mô hình thật cần bổ sung: ca timeout, ca phản hồi rỗng, ca
  phản hồi sai định dạng JSON, và đo độ trùng lặp giữa các lần chạy.
- Các ca timeout, phản hồi rỗng và phản hồi sai định dạng đã được viết ở
  `app/ai_gateway.py` nhưng **chưa** có ca kiểm thử tự động tương ứng.