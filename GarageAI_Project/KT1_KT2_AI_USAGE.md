# NHẬT KÝ SỬ DỤNG AI TRONG PHÂN TÍCH VÀ LẬP TRÌNH

Nhóm 23 — Học phần *Ứng dụng Trí tuệ Nhân tạo (AIA331)*, Mã số 80277
Tương ứng tiêu chí **KT1-09** và **KT2-09**.

> **Cách đọc tài liệu này**
> Phần lượt hỏi – trả lời nguyên văn đã được rút gọn thành bảng để đưa vào báo
> cáo. Mục *Nguyên văn* ở cuối mỗi phần là chỗ dành cho lượt trao đổi đầy đủ;
> nhóm bổ sung vào đó sau khi thực hiện lại từng bước.
>
> Nguyên tắc nhóm đã áp dụng: **AI được dùng để sinh phương án, không dùng để
> quyết định.** Mọi ý đều được kiểm chứng lại trước khi đưa vào thiết kế, và
> những ý bị loại đều được ghi lại.

---

## Phần 1 — KT1: Phân tích và thiết kế

### 1.1. Phân rã quy trình nghiệp vụ garage

| | |
|---|---|
| **Prompt** | *"Phân tích quy trình garage sửa chữa ô tô từ lúc khách đến xe đến lúc hoàn tất thanh toán, nêu rõ dữ liệu phát sinh ở mỗi bước."* |
| **AI hỗ trợ** | Đề xuất 5 actor và nhóm chức năng quản lý |
| **Nhóm kiểm chứng** | Bỏ nhóm *"công sửa chữa"* vì không có bảng dữ liệu riêng; gộp vào bảng dịch vụ sửa chữa |

**Vì sao loại bỏ:** nhóm "công sửa chữa" được AI đề xuất nhưng thực tế garage
tính công tác thành phần đơn giá của dịch vụ, không tách thành một đối tượng dữ
liệu riêng. Nhóm đối chiếu với nghiệp vụ thật rồi mới loại.

### 1.2. Đề xuất lược đồ cơ sở dữ liệu

| | |
|---|---|
| **Prompt** | *"Từ quy trình trên, đề xuất lược đồ CSDL gồm các bảng, khóa chính, khóa ngoại và ràng buộc cần có."* |
| **AI hỗ trợ** | Gợi ý 15 bảng cùng các quan hệ 1–N |
| **Nhóm kiểm chứng** | Loại bỏ các bảng không dùng; thêm bảng danh mục cửa hàng sau khi mở rộng mô-đun cửa hàng |

**Điểm phải tự kiểm, không tin AI:** AI đề xuất lưu cả `customer_id` lẫn
`vehicle_id` ở bảng lịch hẹn mà không giải thích lý do. Nhóm đã bổ sung ghi chú
giải thích tại mục 4.1 của báo cáo: giữ `customer_id` để tra cứu nhanh theo khách
và cho phép đặt lịch trước khi chốt xe, đồng thời backend phải kiểm tra
`customer_id` khớp với `customer_id` của xe.

### 1.3. Trạng thái phiếu sửa chữa

| | |
|---|---|
| **Prompt** | *"Phiếu sửa chữa trong garage có những trạng thái nào, chuyển trạng thái theo điều kiện gì?"* |
| **AI hỗ trợ** | Gợi ý `RECEIVED – INSPECTING – ESTIMATING – REPAIRING – COMPLETED` |
| **Nhóm kiểm chứng** | Thêm nhánh hủy từ `RECEIVED` theo quy định thực tế; thêm vòng lặp `REPAIRING → INSPECTING` khi cần kiểm tra lại |

### 1.4. Vị trí ứng dụng AI

| | |
|---|---|
| **Prompt** | *"Trong ứng dụng quản lý garage, những chức năng AI nào hợp lý và cần kiểm soát ra sao?"* |
| **AI hỗ trợ** | Gợi ý tóm tắt lịch sử, giải thích dịch vụ, báo giá nháp |
| **Nhóm kiểm chứng** | **Loại bỏ ý tưởng "AI chẩn đoán lỗi xe"** vì nằm ngoài phạm vi và rủi ro cao; giữ lại cơ chế Human Review |

**Điểm quan trọng nhất của KT1:** AI có thể gợi ý những chức năng nghe rất hấp dẫn
nhưng không phù hợp với đề tài và không kiểm soát được. Ý tưởng chẩn đoán lỗi xe
đã bị loại dù model đề xuất rất tự tin.

---

## Phần 2 — KT2: Lập trình

| Hạng mục | Yêu cầu đưa cho AI | Kết quả AI trả về | Nhóm kiểm chứng và chỉnh sửa |
|---|---|---|---|
| Khung CRUD | Sinh khung route CRUD khách hàng cho FastAPI kèm template Jinja2 | Route, template và form đầy đủ | AI cho phép nhập giá từ phía client; **nhóm sửa thành luôn đọc giá từ CSDL** |
| Gọi AI | Viết hàm gọi API của nhà cung cấp AI trong Python | Hàm `requests.post` không có timeout | Bổ sung timeout 15 giây, fallback sang chế độ Mock, không ghi API key vào log |
| Tính tiền | Viết hàm tính tổng tiền hóa đơn | Dùng số thực `float` | **Sửa sang tiền tệ nguyên**, chỉ làm tròn ở bước hiển thị |
| Tổ chức prompt | Gợi ý cách tổ chức prompt để dễ bảo trì | Nội dung prompt nằm trực tiếp trong hàm gọi AI | Tách prompt sang tệp `config/prompts/*.txt`; backend chỉ nạp tệp và ghép biến |
| Gỡ lỗi RBAC | Sửa lỗi trả về 403 khi tài khoản Thu ngân mở trang quản lý | Gợi ý thêm kiểm tra vai trò trước khi render | Tách hàm kiểm tra quyền dùng chung cho mọi route, bổ sung ca kiểm thử TC03 |
| Kiểm thử | Sinh ca kiểm thử cho luồng thanh toán hóa đơn | Bộ ca kiểm thử cơ bản theo luồng thành công | **Bổ sung ca thanh toán vượt số tiền phải thu và ca thanh toán bằng 0** |

### Hai lỗi AI tạo ra đã bị bắt

**1. Rò rỉ logic tiền ra phía client.** Trong khung CRUD đầu tiên, AI cho phép giao
diện gửi giá dịch vụ lên backend. Nếu triển khai nguyên xi, người dùng có thể sửa
giá trong yêu cầu. Nhóm đã sửa để backend luôn đọc giá trong CSDL và tự tính tổng.
Đây cũng là nguyên tắc đã được khẳng định ở mục 8.5 của báo cáo.

**2. Dùng số thực cho tiền.** Cộng nhiều dòng số thực sẽ sinh sai số tiền do làm
tròn. Nhóm chuyển toàn bộ cột tiền sang `INTEGER` và chỉ chia khi hiển thị — quyết
định này đã được ghi thành chú thích ở đầu `database/schema.sql`.

---

## Phần 3 — Nguyên tắc nhóm đã áp dụng xuyên suốt

1. Không chấp nhận nội dung AI chỉ vì nó nghe hợp lý. Ba ý tưởng đã bị loại vì
   sai phạm vi hoặc không kiểm soát được.
2. Với các phần liên quan đến tiền, quyền và dữ liệu, nhóm đọc trực tiếp logic
   backend thay vì tin phần diễn giải của AI.
3. Mọi thay đổi do AI gợi ý đều được kiểm lại bằng kiểm thử trước khi giữ.
4. Phần lượt hỏi – trả lời nguyên văn được lưu lại để đối chiếu khi bảo vệ.

---

## Nguyên văn

> Phần ghi lại các lượt trao đổi tiêu biểu với công cụ AI và quyết định kiểm chứng của nhóm.
>
> ```text
> Bước 1.1 – Phân rã quy trình garage
> Prompt:
>   "Phân tích quy trình garage sửa chữa ô tô từ lúc khách đưa xe đến lúc hoàn tất
>    thanh toán, nêu rõ các vai trò (actor) và dữ liệu phát sinh ở mỗi bước."
> Phản hồi AI (tóm lược):
>   - 5 vai trò: Quản lý, Lễ tân, Kỹ thuật viên, Thu ngân, Khách hàng.
>   - Quy trình: Đặt lịch -> Tiếp nhận xe -> Kiểm tra/Báo giá -> Sửa chữa & Xuất
>     phụ tùng -> Nghiệm thu -> Lập hóa đơn & Thanh toán -> Bảo hành.
>   - Đề xuất tách bảng "công sửa chữa (labor_costs)" riêng với "dịch vụ (services)".
> Quyết định của nhóm:
>   - Giữ 4 vai trò đăng nhập hệ thống (MANAGER, RECEPTIONIST, TECHNICIAN, CASHIER);
>     Khách hàng là đối tượng dữ liệu (bảng customers), không có tài khoản đăng nhập.
>   - Loại bỏ bảng "labor_costs" riêng, gộp tiền công vào đơn giá bảng services.
>
> Bước 1.2 – Lược đồ CSDL
> Prompt:
>   "Từ quy trình trên, đề xuất lược đồ CSDL SQLite gồm các bảng, khóa chính,
>    khóa ngoại và ràng buộc toàn vẹn cần có."
> Phản hồi AI (tóm lược):
>   - Đề xuất các bảng users, customers, vehicles, appointments, repair_orders,
>     repair_order_items, services, parts, invoices, payments, ai_results...
>   - Dùng kiểu REAL/FLOAT cho các cột giá tiền (price, unit_price, total, amount).
> Quyết định của nhóm:
>   - Chuyển toàn bộ cột tiền tệ sang INTEGER (VND nguyên) để tránh sai số dấu phẩy động.
>   - Bổ sung ràng buộc CHECK XOR (service_id IS NOT NULL) <> (part_id IS NOT NULL)
>     cho repair_order_items, quotation_items và warranties.
>
> Bước 1.3 – Trạng thái phiếu sửa chữa
> Prompt:
>   "Phiếu sửa chữa trong garage có những trạng thái nào, chuyển trạng thái theo
>    điều kiện gì để không bị nhảy cóc?"
> Phản hồi AI (tóm lược):
>   - Chuỗi tuyến tính: RECEIVED -> INSPECTING -> ESTIMATING -> REPAIRING -> COMPLETED.
> Quyết định của nhóm:
>   - Bổ sung trạng thái CANCELLED (kèm tự động hoàn trả tồn kho qua sổ cái RETURN).
>   - Cho phép quay vòng REPAIRING -> INSPECTING khi phát sinh hạng mục cần kiểm tra lại.
>   - Chặn chuyển sang COMPLETED nếu phiếu chưa có hạng mục nào.
>
> Bước 1.4 – Vị trí ứng dụng AI
> Prompt:
>   "Trong ứng dụng quản lý garage, những chức năng AI nào hợp lý và cần kiểm soát
>    ra sao để an toàn dữ liệu?"
> Phản hồi AI (tóm lược):
>   - Gợi ý 4 chức năng: (1) Tóm tắt lịch sử xe, (2) Giải thích dịch vụ cho khách,
>     (3) Sinh báo giá nháp, (4) Tự động chẩn đoán bệnh xe từ tiếng động cơ.
> Quyết định của nhóm:
>   - Giữ 3 chức năng AI01, AI02, AI03 gắn trực tiếp với dữ liệu CSDL.
>   - Loại bỏ chức năng (4) "AI tự chẩn đoán lỗi xe" vì rủi ro sai lệch kỹ thuật cao.
>   - Áp dụng cơ chế Human Review: mọi kết quả AI đều lưu trạng thái PENDING, chờ
>     nhân viên có quyền ai.review duyệt trước khi sử dụng.
> ```