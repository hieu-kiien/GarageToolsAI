# MINH CHỨNG AI REVIEW MÃ NGUỒN

Nhóm 23 — Học phần *Ứng dụng Trí tuệ Nhân tạo (AIA331)*, Mã số 80277
Tương ứng tiêu chí **KT3-09**.

> **Cách đọc tài liệu này**
> Bảng bên dưới là bản tổng hợp những gì đã review và đã sửa. Mục *Nguyên văn*
> ở cuối là chỗ dành cho đoạn mã trước và sau từng lượt review.
>
> Lưu ý: hai lượt review đầu đã dẫn tới thay đổi cấu trúc dữ liệu, nên phần
> "đoạn mã trước và sau" được mô tả bằng nội dung thay vì dán nguyên khối dài.

---

## Sáu hạng mục đã review

| # | Hạng mục | AI phát hiện | Nhóm xử lý | Kết quả |
|---|---|---|---|---|
| 1 | Bảo mật khóa API | Khóa được đọc trực tiếp trong module thay vì qua biến môi trường | Chuyển sang đọc biến môi trường, bổ sung tệp `.env.example` | Đã sửa. Không còn bí mật trong mã nguồn; `.env` nằm trong `.gitignore` |
| 2 | Quyền truy cập route | Route báo cáo không kiểm tra vai trò trước khi xử lý | Bổ sung kiểm tra vai trò ở backend cho mọi route quản trị | Đã sửa. Trả về 403 khi sai vai trò |
| 3 | Kiểm tra dữ liệu đầu vào | Biển số xe không kiểm tra định dạng và không phát hiện trùng | Thêm ràng buộc `UNIQUE` cho biển số, kiểm tra định dạng ở backend | Đã sửa. Có ca kiểm thử biên tương ứng |
| 4 | Xử lý ngoại lệ | Không bắt lỗi kết nối nhà cung cấp AI, có thể làm dừng tiến trình | Bọc thử bắt lỗi, trả thông báo thân thiện cho người dùng | Đã sửa. Ứng dụng không còn bị dừng |
| 5 | Tách prompt khỏi mã | Prompt nằm trực tiếp trong hàm gọi AI | Tách sang các tệp `config/prompts/*.txt` | Đã sửa. Đổi prompt không cần sửa logic |
| 6 | Nguồn giá báo giá | Giao diện có thể gửi giá lên backend trong yêu cầu báo giá | Backend bỏ qua giá do giao diện gửi và luôn đọc giá trong CSDL | Đã sửa. Kiểm chứng bằng ca kiểm thử TC15 |

---

## Hai phát hiện tạo ra thay đổi lớn nhất

### 4.1. Ràng buộc `service_id` và `part_id`

Bảng `repair_order_items` dùng chung cho dịch vụ và phụ tùng nên có hai khóa ngoại,
một cái có thể rỗng. Khi review lại phần ràng buộc, nhóm mới nhận ra **chưa có quy
tắc nào ngăn được trường hợp cả hai cùng rỗng hoặc cùng có giá trị**.

Hậu quả nếu bỏ qua: một hàng mục sửa chữa không xác định được là dịch vụ hay phụ
tùng, khiến cả báo cáo và báo giá nháp sai.

Đã sửa bằng ràng buộc ở mục 4.3 của báo cáo, hiện thực trong
`database/schema.sql`:

```sql
CHECK (
    (service_id IS NOT NULL AND part_id IS NULL) OR
    (service_id IS NULL     AND part_id IS NOT NULL)
)
```

Có bốn ca kiểm thử bảo vệ ràng buộc này: từ chối khi thiếu cả hai, từ chối khi có
cả hai, chấp nhận khi chỉ có dịch vụ, chấp nhận khi chỉ có phụ tùng.

### 4.2. Giá phải chốt, không được tra động

Cùng đợt review đó, nhóm phát hiện `unit_price` đang được hiểu là liên kết tra động
về bảng `services`. Nếu giữ nguyên cách hiểu đó, **một lần sửa giá dịch vụ trong
danh mục sẽ làm thay đổi cả những hóa đơn đã phát hành trước đó** — tức là lịch
sử tài chính của garage bị ghi đè bằng dữ liệu mới.

Đã sửa: `unit_price` được chốt và lưu ngay tại thời điểm thêm hạng mục. Có ca kiểm
thử đổi toàn bộ giá dịch vụ về 0 rồi xác nhận tổng hóa đơn cũ không đổi.

---

## Điểm nhóm rút ra

| Nhận xét | Chi tiết |
|---|---|
| Lỗi nguy hiểm nhất không nằm ở chỗ sai rõ ràng | Lỗi về tính toàn vẹn dữ liệu trông vẫn "chạy bình thường", chỉ lộ ra khi nghiệp vụ thật diễn ra |
| Prompt tách riêng có giá trị thật | Sau khi tách, việc đổi nội dung prompt không đòi sửa logic, giúp thử nghiệm nhanh |
| Không có lượt review nào cho kết quả "không có vấn đề gì" | Cả sáu lượt đều phát hiện điều cần sửa |

---

## Nguyên văn

> Phần này dành cho đoạn mã trước và sau, nhóm bổ sung sau khi thực hiện review.
>
> ```text
> Lượt 1 – Bảo mật khóa API
> Mã trước:
> Mã sau:
>
> Lượt 2 – Quyền truy cập route
> Mã trước:
> Mã sau:
>
> Lượt 3 – Kiểm tra dữ liệu đầu vào
> Mã trước:
> Mã sau:
>
> Lượt 4 – Xử lý ngoại lệ
> Mã trước:
> Mã sau:
>
> Lượt 5 – Tách prompt khỏi mã
> Mã trước:
> Mã sau:
>
> Lượt 6 – Nguồn giá báo giá
> Mã trước:
> Mã sau:
> ```