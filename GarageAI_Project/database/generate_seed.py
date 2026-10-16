# -*- coding: utf-8 -*-
"""Sinh database/seed_data.sql theo đặc tả mục 4.5 của báo cáo.

Mật khẩu demo: Garage@2026
Định dạng hash: pbkdf2_sha256$<số vòng lặp>$<salt hex>$<hash hex>
"""
import hashlib
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'seed_data.sql')
ITER = 200_000
DEMO_PASSWORD = 'Garage@2026'



EMAIL_THEO_VAI_TRO = {
    'quan_ly': 'huy.nguyen@garage.vn',
    'le_tan': 'ha.tran@garage.vn',
    'ky_thuat_vien': 'duc.le@garage.vn',
    'thu_ngan': 'ha.pham@garage.vn',
}


def email_of(username):
    return EMAIL_THEO_VAI_TRO.get(username, username + '@garage.vn')


MO_TA_PHU_TUNG = {
    'Dau': 'Dầu động cơ chất lượng cao, đóng can 1 lít.',
    'Loc': 'Bộ lọc thay thế cho dịch vụ bảo dưỡng định kỳ.',
    'May': 'Máy phát điện 12V phù hợp xe dưới 2.0L.',
    'Ac': 'Ắc quy 70Ah, sạc tốt, tuổi thọ trên 3 năm.',
    'Bo': 'Bộ má phanh trước gồm má phanh và đĩa phanh.',
    'Dia': 'Đĩa phanh trước, đường kính tiêu chuẩn.',
    'Lop': 'Lốp xe ô tô, kiểm tra áp suất và hoa văn.',
    'Cang': 'Cặp phuộc trước, bộ gồm lò xo và phớt giảm chấn.',
    'Bong': 'Bóng đèn pha LED H7, ánh sáng trắng, tuổi thọ cao.',
    'Guong': 'Gương chiếu hậu trái, kiểu gắn vào cửa.',
    'Ga': 'Ga và chìa khóa điện có mã, cần đăng kì cắt mới.',
}


def desc_of(name):
    for tu, mo_ta in MO_TA_PHU_TUNG.items():
        if name.startswith(tu):
            return mo_ta
    return None


def make_hash(username):
    """Salt cố định theo tên đăng nhập để dữ liệu mẫu tái lập được."""
    salt = hashlib.sha256(('garage-salt::' + username).encode()).hexdigest()[:16]
    h = hashlib.pbkdf2_hmac('sha256', DEMO_PASSWORD.encode(), salt.encode(), ITER)
    return 'pbkdf2_sha256$%d$%s$%s' % (ITER, salt, h.hex())


L = []
def w(line=''):
    L.append(line)


def q(v):
    if v is None:
        return 'NULL'
    if isinstance(v, int):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


# ---------------------------------------------------------------- tài khoản
users = [
    ('quan_ly',    'Nguyễn Quang Huy',    'MANAGER'),
    ('le_tan',     'Trần Thu Hà',         'RECEPTIONIST'),
    ('ky_thuat_vien', 'Lê Minh Đức',     'TECHNICIAN'),
    ('thu_ngan',   'Phạm Thu Hà',        'CASHIER'),
]

# ---------------------------------------------------------------- khách hàng
customers = [
    ('Nguyễn Văn An',   '0901000001', 'an.nguyen@gmail.com',    '12 Nguyễn Huệ, Hà Nội'),
    ('Trần Thị Bình',    '0901000002', 'binh.tran@gmail.com',    '45 Lê Lợi, Hà Nội'),
    ('Lê Quang Cường',   '0901000003', 'cuong.le@gmail.com',     '78 Hai Bà Trưng, Hà Nội'),
    ('Phạm Thị Dung',   '0901000004', 'dung.pham@gmail.com',    '23 Cầu Giấy, Hà Nội'),
    ('Đỗ Hữu Giang',    '0901000005', 'giang.do@gmail.com',     '5 Tây Sơn, Hà Nội'),
    ('Vũ Thị Hà',       '0901000006', 'ha.vu@gmail.com',        '91 Ba Đình, Hà Nội'),
    ('Hoàng Minh Khôi',  '0901000007', 'khoi.hoang@gmail.com',   '30 Giải Phóng, Hà Nội'),
    'Ngô Thị Lan',
    'Bùi Văn Long',
    'Đặng Thị Mai',
]
customers_full = [
    ('Nguyễn Văn An',   '0901000001', 'an.nguyen@gmail.com',  '12 Nguyễn Huệ, Hà Nội'),
    ('Trần Thị Bình',    '0901000002', 'binh.tran@gmail.com',  '45 Lê Lợi, Hà Nội'),
    ('Lê Quang Cường',   '0901000003', 'cuong.le@gmail.com',   '78 Hai Bà Trưng, Hà Nội'),
    ('Phạm Thị Dung',   '0901000004', 'dung.pham@gmail.com',  '23 Cầu Giấy, Hà Nội'),
    ('Đỗ Hữu Giang',    '0901000005', 'giang.do@gmail.com',   '5 Tây Sơn, Hà Nội'),
    ('Vũ Thị Hà',       '0901000006', 'ha.vu@gmail.com',      '91 Ba Đình, Hà Nội'),
    ('Hoàng Minh Khôi',  '0901000007', 'khoi.hoang@gmail.com', '30 Giải Phóng, Hà Nội'),
    ('Ngô Thị Lan',     '0901000008', 'lan.ngo@gmail.com',    '17 Tràng Bông, Hà Nội'),
    ('Bùi Văn Long',    '0901000009', 'long.bui@gmail.com',   '64 Giải Phóng, Hà Nội'),
    ('Đặng Thị Mai',    '0901000010', 'mai.dang@gmail.com',   '8 Láng, Hà Nội'),
]

# ------------------------------------------------------------------ phương tiện
# Cố ý: biển số 30A-1111 thuộc khách 1 và có tới 5 lần sửa chữa,
# dùng làm dữ liệu cho chức năng AI tóm tắt lịch sử (mục 16.7).
vehicles = [
    ('30A-1111', 'Toyota',    'Vios',     2019, 1),
    ('30A-1112', 'Honda',     'Civic',    2020, 1),
    ('30B-2222', 'Mazda',     'CX-5',     2021, 2),
    ('30B-2223', 'Ford',      'Ranger',   2018, 2),
    ('30C-3333', 'Hyundai',   'Tucson',   2022, 3),
    ('30C-3334', 'Kia',       'Cerato',   2020, 3),
    ('30D-4444', 'Nissan',    'X-Trail',  2019, 4),
    ('30D-4445', 'Suzuki',    'Vitara',   2021, 4),
    ('30E-5555', 'Lexus',     'ES350',    2017, 5),
    ('30E-5556', 'Mercedes',  'C200',     2020, 5),
    ('30F-6666', 'Chevrolet', 'Cruze',    2018, 6),
    ('30G-7777', 'BMW',       'X3',       2021, 7),
]

# ------------------------------------------------------------------ dịch vụ
# Dịch vụ số 7 cố ý để NULL mô tả để phục vụ ca kiểm thử dữ liệu thiếu của AI02.
services = [
    ('Thay dầu máy và lọc gió',      'Thay dầu máy định kỳ kèm thay lọc gió, kiểm tra mức dầu và vòng quay.', 450000),
    ('Thay phuộc trước',             'Thay cặp phuộc trước kèm cân bằng bánh xe.', 1200000),
    ('Sửa phanh',                    'Kiểm tra má phanh, đĩa phanh và thay thế linh kiện hư hỏng.', 650000),
    ('Thay máy phát điện',           'Thay ắc quy và kiểm tra hệ thống điện của xe.', 5500000),
    ('Bảo dưỡng động cơ',            'Kiểm tra tổng thể động cơ, thay dầu bộ lọc và các nước.', 1800000),
    ('Thay lốp và cân bằng',         'Thay lốp, kiểm tra áp suất và cân bằng bánh xe.', 300000),
    ('Nâp cấp ánh sáng',              None, 2400000),
    ('Vệ sinh khoang máy và nội thất', 'Vệ sinh toàn bộ khoang lái xe và thảm lót.', 300000),
]

# ------------------------------------------------------------------ phụ tùng
# Phụ tùng số 12 cố ý có tồn kho bằng 0 để kiểm thử giới hạn tồn kho.
parts = [
    ('Dầu động cơ 5W-30 (1 lít)',      120,  180000),
    ('Lọc gió động cơ',                 60,   85000),
    ('Lọc dầu động cơ',                 70,   120000),
    ('Lọc gió cabin',                   90,   95000),
    ('Máy phát 12V 60Ah',               15,   3200000),
    ('Ắc quy 70Ah',                     25,   2500000),
    ('Bộ má phanh trước',               40,   950000),
    ('Đĩa phanh trước',                 35,   780000),
    ('Lốp xe 205/55R16',                0,    1350000),
    ('Lốp xe 215/55R17',                30,   1650000),
    ('Cặp phuộc trước',                 24,   2800000),
    ('Bóng đèn pha LED H7',             80,   650000),
    ('Gương chiếu hậu trái',            18,   1450000),
    ('Gương chiếu hậu phải',           18,   1450000),
    ('Ga và chìa khóa điện',          12,   2100000),
]

# ------------------------------------------------------------------ lịch hẹn
# Cặp lịch 9 và 10 trùng khung giờ trên cùng xe để kiểm thử cảnh báo xung đột.
appointments = [
    (1, 1,  '2026-11-20 09:00', 'Bảo dưỡng định kỳ trước mùa lạ.',              'CONFIRMED'),
    (1, 2,  '2026-11-21 14:30', 'Thay phuộc sau khi khách báo rung phía trước.', 'SCHEDULED'),
    (2, 3,  '2026-11-22 10:15', 'Kiểm tra hệ thống phanh.',                       'SCHEDULED'),
    (2, 4,  '2026-11-23 08:00', 'Thay dầu máy.',                                  'CONFIRMED'),
    (3, 5,  '2026-11-23 16:00', 'Kiểm tra lỗi đèn pha.',                          'SCHEDULED'),
    (4, 7,  '2026-11-24 13:45', 'Thay máy phát.',                                 'SCHEDULED'),
    (4, 8,  '2026-11-25 09:30', 'Thay lốp định kỳ.',                              'SCHEDULED'),
    (5, 9,  '2026-11-26 11:00', 'Kiểm tra hệ thống điện.',                        'CONFIRMED'),
    (6, 11, '2026-11-27 15:00', 'Vệ sinh xe sau chuyến đi dài.',                  'SCHEDULED'),
    (6, 11, '2026-11-27 15:00', 'Ghi thêm yêu cầu vệ sinh ghế.',                  'SCHEDULED'),
]

# ------------------------------------------------------------------ phiếu sửa chữa
# Xe 1 (30A-1111) có 5 phiếu: dùng cho ca kiểm thử AI tóm tắt lịch sử.
repair_orders = [
    # (vehicle, technician, status, ghi chú kỹ thuật, ngày)
    (1,  3, 'COMPLETED',  'Thay dầu, lọc gió. Khách định kỳ 6 tháng.',        '2026-02-14 09:20'),
    (1,  3, 'COMPLETED',  'Thay máy phát. Xe khởi động yếu khi trời lạnh.',   '2026-04-03 10:05'),
    (1,  3, 'COMPLETED',  'Sửa phanh sau. Có tiếng rít khi phanh lùi.',         '2026-06-21 14:40'),
    (1,  3, 'COMPLETED',  'Thay lốp trước và sau, cân bằng bánh xe.',          '2026-08-30 08:50'),
    (1,  3, 'COMPLETED',  'Bảo dưỡng động cơ, thay dầu bộ lọc.',              '2026-10-18 11:30'),
    (2,  3, 'COMPLETED',  'Thay phuộc trước.',                                '2026-03-11 09:00'),
    (3,  3, 'CANCELLED',  'Khách huỷ lịch sau khi đã thay lọc gió cabin.',   '2026-05-22 15:10'),
    (5,  3, 'COMPLETED',  'Sửa phanh trước, thay má và đĩa phanh.',            '2026-07-09 10:40'),
    (9,  3, 'COMPLETED',  'Thay máy phát và ắc quy.',                          '2026-09-02 13:20'),
    (6,  3, 'REPAIRING',   'Đang thay bóng đèn pha LED.',                       '2026-11-12 09:15'),
    (10, 3, 'ESTIMATING',  'Chờ duyệt báo giá nâng cấp ánh sáng.',             '2026-11-13 10:30'),
    (11, 3, 'RECEIVED',    'Khách báo gương chiếu hậu bị trầy, chờ tiếp nhận.', '2026-11-14 16:45'),
]

# ------------------------------------------------------------ hạng mục phiếu
# (mã phiếu, dịch vụ | phụ tùng, số lượng)
items = [
    (1, 'S1', 1, 1), (1, 'P1', 4, 1),
    (2, 'S4', 1, 1), (2, 'P5', 1, 1),
    (3, 'S3', 2, 1), (3, 'P7', 2, 1),
    (4, 'S6', 4, 1), (4, 'P9', 4, 1),
    (5, 'S5', 1, 1), (5, 'P2', 1, 1), (5, 'P3', 1, 1),
    (6, 'S2', 2, 1),
    (7, 'S8', 1, 1), (7, 'P4', 1, 1),
    (8, 'S3', 1, 1), (8, 'P7', 1, 1), (8, 'P8', 2, 1),
    (9, 'S4', 1, 1), (9, 'P6', 1, 1),
    (10, 'S7', 2, 1), (10, 'P12', 2, 1),
    # Phiếu 11 (ESTIMATING) nâng cấp ánh sáng: thêm bóng LED cho cả đèn pha và
    # đèn sương mù, một bộ LED phụ, và vệ sinh khoang lái sau khi tháo cụm đèn.
    (11, 'S7', 1, 1),
    (11, 'P12', 4, 1), (11, 'P12', 2, 1), (11, 'S8', 1, 1),
]
# Phiếu 12 cố ý chưa có hạng mục để kiểm thử tình huống báo giá rỗng.

logs = [
    (1, 'Tiếp nhận, kiểm tra mức dầu trong bình. Mức dầu thấp hơn mốc.'),
    (1, 'Thay dầu mới và lọc gió. Kiểm tra không rò rỉ sau khi thay.'),
    (2, 'Đo áp bình ắc quy: 11.4V, dưới ngưỡng. Đề xuất thay máy phát.'),
    (2, 'Thay máy phát mới. Sạc lại bình và kiểm tra hệ thống điện.'),
    (3, 'Khách báo tiếng rít khi phanh lùi. Kiểm tra má phanh bị mòn.'),
    (3, 'Thay má phanh trước. Độ dày sau thay nằm trong giới hạn.'),
    (4, 'Kiểm tra áp suất bốn lốp. Hai lốp trước dưới ngưỡng.'),
    (4, 'Thay bốn lốp và cân bằng. Kiểm tra van và lông vô tuyến không hỏng.'),
    (5, 'Kiểm tra tổng thể động cơ, không thấy rò rỉ dầu.'),
    (5, 'Thay dầu động cơ và bộ lọc dầu. Khuyến nghị thay dầu sau 6 tháng.'),
    (6, 'Kiểm tra chơi phuộc, cần thay cả cặp trước.'),
    (7, 'Vệ sinh khoang lái xe và thay lọc gió cabin.'),
    (8, 'Đĩa phán mòn đến mức tối thiểu, phải thay.'),
    (8, 'Thay má phanh trước và đĩa phanh trước. Đã đường xem lại.'),
    (9, 'Ắc quy xuống cạn, đề xuất thay cả máy phát và ắc quy.'),
    (9, 'Thay máy phát và ắc quy. Kiểm tra sạc ổn định.'),
    (10, 'Đèn pha bị vàng do bóng cháy. Cần nâng cấp bộ đèn.'),
    (10, 'Đang chờ khách duyệt báo giá trước khi lắp đèn.'),
    (11, 'Khách muốn nâng cấp ánh sáng, cần báo giá nháp.'),
    (12, 'Gương chiếu hậu bị trầy xước, chờ tiếp nhận và báo giá.'),
]

# ---------------------------------------------------------- hóa đơn và thanh toán
# total = tổng unit_price x qty của các hạng mục thuộc phiếu (backend tự tính)
def svc_price(code):
    for name, desc, price in services:
        if 'S' + str(services.index((name, desc, price)) + 1) == code:
            return price
    raise KeyError(code)


S = {i + 1: (n, d, p) for i, (n, d, p) in enumerate(services)}
P = {i + 1: (n, st, p) for i, (n, st, p) in enumerate(parts)}

order_totals = {}
for oid, code, qty, _ in items:
    price = S[int(code[1:])][2] if code.startswith('S') else P[int(code[1:])][2]
    order_totals[oid] = order_totals.get(oid, 0) + price * qty

# 6 hóa đơn đã thanh toán đủ, 1 chưa thanh toán, 1 thanh toán một phần
invoices = [
    (1,  'PAID'),
    (2,  'PAID'),
    (3,  'PAID'),
    (5,  'PAID'),
    (8,  'PAID'),
    (9,  'PAID'),
    (10, 'UNPAID'),    # chưa thu
    (11, 'PARTIAL'),   # thu một phần
]
# 6 khoản thu đủ cho 6 hoá đơn đã thanh toán; hoá đơn 8 thu một phần;
# hoá đơn 1 thu bằng hai khoản để thể hiện việc một hoá đơn có nhiều khoản thu.
payments = [
    (1, 'CASH',     'half'),   # hoá đơn 1 thu bằng hai khoản
    (1, 'TRANSFER', 'half'),
    (2, 'CASH',     'full'),
    (3, 'CARD',     'full'),
    (4, 'CASH',     'full'),
    (5, 'TRANSFER', 'full'),
    (6, 'CARD',     'full'),
    (8, 'ZALO',     'half'),   # hoá đơn 8 mới thu một phần
]

ai_results = [
    ('history', 1,  'APPROVED', 2,
     'Xe 30A-1111 Toyota Vios đã sửa chữa 5 lần gần nhất.\n'
     '1. 14/02/2026: Thay dầu máy và lọc gió - hoàn tất\n'
     '2. 03/04/2026: Thay máy phát điện - hoàn tất\n'
     '3. 21/06/2026: Sửa phanh - hoàn tất\n'
     '4. 30/08/2026: Thay lốp và cân bằng - hoàn tất\n'
     '5. 18/10/2026: Bảo dưỡng động cơ - hoàn tất\n'
     'Dữ liệu thiếu: Không có'),
    ('history', 12, 'PENDING',  None,
     'Xe 30F-6666 Chevrolet Cruze chưa có lịch sử sửa chữa nào trong hệ thống.'),
    ('explain', 1,  'APPROVED', 2,
     '1. Dịch vụ là gì: Thay dầu máy và lọc gió là hạng mục bảo dưỡng định kỳ, '
     'gồm thay dầu máy và thay bộ lọc gió để động cơ bớt hao mòn.\n'
     '2. Hạng mục đang ghi nhận: Thay dầu máy và lọc gió; Dầu động cơ 5W-30.\n'
     '3. Khách cần lưu ý: Chi phí dự kiến 1.080.000 đồng.'),
    ('explain', 7,  'PENDING',  None,
     '1. Dịch vụ là gì: Danh mục chưa có mô tả cho dịch vụ này.\n'
     '2. Hạng mục đang ghi nhận: Nâng cấp ánh sáng.\n'
     '3. Khách cần lưu ý: Không có'),
    ('quote', 10, 'APPROVED', 1,
     'Bảng báo giá nháp cho phiếu sửa chữa số 10.\n'
     '- Nâng cấp ánh sáng x 2: 4.800.000\n'
     '- Bóng đèn pha LED H7 x 2: 1.300.000\n'
     'Tổng dự kiến: 6.100.000\n'
     'Báo giá nháp, cần nhân viên kiểm tra trước khi sử dụng.'),
    ('quote', 12, 'PENDING',  None,
     'Phiếu sửa chữa số 12 chưa có hạng mục nào được ghi nhận nên chưa thể lập báo giá nháp.'),
]

shop_categories = [('Dụng cụ tay', 'dung-cu-tay'), ('Dụng cụ điện', 'dung-cu-dien'),
                   ('Thiết bị kiểm tra', 'thiet-bi-kiem-tra'), ('Dầu bôi trục và vòng bi', 'dau-boi-truc'),
                   ('Phụ kiện và vỏ xe', 'phu-kien'), ('Dụng cụ chuyên dụng', 'dung-cu-chuyen-dung')]

shop_products = [
    ('Bộ khoá vặn 12 chiếc', 1, 'DCV-001', 380000, 25, 'Khoá vặn từ 8 đến 19 mm, đúc thép crôm.'),
    ('Bộ khoá vặn lục giác 9 chiếc', 1, 'DCV-002', 260000, 30, 'Khoá lục giác chuẩn, có đầu cầu.'),
    ('Kìm cuối 8 inch', 1, 'DCV-003', 145000, 45, 'Kìm cuối cách điện.'),
    ('Búa móng ngựa 16 ounce', 1, 'DCV-004', 320000, 18, 'Búa đầu thép, cán gỗ.'),
    ('Xô 20 lít có nắp', 1, 'DCV-005', 85000, 60, 'Xô nhựa HDPE dùng để chứa nhớt thải.'),
    ('Máy khoan bê tông', 2, 'DCD-001', 2450000, 8, 'Công suất 800W, kèm đầu khoan và mũi khoan.'),
    ('Máy mài góc 100mm', 2, 'DCD-002', 1680000, 12, 'Dùng để cắt và mài bề mặt kim loại.'),
    ('Máy hàn thiếc 60W', 2, 'DCD-003', 560000, 20, 'Hàn mạch điện và dây.'),
    ('Đầu khoan từ 3 đến 10mm', 2, 'DCD-004', 210000, 50, 'Bộ 8 đầu khoan, chuẩn côn chuẩn.'),
    ('Đèn pin LED 1000W', 2, 'DCD-005', 1200000, 14, 'Đèn chiếu sáng góc rộng, pin sạc.'),
    ('Máy đo áp suất lốp', 3, 'TBK-001', 890000, 22, 'Đo áp suất bằng đồng hồ, hiển thị kPa và psi.'),
    ('Bộ dụng cụ chẩn đoán OBD', 3, 'TBK-002', 950000, 16, 'Đọc mã lỗi ECU qua cổng OBD-II.'),
    ('Máy đo áp lốp', 3, 'TBK-003', 420000, 26, 'Đo áp suất lốp kỹ thuật số.'),
    ('Đầu đo nhiệt độ dầu', 3, 'TBK-004', 680000, 11, 'Cảm biến và màn hình hiển thị.'),
    ('Mỡ chịu nhiệt 400g', 4, 'DBT-001', 92000, 70, 'Mỡ cầu hữu cơ chịu nhiệt cao.'),
    ('Dầu bôi trục 1 lít', 4, 'DBT-002', 165000, 55, 'Dầu bôi trục và vòng bi chất lượng cao.'),
    ('Bóng đèn pha LED H7', 4, 'DBT-003', 650000, 35, 'Cặp bóng đèn LED trắng.'),
    ('Gương chiếu hậu trái xe ô tô', 5, 'PKC-001', 1450000, 10, 'Gương điện, có đèn báo rẽ.'),
    ('Bọt rửa xe ô tô 5 lít', 6, 'DCC-001', 155000, 40, 'Bọt rửa xe tạo nhiều bọt, không vết.'),
    ('Khăn lau xe chuyên dụng 30x50', 6, 'DCC-002', 45000, 90, 'Sợi microfiber, hút nước tốt.'),
]

shop_orders = [
    ('Nguyễn Văn An', '0901000001', '12 Nguyễn Huệ, Hà Nội', 'PAID'),
    ('Phạm Thị Dung', '0901000004', '23 Cầu Giấy, Hà Nội', 'PENDING'),
]
shop_order_items = [
    (1, 1, 1, 380000), (1, 13, 1, 420000), (1, 18, 1, 950000),
    (2, 3, 2, 145000), (2, 20, 3, 45000),
]

# =============================================================================
# GHI RA FILE
# =============================================================================
w('-- ' + '=' * 75)
w('-- GarageTools AI  |  DỮ LIỆU MẪU')
w('-- File   : database/seed_data.sql')
w('-- Đặc tả : Báo cáo mục 4.5 - Dữ liệu mẫu cho bản demo')
w('-- Mật khẩu demo chung: %s' % DEMO_PASSWORD)
w('--')
w('-- Cảnh báo: đây là tài khoản dùng cho học tập và demo. Khi triển khai thật')
w('-- phải đổi toàn bộ mật khẩu (xem mục 16.16 của báo cáo).')
w('--')
w('-- Các tình huống cố ý tạo ra để phục vụ kiểm thử:')
w('--   * Xe 30A-1111 có 5 lần sửa chữa  -> dữ liệu cho AI tóm tắt lịch sử')
w('--   * Phiếu 12 chưa có hạng mục        -> báo giá nháp rỗng')
w('--   * Dịch vụ 7 không có mô tả        -> AI giải thích gặp dữ liệu thiếu')
w('--   * Phụ tùng 9 tồn kho bằng 0       -> kiểm thử giới hạn tồn kho')
w('--   * Hoá đơn 10 chưa thu, 11 thu một phần -> kiểm thử thanh toán')
w('--   * Hai lịch hẹn 9 và 10 trùng giờ, cùng xe -> kiểm thử phát hiện trùng')
w('-- ' + '=' * 75)
w()
w('PRAGMA foreign_keys = ON;')
w('BEGIN TRANSACTION;')
w()

w('-- ---------------------------------------------------------------------------')
w('-- 1. Tài khoản: 4 vai trò nghiệp vụ')
w('-- ---------------------------------------------------------------------------')
for i, (un, full, role) in enumerate(users, 1):
    w('INSERT INTO users (id, username, password_hash, full_name, email, role, auth_version) VALUES')
    w('  (%d, %s, %s, %s, %s, %s, 1);'
      % (i, q(un), q(make_hash(un)), q(full), q(email_of(un)), q(role)))
w()

w('-- ---------------------------------------------------------------------------')
w('-- 2. Khách hàng: 10')
w('-- ---------------------------------------------------------------------------')
for i, (name, phone, mail, addr) in enumerate(customers_full, 1):
    w('INSERT INTO customers (id, name, phone, email, address) VALUES')
    w('  (%d, %s, %s, %s, %s);' % (i, q(name), q(phone), q(mail), q(addr)))
w()

w('-- ---------------------------------------------------------------------------')
w('-- 3. Xe: 12')
w('-- ---------------------------------------------------------------------------')
for i, (plate, brand, model, year, cust) in enumerate(vehicles, 1):
    w('INSERT INTO vehicles (id, customer_id, plate, brand, model, year) VALUES')
    w('  (%d, %d, %s, %s, %s, %d);' % (i, cust, q(plate), q(brand), q(model), year))
w()

w('-- ---------------------------------------------------------------------------')
w('-- 4. Dịch vụ: 8 (dịch vụ 7 cố ý không có mô tả)')
w('-- ---------------------------------------------------------------------------')
for i, (name, desc, price) in enumerate(services, 1):
    w('INSERT INTO services (id, name, description, price) VALUES')
    w('  (%d, %s, %s, %d);' % (i, q(name), q(desc), price))
w()

w('-- ---------------------------------------------------------------------------')
w('-- 5. Phụ tùng: 15 (phụ tùng 9 cố ý hết hàng)')
w('-- ---------------------------------------------------------------------------')
for i, (name, stock, price) in enumerate(parts, 1):
    w('INSERT INTO parts (id, name, sku, stock, min_stock, price, description) VALUES')
    w('  (%d, %s, %s, %d, %d, %d, %s);'
      % (i, q(name), q('PT-%03d' % i), stock,
         5 if stock > 0 else 2, price, q(desc_of(name))))
w()

w('-- ---------------------------------------------------------------------------')
w('-- 5b. Số dư mở đầu kho (stock_transactions): mỗi phụ tùng tồn > 0 có đúng')
w('--     một dòng ADJUSTMENT bằng đúng `parts.stock`. Bất biến')
w('--     SUM(stock_transactions.qty) == parts.stock bắt đầu từ đây.')
w('-- ---------------------------------------------------------------------------')
for i, (name, stock, price) in enumerate(parts, 1):
    if stock > 0:
        w('INSERT INTO stock_transactions (id, part_id, qty, reason, note) VALUES')
        w('  (%d, %d, %d, \'ADJUSTMENT\', \'Số dư mở đầu khi khởi tạo hệ thống.\');'
          % (i, i, stock))
w()

w('-- ---------------------------------------------------------------------------')
w('-- 6. Lịch hẹn: 10')
w('-- ---------------------------------------------------------------------------')
for i, (cust, veh, when, note, st) in enumerate(appointments, 1):
    w('INSERT INTO appointments (id, customer_id, vehicle_id, scheduled_at, notes, status) VALUES')
    w('  (%d, %d, %d, %s, %s, %s);' % (i, cust, veh, q(when), q(note), q(st)))
w()

w('-- ---------------------------------------------------------------------------')
w('-- 7. Phiếu sửa chữa: 12, phủ đủ sáu trạng thái')
w('-- ---------------------------------------------------------------------------')
for i, (veh, tech, st, note, created) in enumerate(repair_orders, 1):
    w('INSERT INTO repair_orders (id, vehicle_id, technician_id, status, technical_notes, created_at) VALUES')
    w('  (%d, %d, %d, %s, %s, %s);' % (i, veh, tech, q(st), q(note), q(created)))
w()

w('-- ---------------------------------------------------------------------------')
w('-- 8. Hạng mục: %d. unit_price chốt đúng bằng giá tại thời điểm thêm' % len(items))
w('-- ---------------------------------------------------------------------------')
for i, (oid, code, qty, _) in enumerate(items, 1):
    price = S[int(code[1:])][2] if code.startswith('S') else P[int(code[1:])][2]
    w('INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES')
    w('  (%d, %d, %s, %s, %d, %d);' % (
        i, oid,
        q(int(code[1:])) if code.startswith('S') else 'NULL',
        q(int(code[1:])) if code.startswith('P') else 'NULL',
        qty, price))
w()

w('-- ---------------------------------------------------------------------------')
w('-- 9. Nhật ký kỹ thuật: %d' % len(logs))
w('-- ---------------------------------------------------------------------------')
for i, (oid, note) in enumerate(logs, 1):
    w('INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES')
    w('  (%d, %d, 3, %s);' % (i, oid, q(note)))
w()

w('-- ---------------------------------------------------------------------------')
w('-- 10. Hoá đơn: %d (6 đã thu đủ, 1 chưa thu, 1 thu một phần)' % len(invoices))
w('--     total = tổng unit_price x qty của hạng mục thuộc phiếu, do backend tính')
w('-- ---------------------------------------------------------------------------')
inv_total = {}          # id hoá đơn -> tổng tiền
inv_created = {}        # id hoá đơn -> thời điểm lập theo phiếu
for i, (oid, st) in enumerate(invoices, 1):
    total = order_totals[oid]
    created = repair_orders[oid - 1][4]
    inv_total[i] = total
    inv_created[i] = created
    paid = 0
    if st == 'PAID':
        paid = total
    elif st == 'PARTIAL':
        paid = total // 2
    w('INSERT INTO invoices (id, repair_order_id, total, paid, status, created_at) VALUES')
    w('  (%d, %d, %d, %d, %s, %s);' % (i, oid, total, paid, q(st), q(created)))
w()

w('-- ---------------------------------------------------------------------------')
w('-- 11. Thanh toán: %d' % len(payments))
w('-- ---------------------------------------------------------------------------')
for i, (inv, method, mode) in enumerate(payments, 1):
    total = inv_total[inv]
    amt = total if mode == 'full' else total // 2
    paid_at = inv_created[inv]
    w('INSERT INTO payments (id, invoice_id, amount, method, paid_at) VALUES')
    w('  (%d, %d, %d, %s, %s);' % (i, inv, amt, q(method), q(paid_at)))
w()

w('-- ---------------------------------------------------------------------------')
w('-- 12. Kết quả AI: %d (mỗi chức năng 1 kết quả đã duyệt, 1 kết quả chờ duyệt)' % len(ai_results))
w('-- ---------------------------------------------------------------------------')
for i, (kind, oid, rev, by, out) in enumerate(ai_results, 1):
    valid = 0 if rev == 'PENDING' else 1
    inp = '{"repair_order_id": %d, "nguon": "seed_data"}' % oid
    if rev == 'PENDING':
        w('INSERT INTO ai_results (id, kind, repair_order_id, input_json, output_text, is_valid, review_status) VALUES')
        w('  (%d, %s, %d, %s, %s, 0, %s);' % (i, q(kind), oid, q(inp), q(out), q(rev)))
    else:
        w('INSERT INTO ai_results (id, kind, repair_order_id, input_json, output_text, is_valid, review_status, reviewed_by, reviewed_at) VALUES')
        w('  (%d, %s, %d, %s, %s, 1, %s, %d, %s);' % (
            i, q(kind), oid, q(inp), q(out), q(rev), by, q('2026-11-15 09:00:00')))
w()

w('-- ---------------------------------------------------------------------------')
w('-- 13. Cửa hàng dụng cụ (MỞ RỘNG, ngoài phạm vi đề tài)')
w('--     6 danh mục, %d sản phẩm, %d đơn hàng' % (len(shop_products), len(shop_orders)))
w('-- ---------------------------------------------------------------------------')
for i, (name, slug) in enumerate(shop_categories, 1):
    w('INSERT INTO shop_categories (id, name, slug) VALUES (%d, %s, %s);' % (i, q(name), q(slug)))
w()
for i, (name, cat, sku, price, stock, desc) in enumerate(shop_products, 1):
    w('INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES')
    w('  (%d, %d, %s, %s, %d, %d, %s);' % (i, cat, q(name), q(sku), price, stock, q(desc)))
w()
for i, (name, phone, addr, st) in enumerate(shop_orders, 1):
    oid_items = [(pid, qty, up) for o, pid, qty, up in shop_order_items if o == i]
    total = sum(qty * up for _, qty, up in oid_items)
    w('INSERT INTO shop_orders (id, customer_name, phone, address, total, status) VALUES')
    w('  (%d, %s, %s, %s, %d, %s);' % (i, q(name), q(phone), q(addr), total, q(st)))
w()
for i, (oid, pid, qty, up) in enumerate(shop_order_items, 1):
    w('INSERT INTO shop_order_items (id, order_id, product_id, qty, unit_price) VALUES')
    w('  (%d, %d, %d, %d, %d);' % (i, oid, pid, qty, up))
w()

w('-- ---------------------------------------------------------------------------')
w('-- 14. Bảo hành: 4 (SERVICE và PART đan xen, phủ đủ ACTIVE / EXPIRED)')
w('--     Chỉ gắn với phiếu COMPLETED. scope XOR: SERVICE có service_id,')
w('--     PART có part_id — đúng một trong hai.')
w('-- ---------------------------------------------------------------------------')
warranties = [
    # (repair_order_id, scope, service_id, part_id, months, start, status, note)
    (1, 'SERVICE', 1,   None, 6, '2026-02-14', 'EXPIRED',
     'Bảo hành thay dầu động cơ 6 tháng.'),
    (2, 'PART',    None, 5,   12, '2026-04-03', 'ACTIVE',
     'Bảo hành máy phát ắc quy 12 tháng.'),
    (5, 'SERVICE', 5,   None, 3, '2026-10-18', 'ACTIVE',
     'Bảo hành bảo dưỡng định kỳ 3 tháng.'),
    (8, 'PART',    None, 7,   6, '2026-07-09', 'ACTIVE',
     'Bảo hành má phanh trước 6 tháng.'),
]
for i, (oid, scope, sid, pid, months, start, status, note) in enumerate(warranties, 1):
    if status == 'EXPIRED':
        end = {'2026-02-14': '2026-08-14'}[start]
    else:
        end = {'2026-04-03': '2027-04-03', '2026-10-18': '2027-01-18',
               '2026-07-09': '2027-01-09'}[start]
    w('INSERT INTO warranties (id, repair_order_id, scope, service_id, part_id,'
      ' months, start_date, end_date, status, note) VALUES')
    w('  (%d, %d, %s, %s, %s, %d, %s, %s, %s, %s);' % (
        i, oid, q(scope),
        str(sid) if sid else 'NULL', str(pid) if pid else 'NULL',
        months, q(start), q(end), q(status), q(note)))
w()

w('-- ---------------------------------------------------------------------------')
w('-- 15. Biên bản tiếp nhận (intake_records): 3 bản ghi mẫu cho phiếu 1, 10, 11')
w('-- ---------------------------------------------------------------------------')
intake_records = [
    (1,  48500, 'THREE_QUARTER', 'Sơn zin đều, vết xước nhẹ cản sau bên phải.',
     'Chìa khoá thông minh, lốp dự phòng, bộ kích theo xe.',
     'Khách yêu cầu kiểm tra kỹ mức dầu và lọc gió.', 2, '2026-02-14 09:25'),
    (10, 62300, 'HALF', 'Cụm đèn pha trước ố vàng, thân vỏ không móp méo.',
     'Chìa khoá cơ, thảm sàn cao su.',
     'Tiếp nhận kiểm tra nâng cấp cụm đèn pha LED.', 2, '2026-11-12 09:20'),
    (11, 35800, 'FULL', 'Ngoại thất nguyên vẹn, kính chắn gió sạch.',
     'Chìa khoá thông minh, camera hành trình Vietmap.',
     'Khách yêu cầu lập báo giá nâng cấp ánh sáng trước khi thi công.', 2, '2026-11-13 10:35'),
]
for i, (oid, odo, fuel, ext, acc, note, by, created) in enumerate(intake_records, 1):
    w('INSERT INTO intake_records (id, repair_order_id, odometer_at_intake, fuel_level,'
      ' exterior_condition, accessories, notes, created_by, created_at) VALUES')
    w('  (%d, %d, %d, %s, %s, %s, %s, %d, %s);' % (
        i, oid, odo, q(fuel), q(ext), q(acc), q(note), by, q(created)))
w()

w('-- ---------------------------------------------------------------------------')
w('-- 16. Báo giá chính thức (quotations & quotation_items): 3 bản ghi mẫu')
w('--     Phiếu 1: APPROVED & đã áp dụng; Phiếu 10: APPROVED; Phiếu 11: SENT')
w('-- ---------------------------------------------------------------------------')
quotations = [
    (1,  1,  'APPROVED', 'Báo giá bảo dưỡng định kỳ 6 tháng (đã duyệt & áp dụng).',
     '2026-03-01', 1170000, 2, 1, '2026-02-14 09:30', '2026-02-14 09:22', '2026-02-14 09:35', 1),
    (2,  10, 'APPROVED', 'Báo giá nâng cấp đèn pha LED H7 cho xe 30C-3334.',
     '2026-11-30', 6100000, 2, 1, '2026-11-12 09:40', '2026-11-12 09:25', '2026-11-12 09:45', 1),
    (3,  11, 'SENT',     'Báo giá gói nâng cấp ánh sáng & vệ sinh khoang máy xe 30E-5556.',
     '2026-11-30', 6600000, 2, None, None, '2026-11-13 10:40', None, None),
]
for (qid, oid, st, note, valid, tot, cby, aby, aat, cat, app_at, app_by) in quotations:
    w('INSERT INTO quotations (id, repair_order_id, status, note, valid_until, total,'
      ' created_by, approved_by, approved_at, created_at, applied_at, applied_by) VALUES')
    w('  (%d, %d, %s, %s, %s, %d, %d, %s, %s, %s, %s, %s);' % (
        qid, oid, q(st), q(note), q(valid), tot, cby,
        str(aby) if aby else 'NULL', q(aat), q(cat), q(app_at),
        str(app_by) if app_by else 'NULL'))
w()

quotation_items = [
    (1, 1,  1,    None, 1, 450000),
    (2, 1,  None, 1,    4, 180000),
    (3, 2,  7,    None, 2, 2400000),
    (4, 2,  None, 12,   2, 650000),
    (5, 3,  7,    None, 1, 2400000),
    (6, 3,  None, 12,   6, 650000),
    (7, 3,  8,    None, 1, 300000),
]
for (qi_id, qid, sid, pid, qty, up) in quotation_items:
    w('INSERT INTO quotation_items (id, quotation_id, service_id, part_id, qty, unit_price) VALUES')
    w('  (%d, %d, %s, %s, %d, %d);' % (
        qi_id, qid, str(sid) if sid else 'NULL', str(pid) if pid else 'NULL', qty, up))
w()

w('COMMIT;')
w()

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(L) + '\n')

print('Đã ghi %s (%d dòng)' % (OUT, len(L)))
print('Mật khẩu demo: %s' % DEMO_PASSWORD)
print('Tổng tiền hoá đơn:')
for oid, t in sorted(order_totals.items()):
    print('   phiếu %-2d -> %10s đồng' % (oid, format(t, ',').replace(',', '.')))