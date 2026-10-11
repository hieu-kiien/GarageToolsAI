# -*- coding: utf-8 -*-
"""Chạy toàn bộ kiểm thử và sinh TEST_REPORT.md từ kết quả thực tế."""
import io
import os
import re
import subprocess
import sys
import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUITES = [
    ('tests/test_schema_constraints.py', 'Kiểm thử ràng buộc cơ sở dữ liệu',
     'Đối chiếu mục 4.2 (danh sách bảng), mục 4.3 (ràng buộc) và mục 4.5 (dữ liệu mẫu).'),
    ('tests/test_backup_restore.py', 'Kiểm thử sao lưu và khôi phục',
     'Đối chiếu quy trình 5 bước tại mục 4.4.'),
    ('tests/test_backend.py', 'Kiểm thử end-to-end ứng dụng web',
     'Gọi thật các đường dẫn HTTP trên một CSDL tạm: đăng nhập, phân quyền,'
     ' CSRF, kiểm tra đầu vào, tiền và tồn kho (kể cả chạy đồng thời),'
     ' thông báo, phân trang, xoá dữ liệu và AI.'),
]

rows = []
tong_dat = tong_loi = 0

for path, ten, mo_ta in SUITES:
    full = os.path.join(BASE, path)
    r = subprocess.run([sys.executable, full], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    out = (r.stdout or '') + (r.stderr or '')
    n_run = re.search(r'Ran (\d+) test', out)
    n_ok = re.search(r'^OK', out, re.M)
    n_fail = re.search(r'FAILED \(.*?failures=(\d+)', out)
    n_err = re.search(r'FAILED \(.*?errors=(\d+)', out)
    dat = int(n_run.group(1)) if n_run else 0
    loi = (int(n_fail.group(1)) if n_fail else 0) + (int(n_err.group(1)) if n_err else 0)
    if not n_ok:
        loi = loi or 1
    tong_dat += dat - loi
    tong_loi += loi
    rows.append((path, ten, mo_ta, dat, loi))

print('%-44s %6s %6s' % ('BỘ KIỂM THỬ', 'TỔNG', 'LỖI'))
for path, ten, mo_ta, dat, loi in rows:
    print('%-44s %6d %6d' % (path, dat, loi))
print('-' * 60)
print('%-44s %6d %6d' % ('TỔNG CỘNG', tong_dat + tong_loi, tong_loi))

now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

L = []
w = L.append
w('# BÁO CÁO KIỂM THỬ — GarageTools AI')
w('')
w('| | |')
w('|---|---|')
w('| Ngày chạy | %s |' % now)
w('| Môi trường | Python %s, SQLite %s |'
  % ('.'.join(map(str, sys.version_info[:3])), __import__('sqlite3').sqlite_version))
w('| Tổng số ca | **%d** |' % (tong_dat + tong_loi))
w('| Kết quả | **%d đạt / %d lỗi** |' % (tong_dat, tong_loi))
w('')
w('---')
w('')
w('## 1. Phạm vi')
w('')
w('Bộ kiểm thử gồm ba phần: ràng buộc và dữ liệu mẫu của cơ sở dữ liệu, quy')
w('trình sao lưu/khôi phục, và toàn bộ ứng dụng web. Phần ứng dụng được kiểm')
w('tra bằng cách gọi thật các đường dẫn HTTP trên một cơ sở dữ liệu tạm dựng')
w('từ `schema.sql` và `seed_data.sql`, nên ca kiểm thử chạm đúng mã nguồn đang')
w('chạy chứ không kiểm tra bản sao.')
w('')
for path, ten, mo_ta, dat, loi in rows:
    w('### %s' % ten)
    w('')
    w('- Tệp: `%s`' % path)
    w('- Phạm vi: %s' % mo_ta)
    w('- Kết quả: %d ca, %d đạt, %d lỗi' % (dat, dat - loi, loi))
    w('')
w('## 2. Nhóm ca kiểm thử ràng buộc cơ sở dữ liệu')
w('')
w('| Nhóm | Nội dung kiểm tra |')
w('|---|---|')
w('| Hạng mục phiếu | `service_id` và `part_id` phải đúng một trong hai; số lượng và đơn giá không âm |')
w('| Chốt giá | `unit_price` và tổng hóa đơn không đổi khi sửa giá danh mục |')
w('| Thanh toán | Không thu vượt tổng; một phiếu chỉ có một hóa đơn; một hóa đơn nhiều khoản thu |')
w('| Ràng buộc khác | Biển số và tên đăng nhập trùng bị chặn; vai trò hợp lệ; mật khẩu lưu dạng băm |')
w('| Bảo vệ lịch sử | Không xóa được xe hoặc khách đã phát sinh giao dịch |')
w('| Human Review | Không thể duyệt kết quả AI mà không có người duyệt và thời điểm |')
w('| Dữ liệu mẫu | Đủ số lượng bản ghi theo mục 4.5; có đủ tình huống đặc biệt |')
w('| Chỉ mục | Đã tạo đủ chỉ mục quy định tại mục 4.3 |')
w('')
w('## 3. Nhóm ca kiểm thử sao lưu và khôi phục')
w('')
w('| Nhóm | Nội dung kiểm tra |')
w('|---|---|')
w('| Tạo bản sao | Sao lưu tạo được tệp khác rỗng và mở được |')
w('| Toàn vẹn bản sao | Bản sao chứa đủ 16 bảng |')
w('| Khôi phục | Dữ liệu trở về đúng trạng thái trước khi sao lưu |')
w('| Kiểm tra sau khôi phục | `integrity_check` đạt và dữ liệu liên kết vẫn nhất quán |')
w('| Ghi chưa commit | Sao lưu giữa lúc đang ghi không làm hỏng tệp, dữ liệu chưa commit không bị lọt |')
w('| Quy trình 4.4 | Năm bước trong mục 4.4 chạy đúng thứ tự |')
w('')
w('## 4. Nhóm ca kiểm thử ứng dụng web')
w('')
w('| Nhóm | Nội dung kiểm tra |')
w('|---|---|')
w('| Đăng nhập | Chưa đăng nhập bị chuyển về trang đăng nhập; sai mật khẩu, sai tài khoản và cookie giả đều bị từ chối |')
w('| Phân quyền | Bốn vai trò; kỹ thuật viên không quản lý tài khoản, lễ tân không duyệt AI, thu ngân không tiếp nhận phiếu |')
w('| Tìm kiếm lọc sắp xếp | Tìm theo tên, biển số; lọc trạng thái; sắp xếp đúng chiều; truy vấn độc hại không làm hỏng dữ liệu |')
w('| CRUD dùng chung | Thêm, sửa; biểu mẫu thiếu trường và trùng định danh bị chặn; bản ghi đã phát sinh giao dịch không xóa được |')
w('| Phiếu sửa chữa | Thêm hạng mục chốt đúng đơn giá danh mục; thiếu tồn kho bị chặn; chuyển trạng thái đúng luồng; kỹ thuật viên không sửa được phiếu không được phân công |')
w('| Hóa đơn và thanh toán | Tổng do backend tính; không lập trùng hóa đơn; thu một phần rồi thu đủ; không thu vượt và không thu bằng 0 |')
w('| Chức năng AI | Cả ba chức năng tạo được kết quả ở trạng thái PENDING; dịch vụ thiếu mô tả vẫn chạy; AI không tự thêm hạng mục hay lập hóa đơn |')
w('| Human Review | Duyệt/từ chối ghi đủ người duyệt và thời điểm; không duyệt lại được kết quả đã xử lý; người thiếu quyền bị từ chối |')
w('| Mô-đun cửa hàng | Xem và tìm sản phẩm trong phần mở rộng ngoài phạm vi đề tài |')
w('')
w('## 5. Cách chạy lại')
w('')
w('```bash')
for path, _, _, _, _ in rows:
    w('python %s' % path)
w('```')
w('')
w('## 6. Ghi chú')
w('')
w('- Các ca kiểm thử ứng dụng dùng `AI_PROVIDER=mock` nên không cần kết mối')
w('  mạng, không cần khoá API và cho kết quả lặp lại được.')
w('- Ca kiểm thử chạy trên cơ sở dữ liệu tạm nên không làm thay đổi `garage.db`.')
w('- Các ca kiểm thử không phủ môi trường thật có `AI_PROVIDER=openai` và không')
w('  phủ hành vi khi mất mạng; những tình huống đó cần kiểm thử thủ công.')
w('')
w('> Kết quả trên chỉ có giá trị tại thời điểm chạy. Trước khi nộp bài cần chạy')
w('> lại toàn bộ để chắc chắn không phát sinh hồi quy.')

with open(os.path.join(BASE, 'TEST_REPORT.md'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(L) + '\n')

print('\nĐã ghi TEST_REPORT.md  (%d đạt / %d lỗi)' % (tong_dat, tong_loi))