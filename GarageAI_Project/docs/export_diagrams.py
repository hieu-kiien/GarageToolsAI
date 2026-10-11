# -*- coding: utf-8 -*-
"""Xuất 16 sơ đồ từ Báo cáo.docx sang docs/diagrams_final theo đúng tên trong Phụ lục A."""
import os
import shutil
import sys
import io
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = r"D:\1. LapTrinh\Nhom23_GarageToolsAI"
DOCX = os.path.join(ROOT, "Báo cáo.docx")
OUT = os.path.join(ROOT, "GarageAI_Project", "docs", "diagrams_final")

# ánh xạ: tên trong word/media  ->  tên theo Phụ lục A của báo cáo
MAP = [
    ('image1.png',  '01_context.png',              'Hình 1  Sơ đồ ngữ cảnh hệ thống'),
    ('image2.png',  '02_usecase.png',              'Hình 2  Sơ đồ Use Case'),
    ('image3.png',  '03_activity_order.png',       'Hình 3  Activity quy trình mua hàng'),
    ('image4.png',  '04_activity_repair.png',      'Hình 4  Activity quy trình sửa chữa'),
    ('image5.png',  '07_erd.png',                  'Hình 5  Sơ đồ ERD'),
    ('image6.png',  '08_architecture.png',         'Hình 6  Sơ đồ kiến trúc hệ thống'),
    ('image7.png',  '09_component.png',            'Hình 7  Sơ đồ thành phần'),
    ('image8.png',  '10_deployment.png',           'Hình 8  Sơ đồ triển khai'),
    ('image9.png',  '12_dfd.png',                  'Hình 9  Sơ đồ luồng dữ liệu tổng thể'),
    ('image10.png', '11_state.png',                'Hình 10 Sơ đồ trạng thái phiếu sửa chữa'),
    ('image11.png', '13_flow_login.png',           'Hình 11 Luồng đăng nhập và phân quyền'),
    ('image12.png', '14_flow_search_dashboard.png', 'Hình 12 Luồng tìm kiếm, lọc và dashboard'),
    ('image13.png', '15_flow_crud.png',            'Hình 13 Luồng CRUD và xử lý lỗi dữ liệu'),
    ('image14.png', '16_flow_ai_review.png',       'Hình 14 Luồng AI và Human Review'),
    ('image15.png', '05_ai_flow.png',              'Hình 15 Luồng dữ liệu khi gọi AI'),
    ('image16.png', '06_checkout_flow.png',        'Hình 16 Luồng dữ liệu quy trình checkout'),
]

os.makedirs(OUT, exist_ok=True)
z = zipfile.ZipFile(DOCX)

lines = [
    '# DANH SÁCH SƠ ĐỒ - GarageTools AI',
    '#',
    '# Tên tệp và số thứ tự hình đúng theo Phụ lục A của báo cáo.',
    '#',
    '# | Tệp | Nội dung |',
    '# |------|----------|',
]
ok = 0
for src, dst, mo_ta in MAP:
    with z.open('word/media/' + src) as f:
        data = f.read()
    with open(os.path.join(OUT, dst), 'wb') as f:
        f.write(data)
    ok += 1
    lines.append('| `%s` | %s |' % (dst, mo_ta))
    print('  %-28s <- %-12s (%d KB)' % (dst, src, len(data) // 1024))

with open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')

print('\nĐã xuất %d/16 sơ đồ vào %s' % (ok, OUT))
missing = [s for s, _, _ in MAP if 'word/media/' + s not in z.namelist()]
print('Thiếu:', missing if missing else 'không có')
z.close()