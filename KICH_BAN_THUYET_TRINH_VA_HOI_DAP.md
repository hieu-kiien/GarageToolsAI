# KỊCH BẢN TRÌNH BÀY DỰ ÁN HỌC PHẦN & HƯỚNG DẪN TRẢ LỜI CÂU HỎI
## Đề tài: Hệ thống Quản lý Xưởng Dịch vụ Ô tô & Trợ lý AI (GarageTools AI)
- **Học phần:** Ứng dụng Trí tuệ Nhân tạo (AIA331) — Mã đề tài: **80277**
- **Giảng viên hướng dẫn:** TS. Nguyễn Tuấn Anh
- **Nhóm thực hiện:** Nhóm 23 (Nguyễn Đức Dũng · Đồng Quốc Khánh)
- **Tài liệu đi kèm:**
  - Slide trình bày: `Slide_Thuyet_Trinh_Nhom23.html` (12 Slide thoáng đãng, phông chữ **Be Vietnam Pro**, có **Logo trường ICTU**, mỗi slide giao diện chỉ hiển thị 1 ảnh lớn sắc nét bên phải + 3 ý ngắn bên trái)
  - Báo cáo chi tiết: `Báo cáo.pdf`

---

## PHẦN 1: CẤU TRÚC & NHỊP ĐIỆU BÀI TRÌNH BÀY 12 SLIDE (10 – 12 PHÚT)

| Slide | Nền Slide | Nội dung chính | Người trình bày gợi ý | Thời lượng |
| :--- | :---: | :--- | :--- | :---: |
| **Slide 01** | **Tối (Navy)** | Trang bìa có Logo ICTU, tên đề tài, thông tin nhóm & ảnh lớn màn hình Tổng quan | Nguyễn Đức Dũng | 1 phút |
| **Slide 02** | Sáng | 3 bài toán thực tế tại xưởng sửa chữa ô tô & nguyên tắc kiểm soát AI | Nguyễn Đức Dũng | 1 phút |
| **Slide 03** | Sáng | Phân quyền 4 vai trò nhân sự & kiến trúc hệ thống 4 tầng | Nguyễn Đức Dũng | 1 phút |
| **Slide 04** | Sáng | Luồng vận hành Phiếu sửa chữa 6 trạng thái & màn hình Quản lý phiếu | Đồng Quốc Khánh | 1 phút |
| **Slide 05** | Sáng | Chi tiết Phiếu sửa chữa, chốt cứng đơn giá lịch sử & Biên bản tiếp nhận | Đồng Quốc Khánh | 1 phút |
| **Slide 06** | Sáng | Sổ cái Kho phụ tùng đối soát thời gian thực (`Lệch sổ = 0`) & Báo giá | Đồng Quốc Khánh | 1 phút |
| **Slide 07** | Sáng | Bảo vệ toàn vẹn Tiền tệ, Công nợ & minh chứng chặn thu vượt nợ | Đồng Quốc Khánh | 1 phút |
| **Slide 08** | **Tối (Navy)** | **Trọng tâm AIA331:** Thiết kế 3 chức năng Trợ lý AI & Bộ lọc 3 bước chống bịa giá | Nguyễn Đức Dũng | 1,5 phút |
| **Slide 09** | Sáng | Giao diện Trung tâm AI — Cơ chế Hàng chờ ở trạng thái **“Chờ duyệt”** | Nguyễn Đức Dũng | 1 phút |
| **Slide 10** | Sáng | Giao diện Phê duyệt kết quả AI — Chuyển sang **“Đã duyệt”** kèm tên người duyệt | Nguyễn Đức Dũng | 1 phút |
| **Slide 11** | Sáng | Kết quả đo độ trễ thực tế trên Groq API (`< 4 giây`) & kiểm thử tự động (`231/231`) | Nguyễn Đức Dũng | 1 phút |
| **Slide 12** | **Tối (Navy)** | Tổng kết kết quả đạt được, giới hạn hiện tại, hướng phát triển & Cảm ơn | Nguyễn Đức Dũng | 1 phút |

---

## PHẦN 2: LỜI THOẠI CHI TIẾT THEO TỪNG SLIDE

### SLIDE 01: Trang bìa Dự án Học phần
> *"Em chào Thầy và các bạn. Hôm nay Nhóm 23 chúng em gồm Nguyễn Đức Dũng và Đồng Quốc Khánh xin trình bày dự án kết thúc học phần Ứng dụng Trí tuệ Nhân tạo với đề tài: **Hệ thống Quản lý Xưởng Dịch vụ Ô tô & Trợ lý AI (GarageTools AI)**.*
>
> *Mục tiêu của nhóm là xây dựng một phần mềm web hoàn chỉnh giúp các xưởng sửa chữa ô tô vừa và nhỏ quản lý khép kín từ khâu nhận xe, báo giá, xuất kho phụ tùng đến hóa đơn; đồng thời ứng dụng Trợ lý AI để hỗ trợ tóm tắt lịch sử xe, giải thích dịch vụ và gợi ý báo giá nháp một cách an toàn.*
>
> *Bên phải màn hình là giao diện Bảng điều khiển Tổng quan thực tế của hệ thống."*

---

### SLIDE 02: 3 Bài toán Thực tế tại Xưởng Dịch vụ Ô tô
> *"Qua khảo sát thực tế, nhóm tập trung giải quyết 3 bài toán chính:*
> 1. ***Một là lệch tồn kho và nhảy giá cũ:** Khi quản lý rời rạc, việc hủy phiếu giữa chừng rất dễ quên hoàn trả phụ tùng về kho; hoặc khi xưởng đổi bảng giá mới thì các phiếu sửa chữa cũ lại bị nhảy tổng tiền.*
> 2. ***Hai là tốn thời gian tra cứu và tư vấn:** Cố vấn dịch vụ mất nhiều thời gian đọc lại lịch sử sửa chữa dài của xe và giải thích chi phí kỹ thuật cho khách hàng.*
> 3. ***Ba là rủi ro ảo giác khi dùng AI:** Nếu dùng mô hình ngôn ngữ lớn tự do mà không có rào chắn, AI rất dễ tự bịa ra tên phụ tùng ngoài danh mục hoặc tính nhầm tiền.*
>
> *Từ đó, nguyên tắc cốt lõi của nhóm là: **Cơ sở dữ liệu quyết định tuyệt đối tiền tệ và tồn kho — Trợ lý AI chỉ tư vấn nháp và bắt buộc phải qua bước con người kiểm duyệt.**"*

---

### SLIDE 03: Phân quyền 4 Vai trò Nhân sự & Kiến trúc Hệ thống
> *"Ở Slide 03, hệ thống được phân quyền theo đúng 4 vị trí công việc tại xưởng:*
> - ***Quản lý xưởng:** Quản trị danh mục, lập hóa đơn, điều chỉnh kho và là người phê duyệt kết quả AI.*
> - ***Lễ tân / Cố vấn:** Tiếp nhận khách 1-chạm từ lịch hẹn, chạy AI01 tóm tắt lịch sử xe ngay trước khi lập phiếu, điều phối trạng thái, lập báo giá nháp và lập hóa đơn khi phiếu đã hoàn thành.*
> - ***Kỹ thuật viên:** Được cô lập phạm vi dữ liệu hoàn toàn trên cả Tổng quan, Lịch sử và Phiếu sửa chữa — mỗi kỹ thuật viên chỉ nhìn thấy, cập nhật tiến độ, sửa ghi chú kỹ thuật và chạy AI03 trên đúng các phiếu được phân công cho mình.*
> - ***Thu ngân:** Phụ trách tra cứu hóa đơn, đối soát công nợ và ghi nhận thanh toán từng phần hoặc toàn bộ.*
>
> *Bên dưới là kiến trúc 4 tầng độc lập từ giao diện React 19 đến tầng bảo mật, xử lý nghiệp vụ và cơ sở dữ liệu 21 bảng."*

---

### SLIDE 04: Luồng Vận hành Phiếu sửa chữa 6 Trạng thái
> *"Sang Slide 04, em xin trình bày luồng vận hành của một phiếu sửa chữa qua 6 trạng thái: **Tiếp nhận → Kiểm tra → Báo giá → Đang sửa → Hoàn thành**, cùng nhánh rẽ **Đã hủy**.*
>
> *Hệ thống kiểm soát chặt 2 điểm:*
> - *Thứ nhất, bảng điều phối Kanban được thiết kế chịu tải cao (30–50+ xe/ngày) với thanh lọc theo Kỹ thuật viên, cuộn độc lập từng cột, chế độ thẻ thu gọn, hỗ trợ kéo tiến/lùi hợp lệ và chỉ cho chuyển sang **Hoàn thành** khi đã có ít nhất một hạng mục.*
> - *Thứ hai, khi hủy một phiếu đã xuất phụ tùng nhưng chưa thu tiền, hệ thống sẽ **tự động hoàn trả 100% số lượng phụ tùng đó về kho**.*
>
> *Hình bên phải là giao diện Quản lý và lọc phiếu sửa chữa theo từng trạng thái."*

---

### SLIDE 05: Chi tiết Phiếu sửa chữa & Biên bản Tiếp nhận Xe
> *"Trên Slide 05 là màn hình đi sâu vào **Chi tiết của một Phiếu sửa chữa**:*
> - *Ngay khi nhân viên thêm dịch vụ hoặc phụ tùng vào phiếu, đơn giá hiện tại được **chốt cứng vào dòng hạng mục**, giúp hóa đơn lịch sử không bị nhảy giá khi xưởng cập nhật bảng giá mới.*
> - *Kèm theo phiếu là **Biên bản tiếp nhận xe** ghi nhận số ODO, mức nhiên liệu, tình trạng thân vỏ và tư trang khách gửi, cùng nhật ký lưu vết mọi lần chuyển trạng thái."*

---

### SLIDE 06: Sổ cái Kho phụ tùng Đối soát Thời gian thực
> *"Ở Slide 06 là màn hình **Kho phụ tùng và Sổ cái giao dịch**:*
> - *Mọi biến động từ Nhập kho (+), Xuất cho phiếu sửa chữa (-) đến Hoàn trả khi hủy phiếu (+) đều bắt buộc sinh chứng từ trong sổ cái. Nhờ đó số lượng tồn kho hiện tại luôn khớp tuyệt đối với tổng lũy kế sổ cái, hiển thị chỉ số **Lệch sổ bằng 0** ngay trên màn hình.*
> - *Đồng thời, các báo giá sau khi khách đồng ý và nạp vào phiếu sửa chữa sẽ tự khóa sang trạng thái **Đã áp dụng** để ngăn nhân viên bấm nhầm lần hai gây trừ kho kép."*

---

### SLIDE 07: Bảo vệ Toàn vẹn Tiền tệ, Công nợ & Phân quyền
> *"Slide 07 minh họa cơ chế bảo vệ tiền tệ và công nợ của hệ thống:*
> - *Toàn bộ tiền tệ được lưu bằng **số nguyên VNĐ** để không xảy ra sai số làm tròn.*
> - *Khi thu ngân ghi nhận thanh toán, hệ thống khóa giao dịch và kiểm tra công nợ tức thời. Như trên màn hình thực tế bên phải: khi số tiền còn phải thu là **6.100.000 đồng** mà nhập số tiền lớn hơn, hệ thống lập tức chặn lại và báo lỗi rõ ràng."*

---

### SLIDE 08: Trọng tâm Học phần AIA331 — 3 Chức năng Trợ lý AI & Bộ lọc Chống bịa giá
> *"Sang phần trọng tâm của học phần Ứng dụng AI ở Slide 08, bám sát đặc tả Đề tài 80277 (AI chỉ giải thích và tổng hợp dựa trên dữ liệu sửa chữa được cung cấp, tuyệt đối không tự chẩn đoán lỗi xe), nhóm thiết kế 3 chức năng Trợ lý AI:*
> - ***AI01 – Tóm tắt lịch sử xe:** Tổng hợp nhanh các lần sửa trước, trạng thái phiếu, hạng mục đã làm và ghi chú kỹ thuật thành 4 mục chuẩn, đồng thời tự động ẩn danh tên chủ xe trước khi gửi sang LLM.*
> - ***AI02 – Giải thích dịch vụ cho khách:** Diễn giải tên dịch vụ, đơn giá niêm yết và mô tả kỹ thuật trong danh mục thành 3 mục tư vấn dễ hiểu cho khách hàng.*
> - ***AI03 – Sinh báo giá nháp từ dịch vụ và phụ tùng đã chọn:** Để chặn triệt để hiện tượng AI bịa giá hoặc lặp dòng, nhóm xây dựng **Bộ lọc hậu xử lý 3 bước**:*
>   - ***Bước 1:** Đối chiếu từng dòng JSON của AI với hạng mục thực tế trên phiếu, loại bỏ mọi mục lạ hoặc dòng bị lặp lại nhiều lần.*
>   - ***Bước 2:** Chỉ chấp nhận đúng số lượng và đơn giá đã chốt trong CSDL, đồng thời gắn nhãn rõ ghi chú tham khảo của AI.*
>   - ***Bước 3:** Bỏ qua tổng tiền do AI tự cộng nếu lệch và luôn giữ tổng tiền số nguyên chính thức do Backend tính."*

---

### SLIDE 09: Trung tâm AI — Cơ chế Hàng chờ “Chờ duyệt”
> *"Slide 09 là giao diện **Trung tâm AI** khi nhân viên vừa bấm chạy một chức năng AI:*
> - *Kết quả sinh ra không bao giờ tự ý ghi đè vào phiếu sửa chữa mà được lưu vào **Hàng chờ duyệt kết quả** với nhãn màu vàng **Chờ duyệt**.*
> - *Trên mỗi thẻ kết quả đều hiển thị minh bạch nhà cung cấp mô hình, thời gian xử lý và hai nút thao tác **Duyệt / Từ chối**."*

---

### SLIDE 10: Phê duyệt Kết quả AI & Lưu vết Trách nhiệm
> *"Tiếp nối ở Slide 10 là màn hình sau khi **Quản lý xưởng** đã kiểm tra và bấm phê duyệt:*
> - *Lễ tân và Kỹ thuật viên được chạy AI để hỗ trợ công việc, nhưng chỉ Quản lý mới có thẩm quyền phê duyệt.*
> - *Sau khi bấm duyệt, thẻ kết quả chuyển sang nhãn xanh **Đã duyệt** và ghi rõ tên người chịu trách nhiệm: **'Duyệt bởi Trần Thu Hà'**."*

---

### SLIDE 11: Kết quả Đo kiểm Độ trễ AI & Kiểm thử Toàn diện
> *"Ở Slide 11 là các con số đo kiểm thực nghiệm của dự án:*
> - *Khi gọi mô hình ngôn ngữ lớn thật qua dịch vụ **Groq API** (sử dụng gói miễn phí **0 VNĐ**), thời gian phản hồi thực tế chỉ từ **2,46 giây đến 3,99 giây** (AI01: 2,46s; AI03: 2,98s; AI02: 3,99s), nhanh hơn rất nhiều so với ngưỡng mục tiêu 10 giây. Khi mất mạng, chế độ dự phòng nội bộ phản hồi tức thì trong 1 mili-giây.*
> - *Về chất lượng phần mềm, hệ thống đã vượt qua **231 trên 231 ca kiểm thử tự động**, cùng đầy đủ các kịch bản kiểm thử biên và luồng nghiệp vụ khép kín."*

---

### SLIDE 12: Tổng kết Dự án, Giới hạn & Hướng Phát triển
> *"Cuối cùng ở Slide 12, nhóm xin tổng kết lại kết quả đạt được cùng các giới hạn hiện tại:*
> - *Hệ thống đã hoàn thiện 7 phân hệ khép kín với 16 màn hình, đảm bảo toàn vẹn tiền tệ – tồn kho và tích hợp 3 trợ lý AI an toàn.*
> - *Về giới hạn trong phạm vi học phần: hiện tại nội dung tư vấn chưa tự động đẩy qua tin nhắn Zalo/SMS, và AI mới xử lý văn bản chứ chưa phân tích hình ảnh vết xước xe.*
> - *Hướng phát triển tiếp theo của nhóm là tích hợp AI đa phương thức nhận diện ảnh chụp thân vỏ xe lúc tiếp nhận, kết nối thông báo tự động qua Zalo OA và mở rộng cho mô hình chuỗi nhiều chi nhánh.*
>
> *Phần trình bày của Nhóm 23 đến đây là kết thúc. Chúng em xin chân thành cảm ơn Thầy và các bạn đã lắng nghe ạ!"*

---

## PHẦN 3: CÂU HỎI THƯỜNG GẶP KHI TRÌNH BÀY DỰ ÁN HỌC PHẦN

1. **Hỏi: AI trong bài là gọi API thật hay dữ liệu viết sẵn? Dùng API nào để không tốn tiền?**
   - **Đáp:** Gọi API mô hình ngôn ngữ lớn thật 100%, hỗ trợ **Groq**, **Google Gemini**, **OpenRouter** và **OpenAI**. Nhóm dùng gói **Free Tier (0 VNĐ)** từ `console.groq.com` và `aistudio.google.com` với độ trễ dưới 4 giây, đồng thời có cơ chế dự phòng nội bộ khi mất mạng.
2. **Hỏi: Làm sao chặn việc AI báo sai giá phụ tùng?**
   - **Đáp:** Kết quả của AI03 đi qua bộ lọc đối chiếu trực tiếp với bảng danh mục trong CSDL: mục nào không khớp tên sẽ bị loại bỏ, mục nào khớp sẽ bị ghi đè lại bằng đúng đơn giá niêm yết trong CSDL rồi tính lại tổng tiền bằng code Python.
3. **Hỏi: Khi xưởng tăng giá phụ tùng trong danh mục thì phiếu cũ có bị thay đổi tổng tiền không?**
   - **Đáp:** Không, vì đơn giá đã được sao chép và khóa cứng vào dòng hạng mục ngay tại thời điểm thêm vào phiếu sửa chữa.
4. **Hỏi: Hủy phiếu sửa chữa đã lấy phụ tùng ra khỏi kho thì sao?**
   - **Đáp:** Nếu phiếu đã thu tiền thì chặn không cho hủy; nếu chưa thu tiền thì hệ thống tự động cộng trả lại 100% phụ tùng về kho và ghi dòng hoàn trả (`RETURN`) vào sổ cái.
