# KỊCH BẢN THUYẾT TRÌNH 7 PHÚT (8 SLIDE REVEAL.JS) & CẨM NANG HỎI – ĐÁP

- **Học phần:** Ứng dụng Trí tuệ Nhân tạo (AIA331) — **Mã đề tài:** 80277 — **Nhóm 23**
- **Giảng viên hướng dẫn:** TS. Nguyễn Tuấn Anh
- **Sinh viên thực hiện:** Nguyễn Đức Dũng (Trưởng nhóm) & Đồng Quốc Khánh
- **Thời lượng thuyết trình:** **Đúng 7 phút** (8 Slide trên thư viện **Reveal.js 5.1**, không chèn câu hỏi vào slide).
- **File Slide trình chiếu:** [`Slide_Thuyet_Trinh_Nhom23.html`](./Slide_Thuyet_Trinh_Nhom23.html)

---

## PHẦN 1: CÁC HIỆU ỨNG & TƯƠNG TÁC TRÊN BỘ SLIDE REVEAL.JS MỚI

Bộ slide [`Slide_Thuyet_Trinh_Nhom23.html`](./Slide_Thuyet_Trinh_Nhom23.html) đã được tích hợp trực tiếp thư viện **Reveal.js 5.1** chuẩn quốc tế + **Lucide Icons** + **Chart.js** + **Hiệu ứng nền Aurora Sáng (Light Glassmorphism)**:

1. **Chuyển hiệu ứng từng ý (Fragments) & Chuyển trang:**
   - Bấm phím mũi tên **`→`** hoặc **`Space`**: Ở **Slide 2, 3, 4**, mỗi lần bấm `→` các thẻ nội dung sẽ **trượt nhẹ lên (Fade-up)** theo đúng nhịp nói của bạn để thầy cô và các bạn dễ theo dõi.
2. **Xem toàn cảnh 8 Slide dạng lưới 3D (Overview Mode của Reveal.js):**
   - Bấm phím **`O`** (hoặc **`Esc`**) bất kỳ lúc nào để thu nhỏ toàn bộ 8 slide thành bảng tổng quan rất đẹp mắt, bấm vào slide nào sẽ bay thẳng tới slide đó.
3. **Tương tác chuyển đổi 6 Màn hình Web thật ngay tại Slide 5:**
   - Tại **Slide 5**, có 6 nút tròn (`1. Điều phối Kanban` → `6. Chặn Phân quyền 403`). Khi bấm vào, khung trình duyệt MacBook bên dưới sẽ chuyển mượt sang ảnh màn hình thật tương ứng.
   - **Bấm trực tiếp vào bất kỳ khung ảnh trình duyệt nào** (ở Slide 1, Slide 5, Slide 6) để **phóng to ảnh toàn màn hình (Lightbox)** cho thầy cô nhìn rõ từng chi tiết.
4. **Biểu đồ động (Chart.js) & Số đếm tự động (Count-up):**
   - Ở **Slide 1**, 4 ô số liệu (`21 bảng`, `16 màn hình`, `3 trợ lý AI`, `226/226`) tự động chạy hiệu ứng đếm số.
   - Ở **Slide 7**, 2 biểu đồ đo độ trễ Groq và kết quả kiểm thử tự động vẽ hiệu ứng chuyển động mượt mà.

---

## PHẦN 2: KỊCH BẢN NÓI CHI TIẾT TỪNG PHÚT (8 SLIDE — GÓI GỌN ĐÚNG 7 PHÚT)

---

### 🔹 SLIDE 1: Trang bìa — Giới thiệu Đề tài & Quy mô (0:00 – 0:45 | 45 giây)

> **Lời thoại:**
> "Em xin kính chào Thầy và Hội đồng chấm đồ án, chào các bạn sinh viên ạ. Em là đại diện của **Nhóm 23** (gồm Nguyễn Đức Dũng và Đồng Quốc Khánh). Hôm nay em xin trình bày đồ án học phần Ứng dụng Trí tuệ Nhân tạo (mã đề tài 80277): **Hệ thống Quản trị Xưởng Dịch vụ Ô tô tích hợp Trợ lý AI — GarageTools AI**.
>
> Hệ thống của nhóm quản lý khép kín toàn bộ quy trình xưởng từ đặt lịch, tiếp nhận, báo giá, sổ cái kho đến nghiệm thu, hóa đơn, bảo hành; kết hợp **3 chức năng Trợ lý AI có kiểm duyệt Human Review**. Đồ án đã hoàn thiện trọn vẹn qua 4 cột mốc từ KT1 đến Cuối kỳ với **21 bảng CSDL SQLite**, **16 màn hình React 19** kết nối **FastAPI**, và vượt qua **100% trên tổng số 226 ca kiểm thử tự động**."

---

### 🔹 SLIDE 2: Thực trạng Quản lý Xưởng & Vì sao cần "Rào chắn" cho AI? (0:45 – 1:40 | 55 giây)

*(Lưu ý thao tác: Slide này có hiệu ứng xuất hiện từng ý — vừa nói vừa bấm nhẹ phím `→`)*

> **Lời thoại:**
> "Thưa thầy cô, xuất phát từ thực tế tại các garage vừa và nhỏ, có **3 rủi ro gây thất thoát lớn nhất**:
> - *(Bấm `→`)* **Một là** lệch tồn kho và xuất âm kho khi hai nhân viên cùng lấy một phụ tùng cuối cùng, hoặc hủy phiếu nhưng quên hoàn kho.
> - *(Bấm `→`)* **Hai là** sai lệch lịch sử tài chính: nếu lưu giá kiểu tra cứu động từ danh mục, một lần đổi giá dịch vụ sẽ làm thay đổi tổng tiền của cả các hóa đơn cũ đã thu.
> - *(Bấm `→`)* **Ba là** rủi ro **ảo giác (Hallucination)** khi gọi AI tự do: AI rất dễ tự bịa phụ tùng lạ, tính sai tổng tiền hoặc chẩn đoán mò bệnh xe.
>
> Vì vậy ở giai đoạn **KT1**, khi dùng AI hỗ trợ phân tích thiết kế, nhóm xác lập nguyên tắc: **AI chỉ sinh phương án, con người kiểm chứng và quyết định**:
> - *(Bấm `→`)* Nhóm **chủ động bác bỏ gợi ý 'AI tự chẩn đoán lỗi xe'** vì rủi ro kỹ thuật cao, chỉ giữ **AI01, AI02, AI03** bám sát CSDL.
> - *(Bấm `→`)* Chuẩn hóa lược đồ bằng cách gộp tiền công vào đơn giá dịch vụ và thêm nhánh hủy phiếu tự hoàn kho.
> - *(Bấm `→`)* Giữ vững nguyên tắc vàng: **AI chỉ trình bày văn bản tư vấn ở trạng thái Chờ duyệt (`PENDING`), tuyệt đối không tự quyết định tiền.**"

---

### 🔹 SLIDE 3: Kiến trúc 4 Tầng & Phân quyền 4 Vai trò (RBAC) (1:40 – 2:35 | 55 giây)

*(Lưu ý thao tác: Nói xong 4 tầng kiến trúc ở hàng trên thì bấm `→` để hiện lần lượt 4 vai trò ở hàng dưới)*

> **Lời thoại:**
> "Về kiến trúc ở **Slide 3**, hệ thống tách biệt thành **4 tầng**:
> 1. **Giao diện Web** xây dựng bằng **React 19 + TanStack Start** (16 màn hình) kèm giao diện Jinja2 tích hợp sẵn.
> 2. **Tầng Bảo mật** băm mật khẩu bằng **Argon2id**, dùng Cookie ký HMAC kèm cột **`auth_version`** giúp thu hồi ngay lập tức mọi phiên đang mở khi đổi mật khẩu hoặc khóa tài khoản, kết hợp **CSRF Token** 2 lớp.
> 3. **Tầng Dịch vụ & AI Gateway** độc lập nhà cung cấp.
> 4. **Tầng CSDL SQLite 3 bật chế độ WAL** với 21 bảng và 37 chỉ mục.
>
> Hệ thống kiểm soát phân quyền **4 vai trò nội bộ**:
> - *(Bấm `→`)* **Quản lý (`MANAGER`)**: Toàn quyền điều hành và là vai trò duy nhất được **duyệt kết quả AI (`ai.review`)**.
> - *(Bấm `→`)* **Lễ tân (`RECEPTIONIST`)**: Tiếp nhận xe, lập báo giá, quản lý kho, chạy AI01–AI03 nhưng bị chặn quyền duyệt AI.
> - *(Bấm `→`)* **Kỹ thuật viên (`TECHNICIAN`)**: Bị **cô lập quyền thao tác theo từng phiếu** — chỉ sửa được đúng phiếu giao cho mình.
> - *(Bấm `→`)* **Thu ngân (`CASHIER`)**: Ghi nhận thanh toán, bị chặn sửa phiếu kỹ thuật và chặn chạy AI."

---

### 🔹 SLIDE 4: 4 Chốt chặn Bảo vệ Tuyệt đối Tiền tệ & Tồn kho (2:35 – 3:45 | 70 giây)

*(Lưu ý thao tác: Bấm `→` lần lượt cho 4 thẻ chốt chặn hiện ra — đây là phần kỹ thuật ăn điểm nhất)*

> **Lời thoại:**
> "Sang giai đoạn **KT2 và đợt dùng AI Review mã nguồn ở KT3**, nhóm đã xây dựng **4 chốt chặn kỹ thuật** bảo vệ tiền và tồn kho:
> - *(Bấm `→`)* **Thứ nhất — Tiền tệ nguyên và Chốt giá lịch sử:** Nhóm đã sửa lỗi AI dùng số thực `FLOAT` sang số nguyên **`INTEGER` (tính bằng đồng)** để triệt tiêu sai số làm tròn; đồng thời Backend luôn tự đọc giá từ CSDL và **chốt cứng vào cột `unit_price`** lúc thêm hạng mục. Đổi giá danh mục không bao giờ làm thay đổi hóa đơn cũ.
> - *(Bấm `→`)* **Thứ hai — Ràng buộc `CHECK XOR`:** Áp dụng trực tiếp trong SQLite trên cả 3 bảng hạng mục phiếu, báo giá và bảo hành — bắt buộc mỗi dòng **hoặc là Dịch vụ, hoặc là Phụ tùng, đúng một trong hai**, không bao giờ mơ hồ.
> - *(Bấm `→`)* **Thứ ba — Sổ cái tồn kho bất biến (`stock_transactions`):** Mọi biến động tồn kho bắt buộc đi qua Sổ cái theo 4 lý do Nhập, Xuất, Hoàn trả, Điều chỉnh, giữ bất biến **`parts.stock` luôn bằng tổng đại số `SUM(qty)` trên sổ cái**.
> - *(Bấm `→`)* **Thứ tư — Giao dịch nguyên tử `BEGIN IMMEDIATE`:** Kiểm tra điều kiện ngay trong câu lệnh `UPDATE` (`WHERE stock + ? >= 0` và `WHERE total - paid >= ?`), chặn 100% lỗi xuất âm kho hay thu tiền vượt tổng hóa đơn khi 2 người bấm cùng lúc."

---

### 🔹 SLIDE 5: Quy trình 6 Trạng thái & 16 Màn hình React 19 Thực tế (3:45 – 4:50 | 65 giây)

*(Lưu ý thao tác: Dùng chuột bấm nhanh qua các nút tròn `2. Chi tiết Phiếu`, `3. Báo giá Idempotent`, `5. Chặn Thu vượt (409)` để thầy cô thấy ngay ảnh giao diện thật)*

> **Lời thoại:**
> "Ở **Slide 5** là vòng đời 6 trạng thái của phiếu sửa chữa: từ **Đã tiếp nhận** (ghi biên bản số ODO, mức xăng, ngoại thất), sang **Đang kiểm tra**, **Đang báo giá**, **Đang sửa chữa** cho tới khi **Đã hoàn thành** (để Nghiệm thu, Lập hóa đơn, Cấp bảo hành); hoặc nhánh **Đã hủy phiếu** tự động hoàn trả phụ tùng về kho.
>
> *(Bấm qua vài nút màn hình bên dưới)*
> Ngay trên khung trình duyệt bên dưới là ảnh chụp thực tế từ 16 màn hình React 19 của hệ thống: từ Bảng điều phối Kanban, màn hình Chi tiết phiếu & Nghiệm thu, màn hình Báo giá chính thức chỉ cho phép áp dụng **đúng một lần (idempotent)**, cho tới màn hình Tài chính tự động chặn lỗi **HTTP 409** khi thu ngân nhập số tiền vượt quá số còn phải trả."

---

### 🔹 SLIDE 6: 3 Chức năng AI, Bộ lọc Chống Ảo giác & Human Review (4:50 – 5:50 | 60 giây)

> **Lời thoại:**
> "Tại **Slide 6** là trọng tâm của giai đoạn **KT3**: tích hợp 3 chức năng AI với các tệp prompt tách độc lập khỏi mã nguồn:
> - **AI01 (`history.txt`):** Tóm tắt lịch sử sửa chữa của xe theo đúng 4 mục, xe mới chưa sửa lần nào thì báo rõ chưa có lịch sử, cấm suy đoán bệnh mới.
> - **AI02 (`explain.txt`):** Giải thích dịch vụ bằng ngôn ngữ đời thường cho chủ xe; xử lý an toàn cả ca biên khi dịch vụ bị trống mô tả (`NULL`) mà không gây lỗi 500.
> - **AI03 (`quote.txt`):** Lập báo giá nháp dạng JSON. Điểm đắt giá nhất tại `ai_gateway.py` là **Bộ lọc hậu kiểm không tin lời model**: hệ thống bóc tách JSON, lọc chỉ giữ lại dòng nào khớp chính xác cả Tên, Số lượng và Đơn giá với CSDL; nếu AI cộng sai tổng tiền thì hệ thống **cưỡng bức dùng `backend_total` của Backend**; và tự động Fallback sang chế độ dự phòng `mock` nếu đứt mạng hoặc lỗi 429.
>
> Đặc biệt, mọi kết quả AI sinh ra đều lưu ở trạng thái **`PENDING` (Chờ duyệt)**. Chỉ **Quản lý (`ai.review`)** mới được bấm Duyệt hoặc Từ chối và bị khóa một chiều không cho duyệt lại lần hai."

---

### 🔹 SLIDE 7: Thực nghiệm Mô hình Thật (Groq) & Kiểm thử Cuối kỳ (5:50 – 6:30 | 40 giây)

> **Lời thoại:**
> "Ở **Slide 7 (Giai đoạn Cuối kỳ)** là kết quả đo lường thực nghiệm và kiểm thử:
> - Biểu đồ bên trái là độ trễ đo thực tế trên mô hình thật **`openai/gpt-oss-120b` qua Groq Cloud**: trung bình chỉ từ **2.46 giây đến 3.99 giây**, nhanh hơn gấp 3 lần so với trần yêu cầu Cuối kỳ là dưới 10 giây.
> - Biểu đồ bên phải là kết quả 4 tầng kiểm thử đạt **100% PASS**: gồm **226/226 ca tự động Backend**, **31/31 ca Smoke**, **32/32 ca E2E xuyên suốt** (đối soát sổ cái kho sau toàn bộ quy trình lệch bằng 0), cùng **35/35 ca UAT** và đóng gói hoàn chỉnh bằng Docker kèm GitHub Actions CI."

---

### 🔹 SLIDE 8: Giới hạn Hiện tại, Hướng Phát triển & Lời Cảm ơn (6:30 – 7:00 | 30 giây)

> **Lời thoại:**
> "Cuối cùng ở **Slide 8**, nhóm xin nhìn nhận khách quan 3 giới hạn hiện tại và hướng phát triển:
> - **Về giới hạn hiện tại:** (1) Kết quả AI03 sau khi duyệt đang dừng ở văn bản tư vấn trong `ai_results` chứ chưa tự sinh bản ghi sang bảng `quotations` để tách bạch an toàn dữ liệu AI và chứng từ tài chính; (2) Kho hiện trừ trực tiếp khi áp dụng báo giá chứ chưa tách bước *'Giữ kho tạm thời'* lúc báo giá đang chờ khách duyệt; và (3) SQLite WAL khóa ghi mức toàn file nên tối ưu cho 1 xưởng độc lập (5–30 người).
> - **Hướng nâng cấp tiếp theo** là chuyển lên **PostgreSQL** cho chuỗi đa chi nhánh, bổ sung hàng đợi bất đồng bộ cho AI, kết nối thiết bị đọc lỗi **OBD-II**, **Vision AI** nhận diện vết trầy xước xe và thanh toán **VietQR**.
>
> Phần trình bày 7 phút của Nhóm 23 đến đây là kết thúc. Em xin trân trọng cảm ơn Thầy/Cô và các bạn đã lắng nghe, và xin phép được lắng nghe câu hỏi từ Hội đồng ạ!"

---

## PHẦN 3: CẨM NANG 12 CÂU HỎI PHẢN BIỆN DÀNH RIÊNG CHO BẠN (ĐỌC TRÊN ĐIỆN THOẠI/GIẤY KHI HỎI ĐÁP)

*(Phần này chỉ nằm trong tài liệu này để bạn ôn trước khi lên bảng, hoàn toàn không xuất hiện trên Slide)*

1. **Tại sao nhóm lại loại bỏ chức năng "AI tự chẩn đoán lỗi xe"?**
   - **Trả lời:** Ở giai đoạn KT1, công cụ AI có đề xuất tính năng này nhưng nhóm **chủ động bác bỏ** vì cùng một triệu chứng (như *động cơ rung giật*) có hàng chục nguyên nhân cơ khí/điện tử cần đo kiểm thực tế bằng máy OBD-II tại cầu nâng. Nếu để LLM tự phán đoán từ vài dòng chữ sẽ vi phạm nguyên tắc *"Chỉ sử dụng dữ liệu có thật trong CSDL"* và gây rủi ro kỹ thuật cao.
2. **Làm sao đảm bảo AI không tự bịa giá tiền hoặc tự thêm phụ tùng vào phiếu sửa chữa (AI03)?**
   - **Trả lời:** Có **3 lớp khóa** trong `app/ai_gateway.py`: (1) Hàm `bao_gia_nhap()` chỉ `SELECT`, tuyệt đối không `INSERT`/`UPDATE` vào bảng hạng mục hay hóa đơn; (2) Mảng `items` do AI trả về bị lọc đối chiếu từng dòng: phải khớp 100% Tên, Số lượng và Đơn giá với CSDL mới được giữ lại; (3) Tổng tiền chính thức `backend_total` do SQL tự tính, nếu AI trả `total` khác thì hệ thống ghi cảnh báo và **ép dùng `backend_total`**.
3. **Nếu đang chạy thật mà mất mạng, quá thời gian chờ (Timeout) hoặc API Groq báo lỗi 429 (hết hạn mức) thì sao?**
   - **Trả lời:** Trong `ai_gateway.py`, hàm `goi()` bắt toàn bộ ngoại lệ `TimeoutException`, HTTP `429`, `500` hoặc JSON vỡ và tự động chuyển sang chế độ dự phòng **`_goi_mock()`** dựng kết quả chuẩn từ CSDL để quy trình tiếp nhận của xưởng không bao giờ bị lỗi 500. (Đã có 15 ca kiểm thử trong `TestAiGateway`).
4. **Nếu một dịch vụ bị bỏ trống mô tả (`description = NULL`), khi chạy AI02 (Giải thích dịch vụ) có bị lỗi không?**
   - **Trả lời:** Không lỗi ạ. Khi `description` là `NULL`, hệ thống bắt buộc phần 1 trả về đúng câu quy định: *"1. Dịch vụ là gì: Danh mục chưa có mô tả cho dịch vụ này"* (được kiểm chứng tự động bởi ca test `test_ai02_dich_vu_thieu_mo_ta_van_tao_duoc_ket_qua`).
5. **Cơ chế Human Review kiểm soát ở tầng CSDL và phân quyền như thế nào?**
   - **Trả lời:** Mọi kết quả AI sinh ra đều lưu vào `ai_results` với `review_status = 'PENDING'`. Ràng buộc `CHECK` của bảng bắt buộc khi chuyển sang `APPROVED`/`REJECTED` phải có đủ `reviewed_by` và `reviewed_at`. Chỉ vai trò **`MANAGER`** mới có quyền `ai.review` (Lễ tân/KTV gọi API bị chặn 403), và câu lệnh `UPDATE ... WHERE review_status = 'PENDING'` chặn tuyệt đối việc duyệt lại lần 2.
6. **Giải thích cơ chế chống Race Condition khi 2 người cùng lấy 1 phụ tùng cuối cùng hoặc thu tiền cùng lúc?**
   - **Trả lời:** Nhóm không dùng `if stock >= qty` trong Python rồi mới `UPDATE` (vì sẽ bị lỗi tranh chấp TOCTOU). Thay vào đó, nhóm mở transaction **`BEGIN IMMEDIATE`** và gộp điều kiện kiểm tra ngay trong câu lệnh SQL nguyên tử: `UPDATE parts SET stock = stock + ? WHERE id = ? AND stock + ? >= 0` (và `WHERE total - paid >= ?` với hóa đơn). Nếu `rowcount != 1`, giao dịch tự rollback và báo lỗi 409/422 ngay.
7. **Nếu bấm nút "Áp dụng báo giá vào phiếu" 2 lần liên tiếp (double-click) thì kho có bị trừ 2 lần không?**
   - **Trả lời:** Tuyệt đối không. Bảng `quotations` có cột `applied_at`. Hàm `ap_dung_vao_phieu()` kiểm tra trong `BEGIN IMMEDIATE`: nếu `applied_at IS NOT NULL` thì từ chối ngay với mã **HTTP 409 Conflict**. Kịch bản `scripts/e2e.ps1` đã bắn lặp 2 lần liên tiếp và chứng minh kho chỉ trừ đúng 1 lần, đối soát `/api/stock/audit` lệch bằng 0.
8. **Tại sao phải có ràng buộc `CHECK XOR` trên bảng hạng mục (`repair_order_items`)?**
   - **Trả lời:** Đây là phát hiện quan trọng nhất của nhóm trong đợt **AI Review mã nguồn (KT3-09)**. Vì bảng hạng mục dùng chung cho cả dịch vụ (`service_id`) và phụ tùng (`part_id`), nếu không có `CHECK ((service_id IS NOT NULL AND part_id IS NULL) OR (service_id IS NULL AND part_id IS NOT NULL))`, dữ liệu có thể lọt dòng cả hai cùng rỗng hoặc cả hai cùng có giá trị, làm sai lệch báo cáo doanh thu.
9. **Khi đổi giá dịch vụ/phụ tùng trong Danh mục (`catalog`), các hóa đơn cũ đã phát hành có bị nhảy số không?**
   - **Trả lời:** Không bao giờ thay đổi. Tại thời điểm thêm hạng mục vào phiếu hoặc báo giá, đơn giá hiện hành được sao chép và **chốt cứng vào cột `unit_price`**. Tổng phiếu và hóa đơn luôn tính trên `unit_price` đã chốt (có ca kiểm thử đổi toàn bộ giá danh mục về 0đ và xác nhận hóa đơn cũ không đổi).
10. **Khi nhân viên bị khóa tài khoản hoặc bị đổi mật khẩu, phiên đăng nhập đang mở trên máy họ có còn tác dụng không?**
    - **Trả lời:** Mất hiệu lực ngay lập tức ở request kế tiếp nhờ cột **`auth_version`** trong bảng `users`. Mỗi khi đổi mật khẩu hoặc khóa tài khoản, `auth_version` tăng lên 1, làm chữ ký phiên cũ trong cookie không còn khớp.
11. **Trong quá trình dùng AI lập trình (KT2), lỗi nguy hiểm nhất do AI sinh ra mà nhóm bắt được là gì?**
    - **Trả lời:** Có 2 lỗi liên quan đến tiền: (1) AI cho phép form phía client gửi `unit_price` lên server (người dùng có thể sửa HTML thành giá 0đ) — nhóm sửa lại để Backend luôn tự tra giá từ CSDL; (2) AI dùng số thực `FLOAT` cho tiền tệ gây sai số làm tròn — nhóm chuyển toàn bộ sang số nguyên `INTEGER`.
12. **Nếu thầy cô hỏi: "Sao trong file PDF báo cáo có nhắc tới AI04 / bảng đặt giữ kho riêng, mà trên Slide và Code thực tế lại là 3 chức năng AI01–AI03 và sổ cái `stock_transactions`?"**
    - **Trả lời:** *"Dạ thưa thầy, trong báo cáo lý thuyết nhóm có phác thảo cả kiến trúc mở rộng định hướng. Khi hiện thực hóa mã nguồn chính thức và nghiệm thu theo đúng **40 tiêu chí bắt buộc của học phần AIA331 (KT1 → KT3 → Cuối kỳ)**, nhóm đã chuẩn hóa vào **3 chức năng AI01–AI03** và **Sổ cái tồn kho nguyên tử (`stock_transactions`)** để đảm bảo 100% tính tất định, không có tính năng thừa ngoài kiểm soát và vượt qua toàn bộ **226/226 ca kiểm thử tự động** ạ!"*
