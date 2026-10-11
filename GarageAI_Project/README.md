# GarageTools AI

Hệ thống quản lý garage sửa chữa ô tô có tích hợp AI — Học phần *Ứng dụng Trí tuệ
Nhân tạo (AIA331)*, Mã số 80277, Nhóm 23.

> **Tình trạng hiện tại:** ứng dụng chạy được đầy đủ: đăng nhập, phân quyền bốn
> vai trò, CRUD nghiệp vụ, tìm kiếm/lọc/sắp xếp, phiếu sửa chữa, hóa đơn và
> thanh toán, báo cáo, ba chức năng AI kèm Human Review. Backend đã viết lại theo
> cấu trúc tầng (core / services / routes), có CSRF, giới hạn tân suất, phân trang
> và kiểm thử đầu vào. Kiểm thử tự động đạt **102/102**. Giao diện đang được
> thiết kế lại — hợp đồng ngữ cảnh cho `templates/` nằm ở mục 7.

---

## 1. Yêu cầu môi trường

| Thành phần | Yêu cầu |
|---|---|
| Python | 3.10 trở lên |
| Cơ sở dữ liệu | SQLite (tích hợp sẵn trong Python, không cần cài thêm) |
| Trình duyệt | Bản mới của Chrome, Edge hoặc Firefox |
| Mạng | Không bắt buộc nếu dùng `AI_PROVIDER=mock` |

Docker là tuỳ chọn, dùng khi muốn chạy theo kiểu container.

## 2. Cài đặt

```bash
git clone <địa-chỉ-kho-mã-nguồn>
cd GarageAI_Project

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

## 3. Tạo cơ sở dữ liệu

```bash
python database/init_db.py
```

Lệnh này đọc `database/schema.sql` rồi `database/seed_data.sql`, tạo ra tệp
`garage.db` ở thư mục gốc với 16 bảng, 29 chỉ mục và 171 dòng dữ liệu mẫu.

Kiểm tra toàn bộ kiểm thử:

```bash
python tests/run_all.py
```

Kết quả mong đợi: **102/102 đạt**, tự sinh lại `TEST_REPORT.md`.

## 4. Cấu hình biến môi trường

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

Mở `.env` và điền giá trị thật:

- `SECRET_KEY` — bắt buộc đổi khi triển khai thật.
  Sinh bằng: `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- `OPENAI_API_KEY` — chỉ điền khi dùng nhà cung cấp AI thật.

> Tệp `.env` đã nằm trong `.gitignore`. **Không bao giờ** commit tệp này.

## 5. Chạy ứng dụng

```bash
python -m uvicorn app.main:app --reload
```

Mở trình duyệt tại <http://127.0.0.1:8000>

## 6. Tài khoản demo

| Vai trò | Tên đăng nhập | Mật khẩu |
|---|---|---|
| Quản lý | `quan_ly` | `Garage@2026` |
| Lễ tân | `le_tan` | `Garage@2026` |
| Kỹ thuật viên | `ky_thuat_vien` | `Garage@2026` |
| Thu ngân | `thu_ngan` | `Garage@2026` |

Mật khẩu được lưu dạng băm **Argon2id** (thư viện `argon2-cffi`). Nếu môi trường
không cài được thư viện này, ứng dụng tự chuyển sang PBKDF2-SHA256 với 200.000
vòng lặp để không chết, và mỗi tài khoản vẫn có một muối khác nhau.

Đổi mật khẩu hoặc khoá tài khoản sẽ làm mất hiệu lực mọi phiên đang đăng nhập
nhờ cột `auth_version`.

> Đây là tài khoản dùng cho học tập và demo. Khi triển khai thật phải đổi toàn bộ
> mật khẩu và tạo tài khoản riêng cho từng nhân viên.

## 7. Cấu trúc dự án

```
GarageAI_Project/
├── app/                    # mã ứng dụng FastAPI
│   ├── main.py             # create_app(): middleware, ngoại lệ, gắn router
│   ├── models.py           # Pydantic v2: mọi đối tượng đầu vào/ra
│   ├── crud.py             # tầng truy cập: tham số hoá, whitelist, phân trang
│   ├── ai_gateway.py       # AI Gateway: mock và OpenAI, có fallback
│   ├── core/               # nền tảng chung
│   │   ├── config.py       # đọc biến môi trường, fail-fast khi production
│   │   ├── db.py           # kết nối, BEGIN IMMEDIATE, busy_timeout
│   │   ├── security.py     # băm mật khẩu, phiên, CSRF, Origin
│   │   ├── ratelimit.py    # giới hạn tân suất theo cửa sổ trượt
│   │   ├── flash.py        # thông báo một lần qua cookie có ký
│   │   ├── pagination.py   # trang, giới hạn LIMIT, đường dẫn trang
│   │   ├── errors.py       # AppError và các loại con theo mã HTTP
│   │   ├── money.py        # định dạng tiền, ngày theo giờ Việt Nam
│   │   └── logging.py      # nhật ký có mã yêu cầu
│   ├── services/           # nghiệp vụ (không biết HTTP)
│   │   ├── auth.py         # đăng nhập, phiên, kiểm tra quyền
│   │   ├── security_matrix.py  # ma trận vai trò - quyền
│   │   ├── orders.py       # phiếu sửa chữa, hạng mục, tồn kho
│   │   ├── billing.py      # hóa đơn, thanh toán
│   │   ├── parties.py      # khách hàng, xe, lịch hẹn
│   │   ├── catalog.py      # dịch vụ, phụ tùng, cửa hàng
│   │   ├── ai.py           # gọi AI, lưu kết quả, duyệt
│   │   └── reports.py      # dashboard và báo cáo
│   ├── routes/             # HTTP (chỉ kiểm quyền, gọi dịch vụ, trả trang)
│   ├── templates/          # giao diện Jinja2
│   └── static/             # CSS
├── config/prompts/         # system, history, explain, quote
├── database/
│   ├── schema.sql          # 16 bảng kèm ràng buộc và chỉ mục
│   ├── seed_data.sql       # dữ liệu mẫu
│   ├── generate_seed.py    # sinh lại seed_data.sql
│   └── init_db.py          # tạo garage.db
├── docs/
│   ├── diagrams_final/     # 16 sơ đồ PNG
│   ├── chup_man_hinh.py    # chụp ảnh từ ứng dụng đang chạy
│   └── BANG_ANH.md         # bảng ảnh chụp
├── screenshots/            # ảnh màn hình thật
├── tests/
│   ├── test_schema_constraints.py   # 37 ca ràng buộc CSDL
│   ├── test_backup_restore.py        # 6 ca sao lưu/khôi phục
│   ├── test_backend.py               # 59 ca ứng dụng web
│   └── run_all.py                   # chạy tất cả, sinh TEST_REPORT.md
├── garage.db
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

### Hợp đồng ngữ cảnh cho giao diện

Mọi trang đi qua `app/routes/__init__.py: render()`, tức là template luôn có sẵn:

| Biến | Ý nghĩa |
|---|---|
| `user` | Người đang đăng nhập, `None` nếu chưa đăng nhập |
| `csrf_token` | Bắt buộc đặt trong mọi `<form method="post">` dưới tên `csrf_token` |
| `quyen['...']` | Bảng quyền theo vai trò, dùng ẩn/hiện nút |
| `flash.loi` / `flash.thong_bao` | Thông báo tự xoá sau một lần hiển thị |
| `loi` | Lỗi theo từng ô form: `{truong: [thong_diep]}` |
| `dong` / `tong_so_ban_ghi` / `trang` / `tong_trang` | Dữ liệu + phân trang |
| `duong_dan_trang`, `format_tien`, `format_ngay`, `ten_trang_thai`, `vai_tro_ten` | Hàm định dạng |

Quy tắc: mọi thao tác ghi dữ liệu là **POST kèm mã CSRF**; không có đường dẫn
GET nào xoá hoặc sửa dữ liệu. Danh sách đều nhận tham số `q` (tìm kiếm),
`trang` và `moi_trang` (phân trang).

## 8. Ba chức năng AI

| Mã | Chức năng | File prompt | Biến đầu vào |
|---|---|---|---|
| AI01 | Tóm tắt lịch sử sửa chữa | `config/prompts/history.txt` | `{{repair_history}}` |
| AI02 | Giải thích dịch vụ cho khách | `config/prompts/explain.txt` | `{{service}}` |
| AI03 | Báo giá nháp | `config/prompts/quote.txt` | `{{items}}`, `{{backend_total}}` |

Nguyên tắc bất di bất dịch: **AI không phải nguồn của dữ liệu nghiệp vụ.** Giá,
số lượng và tổng tiền đều do backend đọc từ CSDL và tự tính. Kết quả AI luôn
lưu ở trạng thái `PENDING` và phải được nhân viên duyệt trước khi sử dụng.

## 9. Sao lưu và khôi phục

```bash
# Sao lưu
copy garage.db backups\garage_2026-11-20.db     # Windows
cp garage.db backups/garage_2026-11-20.db         # macOS / Linux

# Khôi phục
copy backups\garage_2026-11-20.db garage.db
```

Nên dừng ứng dụng trước khi sao lưu để tránh ghi dở dang. Sau khi khôi phục,
chạy lại `python tests/test_schema_constraints.py` để kiểm tra dữ liệu còn hợp lệ.

## 10. Trạng thái triển khai

| Hạng mục | Trạng thái |
|---|---|
| Schema cơ sở dữ liệu (16 bảng, 29 chỉ mục, đủ ràng buộc) | Hoàn thành |
| Dữ liệu mẫu (171 dòng) | Hoàn thành |
| 16 sơ đồ thiết kế | Hoàn thành |
| Prompt ba chức năng AI | Hoàn thành |
| Đăng nhập, phiên ký, phân quyền bốn vai trò | Hoàn thành |
| CRUD nghiệp vụ + tìm kiếm, lọc, sắp xếp | Hoàn thành |
| Phiếu sửa chữa, hóa đơn, thanh toán | Hoàn thành |
| Dashboard và năm báo cáo | Hoàn thành |
| Ba chức năng AI và Human Review | Hoàn thành (chế độ `mock`) |
| Backend viết lại theo cấu trúc tầng | Hoàn thành |
| CSRF + kiểm tra Origin, giới hạn tân suất | Hoàn thành |
| Thông báo một lần, phân trang, kiểm tra đầu vào | Hoàn thành |
| Mọi thao tác ghi là POST (xoá không còn là GET) | Hoàn thành |
| Kiểm thử tự động (102 ca) | Hoàn thành |
| Ảnh chụp màn hình thật | Hoàn thành |
| Dockerfile và docker-compose | Đã có tệp, **chưa** chạy thử |
| Giao diện chính thức (đang dùng bản tối giản) | **Đang làm** |
| Kiểm thử với `AI_PROVIDER=openai` | **Chưa làm**, cần khoá API thật |
| Ca kiểm thử timeout / phản hồi rỗng / sai định dạng AI | **Chưa làm** |
| Kiểm thử nghiệm thu bởi người dùng thực tế | **Chưa làm** |

Chi tiết phần còn thiếu nằm ở `FINAL_ACCEPTANCE_CHECKLIST.md`.

## 11. Chạy bằng Docker

```bash
docker compose up --build
```

Mở trình duyệt tại <http://127.0.0.1:8000>. Lần chạy đầu dựng CSDL từ schema và
dữ liệu mẫu. Đặt `SECRET_KEY` thật trước khi dùng ở môi trường thật.

## 12. Chụp lại ảnh màn hình

```bash
python -m uvicorn app.main:app --port 8010
python docs/chup_man_hinh.py
```

Tệp ảnh nằm ở `screenshots/`, bảng mô tả nằm ở `docs/BANG_ANH.md`.

## 13. Tài liệu liên quan

| Tài liệu | Nội dung |
|---|---|
| `KT3_PROMPT_EXPERIMENTS.md` | Nhật ký thử nghiệm ba chức năng AI |
| `KT1_KT2_AI_USAGE.md` | Nhật ký sử dụng AI trong phân tích và lập trình |
| `KT3_AI_REVIEW.md` | Minh chứng AI review mã nguồn |
| `TEST_REPORT.md` | Kết quả kiểm thử, sinh tự động |
| `USER_ACCEPTANCE_TEST.md` | Kịch bản kiểm thử nghiệm thu người dùng |
| `FINAL_ACCEPTANCE_CHECKLIST.md` | Phiếu kiểm tra hoàn thành trước khi nộp |