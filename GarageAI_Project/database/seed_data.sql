-- ===========================================================================
-- GarageTools AI  |  DỮ LIỆU MẪU
-- File   : database/seed_data.sql
-- Đặc tả : Báo cáo mục 4.5 - Dữ liệu mẫu cho bản demo
-- Mật khẩu demo chung: Garage@2026
--
-- Cảnh báo: đây là tài khoản dùng cho học tập và demo. Khi triển khai thật
-- phải đổi toàn bộ mật khẩu (xem mục 16.16 của báo cáo).
--
-- Các tình huống cố ý tạo ra để phục vụ kiểm thử:
--   * Xe 30A-1111 có 5 lần sửa chữa  -> dữ liệu cho AI tóm tắt lịch sử
--   * Phiếu 12 chưa có hạng mục        -> báo giá nháp rỗng
--   * Dịch vụ 7 không có mô tả        -> AI giải thích gặp dữ liệu thiếu
--   * Phụ tùng 9 tồn kho bằng 0       -> kiểm thử giới hạn tồn kho
--   * Hoá đơn 10 chưa thu, 11 thu một phần -> kiểm thử thanh toán
--   * Hai lịch hẹn 9 và 10 trùng giờ, cùng xe -> kiểm thử phát hiện trùng
-- ===========================================================================

PRAGMA foreign_keys = ON;
BEGIN TRANSACTION;

-- ---------------------------------------------------------------------------
-- 1. Tài khoản: 4 vai trò nghiệp vụ
-- ---------------------------------------------------------------------------
INSERT INTO users (id, username, password_hash, full_name, email, role, auth_version) VALUES
  (1, 'quan_ly', 'pbkdf2_sha256$200000$970fcaa780dad97f$9de7efee8cfe13fdd963907d92c1bc8b77f979e0db13536f8a8a0ab82db70df2', 'Nguyễn Quang Huy', 'huy.nguyen@garage.vn', 'MANAGER', 1);
INSERT INTO users (id, username, password_hash, full_name, email, role, auth_version) VALUES
  (2, 'le_tan', 'pbkdf2_sha256$200000$08e6ece5db225665$6962803e5b808fe2b3ffa76bd82b369ba54fd89d2f6d1c349ac6392b0f3fbcf5', 'Trần Thu Hà', 'ha.tran@garage.vn', 'RECEPTIONIST', 1);
INSERT INTO users (id, username, password_hash, full_name, email, role, auth_version) VALUES
  (3, 'ky_thuat_vien', 'pbkdf2_sha256$200000$ed697acd68b6b205$fb1eef87c1c3a1837968a38fb5e10bff1e27733c71cab80ceee30af56372c8bc', 'Lê Minh Đức', 'duc.le@garage.vn', 'TECHNICIAN', 1);
INSERT INTO users (id, username, password_hash, full_name, email, role, auth_version) VALUES
  (4, 'thu_ngan', 'pbkdf2_sha256$200000$c264ef2490acdbe1$cfbec5c7b7932bacf1478aae831a4ca9d4253826b7d1d61243b28811aba9bb02', 'Phạm Thu Hà', 'ha.pham@garage.vn', 'CASHIER', 1);

-- ---------------------------------------------------------------------------
-- 2. Khách hàng: 10
-- ---------------------------------------------------------------------------
INSERT INTO customers (id, name, phone, email, address) VALUES
  (1, 'Nguyễn Văn An', '0901000001', 'an.nguyen@gmail.com', '12 Nguyễn Huệ, Hà Nội');
INSERT INTO customers (id, name, phone, email, address) VALUES
  (2, 'Trần Thị Bình', '0901000002', 'binh.tran@gmail.com', '45 Lê Lợi, Hà Nội');
INSERT INTO customers (id, name, phone, email, address) VALUES
  (3, 'Lê Quang Cường', '0901000003', 'cuong.le@gmail.com', '78 Hai Bà Trưng, Hà Nội');
INSERT INTO customers (id, name, phone, email, address) VALUES
  (4, 'Phạm Thị Dung', '0901000004', 'dung.pham@gmail.com', '23 Cầu Giấy, Hà Nội');
INSERT INTO customers (id, name, phone, email, address) VALUES
  (5, 'Đỗ Hữu Giang', '0901000005', 'giang.do@gmail.com', '5 Tây Sơn, Hà Nội');
INSERT INTO customers (id, name, phone, email, address) VALUES
  (6, 'Vũ Thị Hà', '0901000006', 'ha.vu@gmail.com', '91 Ba Đình, Hà Nội');
INSERT INTO customers (id, name, phone, email, address) VALUES
  (7, 'Hoàng Minh Khôi', '0901000007', 'khoi.hoang@gmail.com', '30 Giải Phóng, Hà Nội');
INSERT INTO customers (id, name, phone, email, address) VALUES
  (8, 'Ngô Thị Lan', '0901000008', 'lan.ngo@gmail.com', '17 Tràng Bông, Hà Nội');
INSERT INTO customers (id, name, phone, email, address) VALUES
  (9, 'Bùi Văn Long', '0901000009', 'long.bui@gmail.com', '64 Giải Phóng, Hà Nội');
INSERT INTO customers (id, name, phone, email, address) VALUES
  (10, 'Đặng Thị Mai', '0901000010', 'mai.dang@gmail.com', '8 Láng, Hà Nội');

-- ---------------------------------------------------------------------------
-- 3. Xe: 12
-- ---------------------------------------------------------------------------
INSERT INTO vehicles (id, customer_id, plate, brand, model, year) VALUES
  (1, 1, '30A-1111', 'Toyota', 'Vios', 2019);
INSERT INTO vehicles (id, customer_id, plate, brand, model, year) VALUES
  (2, 1, '30A-1112', 'Honda', 'Civic', 2020);
INSERT INTO vehicles (id, customer_id, plate, brand, model, year) VALUES
  (3, 2, '30B-2222', 'Mazda', 'CX-5', 2021);
INSERT INTO vehicles (id, customer_id, plate, brand, model, year) VALUES
  (4, 2, '30B-2223', 'Ford', 'Ranger', 2018);
INSERT INTO vehicles (id, customer_id, plate, brand, model, year) VALUES
  (5, 3, '30C-3333', 'Hyundai', 'Tucson', 2022);
INSERT INTO vehicles (id, customer_id, plate, brand, model, year) VALUES
  (6, 3, '30C-3334', 'Kia', 'Cerato', 2020);
INSERT INTO vehicles (id, customer_id, plate, brand, model, year) VALUES
  (7, 4, '30D-4444', 'Nissan', 'X-Trail', 2019);
INSERT INTO vehicles (id, customer_id, plate, brand, model, year) VALUES
  (8, 4, '30D-4445', 'Suzuki', 'Vitara', 2021);
INSERT INTO vehicles (id, customer_id, plate, brand, model, year) VALUES
  (9, 5, '30E-5555', 'Lexus', 'ES350', 2017);
INSERT INTO vehicles (id, customer_id, plate, brand, model, year) VALUES
  (10, 5, '30E-5556', 'Mercedes', 'C200', 2020);
INSERT INTO vehicles (id, customer_id, plate, brand, model, year) VALUES
  (11, 6, '30F-6666', 'Chevrolet', 'Cruze', 2018);
INSERT INTO vehicles (id, customer_id, plate, brand, model, year) VALUES
  (12, 7, '30G-7777', 'BMW', 'X3', 2021);

-- ---------------------------------------------------------------------------
-- 4. Dịch vụ: 8 (dịch vụ 7 cố ý không có mô tả)
-- ---------------------------------------------------------------------------
INSERT INTO services (id, name, description, price) VALUES
  (1, 'Thay dầu máy và lọc gió', 'Thay dầu máy định kỳ kèm thay lọc gió, kiểm tra mức dầu và vòng quay.', 450000);
INSERT INTO services (id, name, description, price) VALUES
  (2, 'Thay phuộc trước', 'Thay cặp phuộc trước kèm cân bằng bánh xe.', 1200000);
INSERT INTO services (id, name, description, price) VALUES
  (3, 'Sửa phanh', 'Kiểm tra má phanh, đĩa phanh và thay thế linh kiện hư hỏng.', 650000);
INSERT INTO services (id, name, description, price) VALUES
  (4, 'Thay máy phát điện', 'Thay ắc quy và kiểm tra hệ thống điện của xe.', 5500000);
INSERT INTO services (id, name, description, price) VALUES
  (5, 'Bảo dưỡng động cơ', 'Kiểm tra tổng thể động cơ, thay dầu bộ lọc và các nước.', 1800000);
INSERT INTO services (id, name, description, price) VALUES
  (6, 'Thay lốp và cân bằng', 'Thay lốp, kiểm tra áp suất và cân bằng bánh xe.', 300000);
INSERT INTO services (id, name, description, price) VALUES
  (7, 'Nâp cấp ánh sáng', NULL, 2400000);
INSERT INTO services (id, name, description, price) VALUES
  (8, 'Vệ sinh khoang máy và nội thất', 'Vệ sinh toàn bộ khoang lái xe và thảm lót.', 300000);

-- ---------------------------------------------------------------------------
-- 5. Phụ tùng: 15 (phụ tùng 9 cố ý hết hàng)
-- ---------------------------------------------------------------------------
INSERT INTO parts (id, name, sku, stock, min_stock, price, description) VALUES
  (1, 'Dầu động cơ 5W-30 (1 lít)', 'PT-001', 120, 5, 180000, NULL);
INSERT INTO parts (id, name, sku, stock, min_stock, price, description) VALUES
  (2, 'Lọc gió động cơ', 'PT-002', 60, 5, 85000, NULL);
INSERT INTO parts (id, name, sku, stock, min_stock, price, description) VALUES
  (3, 'Lọc dầu động cơ', 'PT-003', 70, 5, 120000, NULL);
INSERT INTO parts (id, name, sku, stock, min_stock, price, description) VALUES
  (4, 'Lọc gió cabin', 'PT-004', 90, 5, 95000, NULL);
INSERT INTO parts (id, name, sku, stock, min_stock, price, description) VALUES
  (5, 'Máy phát 12V 60Ah', 'PT-005', 15, 5, 3200000, NULL);
INSERT INTO parts (id, name, sku, stock, min_stock, price, description) VALUES
  (6, 'Ắc quy 70Ah', 'PT-006', 25, 5, 2500000, NULL);
INSERT INTO parts (id, name, sku, stock, min_stock, price, description) VALUES
  (7, 'Bộ má phanh trước', 'PT-007', 40, 5, 950000, NULL);
INSERT INTO parts (id, name, sku, stock, min_stock, price, description) VALUES
  (8, 'Đĩa phanh trước', 'PT-008', 35, 5, 780000, NULL);
INSERT INTO parts (id, name, sku, stock, min_stock, price, description) VALUES
  (9, 'Lốp xe 205/55R16', 'PT-009', 0, 2, 1350000, NULL);
INSERT INTO parts (id, name, sku, stock, min_stock, price, description) VALUES
  (10, 'Lốp xe 215/55R17', 'PT-010', 30, 5, 1650000, NULL);
INSERT INTO parts (id, name, sku, stock, min_stock, price, description) VALUES
  (11, 'Cặp phuộc trước', 'PT-011', 24, 5, 2800000, NULL);
INSERT INTO parts (id, name, sku, stock, min_stock, price, description) VALUES
  (12, 'Bóng đèn pha LED H7', 'PT-012', 80, 5, 650000, NULL);
INSERT INTO parts (id, name, sku, stock, min_stock, price, description) VALUES
  (13, 'Gương chiếu hậu trái', 'PT-013', 18, 5, 1450000, NULL);
INSERT INTO parts (id, name, sku, stock, min_stock, price, description) VALUES
  (14, 'Gương chiếu hậu phải', 'PT-014', 18, 5, 1450000, NULL);
INSERT INTO parts (id, name, sku, stock, min_stock, price, description) VALUES
  (15, 'Ga và chìa khóa điện', 'PT-015', 12, 5, 2100000, 'Ga và chìa khóa điện có mã, cần đăng kì cắt mới.');

-- ---------------------------------------------------------------------------
-- 5b. Số dư mở đầu kho (stock_transactions): mỗi phụ tùng tồn > 0 có đúng
--     một dòng ADJUSTMENT bằng đúng `parts.stock`. Bất biến
--     SUM(stock_transactions.qty) == parts.stock bắt đầu từ đây.
-- ---------------------------------------------------------------------------
INSERT INTO stock_transactions (id, part_id, qty, reason, note) VALUES
  (1, 1, 120, 'ADJUSTMENT', 'Số dư mở đầu khi khởi tạo hệ thống.');
INSERT INTO stock_transactions (id, part_id, qty, reason, note) VALUES
  (2, 2, 60, 'ADJUSTMENT', 'Số dư mở đầu khi khởi tạo hệ thống.');
INSERT INTO stock_transactions (id, part_id, qty, reason, note) VALUES
  (3, 3, 70, 'ADJUSTMENT', 'Số dư mở đầu khi khởi tạo hệ thống.');
INSERT INTO stock_transactions (id, part_id, qty, reason, note) VALUES
  (4, 4, 90, 'ADJUSTMENT', 'Số dư mở đầu khi khởi tạo hệ thống.');
INSERT INTO stock_transactions (id, part_id, qty, reason, note) VALUES
  (5, 5, 15, 'ADJUSTMENT', 'Số dư mở đầu khi khởi tạo hệ thống.');
INSERT INTO stock_transactions (id, part_id, qty, reason, note) VALUES
  (6, 6, 25, 'ADJUSTMENT', 'Số dư mở đầu khi khởi tạo hệ thống.');
INSERT INTO stock_transactions (id, part_id, qty, reason, note) VALUES
  (7, 7, 40, 'ADJUSTMENT', 'Số dư mở đầu khi khởi tạo hệ thống.');
INSERT INTO stock_transactions (id, part_id, qty, reason, note) VALUES
  (8, 8, 35, 'ADJUSTMENT', 'Số dư mở đầu khi khởi tạo hệ thống.');
INSERT INTO stock_transactions (id, part_id, qty, reason, note) VALUES
  (10, 10, 30, 'ADJUSTMENT', 'Số dư mở đầu khi khởi tạo hệ thống.');
INSERT INTO stock_transactions (id, part_id, qty, reason, note) VALUES
  (11, 11, 24, 'ADJUSTMENT', 'Số dư mở đầu khi khởi tạo hệ thống.');
INSERT INTO stock_transactions (id, part_id, qty, reason, note) VALUES
  (12, 12, 80, 'ADJUSTMENT', 'Số dư mở đầu khi khởi tạo hệ thống.');
INSERT INTO stock_transactions (id, part_id, qty, reason, note) VALUES
  (13, 13, 18, 'ADJUSTMENT', 'Số dư mở đầu khi khởi tạo hệ thống.');
INSERT INTO stock_transactions (id, part_id, qty, reason, note) VALUES
  (14, 14, 18, 'ADJUSTMENT', 'Số dư mở đầu khi khởi tạo hệ thống.');
INSERT INTO stock_transactions (id, part_id, qty, reason, note) VALUES
  (15, 15, 12, 'ADJUSTMENT', 'Số dư mở đầu khi khởi tạo hệ thống.');

-- ---------------------------------------------------------------------------
-- 6. Lịch hẹn: 10
-- ---------------------------------------------------------------------------
INSERT INTO appointments (id, customer_id, vehicle_id, scheduled_at, notes, status) VALUES
  (1, 1, 1, '2026-11-20 09:00', 'Bảo dưỡng định kỳ trước mùa lạ.', 'CONFIRMED');
INSERT INTO appointments (id, customer_id, vehicle_id, scheduled_at, notes, status) VALUES
  (2, 1, 2, '2026-11-21 14:30', 'Thay phuộc sau khi khách báo rung phía trước.', 'SCHEDULED');
INSERT INTO appointments (id, customer_id, vehicle_id, scheduled_at, notes, status) VALUES
  (3, 2, 3, '2026-11-22 10:15', 'Kiểm tra hệ thống phanh.', 'SCHEDULED');
INSERT INTO appointments (id, customer_id, vehicle_id, scheduled_at, notes, status) VALUES
  (4, 2, 4, '2026-11-23 08:00', 'Thay dầu máy.', 'CONFIRMED');
INSERT INTO appointments (id, customer_id, vehicle_id, scheduled_at, notes, status) VALUES
  (5, 3, 5, '2026-11-23 16:00', 'Kiểm tra lỗi đèn pha.', 'SCHEDULED');
INSERT INTO appointments (id, customer_id, vehicle_id, scheduled_at, notes, status) VALUES
  (6, 4, 7, '2026-11-24 13:45', 'Thay máy phát.', 'SCHEDULED');
INSERT INTO appointments (id, customer_id, vehicle_id, scheduled_at, notes, status) VALUES
  (7, 4, 8, '2026-11-25 09:30', 'Thay lốp định kỳ.', 'SCHEDULED');
INSERT INTO appointments (id, customer_id, vehicle_id, scheduled_at, notes, status) VALUES
  (8, 5, 9, '2026-11-26 11:00', 'Kiểm tra hệ thống điện.', 'CONFIRMED');
INSERT INTO appointments (id, customer_id, vehicle_id, scheduled_at, notes, status) VALUES
  (9, 6, 11, '2026-11-27 15:00', 'Vệ sinh xe sau chuyến đi dài.', 'SCHEDULED');
INSERT INTO appointments (id, customer_id, vehicle_id, scheduled_at, notes, status) VALUES
  (10, 6, 11, '2026-11-27 15:00', 'Ghi thêm yêu cầu vệ sinh ghế.', 'SCHEDULED');

-- ---------------------------------------------------------------------------
-- 7. Phiếu sửa chữa: 12, phủ đủ sáu trạng thái
-- ---------------------------------------------------------------------------
INSERT INTO repair_orders (id, vehicle_id, technician_id, status, technical_notes, created_at) VALUES
  (1, 1, 3, 'COMPLETED', 'Thay dầu, lọc gió. Khách định kỳ 6 tháng.', '2026-02-14 09:20');
INSERT INTO repair_orders (id, vehicle_id, technician_id, status, technical_notes, created_at) VALUES
  (2, 1, 3, 'COMPLETED', 'Thay máy phát. Xe khởi động yếu khi trời lạnh.', '2026-04-03 10:05');
INSERT INTO repair_orders (id, vehicle_id, technician_id, status, technical_notes, created_at) VALUES
  (3, 1, 3, 'COMPLETED', 'Sửa phanh sau. Có tiếng rít khi phanh lùi.', '2026-06-21 14:40');
INSERT INTO repair_orders (id, vehicle_id, technician_id, status, technical_notes, created_at) VALUES
  (4, 1, 3, 'COMPLETED', 'Thay lốp trước và sau, cân bằng bánh xe.', '2026-08-30 08:50');
INSERT INTO repair_orders (id, vehicle_id, technician_id, status, technical_notes, created_at) VALUES
  (5, 1, 3, 'COMPLETED', 'Bảo dưỡng động cơ, thay dầu bộ lọc.', '2026-10-18 11:30');
INSERT INTO repair_orders (id, vehicle_id, technician_id, status, technical_notes, created_at) VALUES
  (6, 2, 3, 'COMPLETED', 'Thay phuộc trước.', '2026-03-11 09:00');
INSERT INTO repair_orders (id, vehicle_id, technician_id, status, technical_notes, created_at) VALUES
  (7, 3, 3, 'CANCELLED', 'Khách huỷ lịch sau khi đã thay lọc gió cabin.', '2026-05-22 15:10');
INSERT INTO repair_orders (id, vehicle_id, technician_id, status, technical_notes, created_at) VALUES
  (8, 5, 3, 'COMPLETED', 'Sửa phanh trước, thay má và đĩa phanh.', '2026-07-09 10:40');
INSERT INTO repair_orders (id, vehicle_id, technician_id, status, technical_notes, created_at) VALUES
  (9, 9, 3, 'COMPLETED', 'Thay máy phát và ắc quy.', '2026-09-02 13:20');
INSERT INTO repair_orders (id, vehicle_id, technician_id, status, technical_notes, created_at) VALUES
  (10, 6, 3, 'REPAIRING', 'Đang thay bóng đèn pha LED.', '2026-11-12 09:15');
INSERT INTO repair_orders (id, vehicle_id, technician_id, status, technical_notes, created_at) VALUES
  (11, 10, 3, 'ESTIMATING', 'Chờ duyệt báo giá nâng cấp ánh sáng.', '2026-11-13 10:30');
INSERT INTO repair_orders (id, vehicle_id, technician_id, status, technical_notes, created_at) VALUES
  (12, 11, 3, 'RECEIVED', 'Khách báo gương chiếu hậu bị trầy, chờ tiếp nhận.', '2026-11-14 16:45');

-- ---------------------------------------------------------------------------
-- 8. Hạng mục: 25. unit_price chốt đúng bằng giá tại thời điểm thêm
-- ---------------------------------------------------------------------------
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (1, 1, 1, NULL, 1, 450000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (2, 1, NULL, 1, 4, 180000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (3, 2, 4, NULL, 1, 5500000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (4, 2, NULL, 5, 1, 3200000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (5, 3, 3, NULL, 2, 650000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (6, 3, NULL, 7, 2, 950000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (7, 4, 6, NULL, 4, 300000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (8, 4, NULL, 9, 4, 1350000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (9, 5, 5, NULL, 1, 1800000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (10, 5, NULL, 2, 1, 85000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (11, 5, NULL, 3, 1, 120000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (12, 6, 2, NULL, 2, 1200000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (13, 7, 8, NULL, 1, 300000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (14, 7, NULL, 4, 1, 95000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (15, 8, 3, NULL, 1, 650000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (16, 8, NULL, 7, 1, 950000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (17, 8, NULL, 8, 2, 780000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (18, 9, 4, NULL, 1, 5500000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (19, 9, NULL, 6, 1, 2500000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (20, 10, 7, NULL, 2, 2400000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (21, 10, NULL, 12, 2, 650000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (22, 11, 7, NULL, 1, 2400000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (23, 11, NULL, 12, 4, 650000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (24, 11, NULL, 12, 2, 650000);
INSERT INTO repair_order_items (id, repair_order_id, service_id, part_id, qty, unit_price) VALUES
  (25, 11, 8, NULL, 1, 300000);

-- ---------------------------------------------------------------------------
-- 9. Nhật ký kỹ thuật: 20
-- ---------------------------------------------------------------------------
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (1, 1, 3, 'Tiếp nhận, kiểm tra mức dầu trong bình. Mức dầu thấp hơn mốc.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (2, 1, 3, 'Thay dầu mới và lọc gió. Kiểm tra không rò rỉ sau khi thay.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (3, 2, 3, 'Đo áp bình ắc quy: 11.4V, dưới ngưỡng. Đề xuất thay máy phát.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (4, 2, 3, 'Thay máy phát mới. Sạc lại bình và kiểm tra hệ thống điện.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (5, 3, 3, 'Khách báo tiếng rít khi phanh lùi. Kiểm tra má phanh bị mòn.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (6, 3, 3, 'Thay má phanh trước. Độ dày sau thay nằm trong giới hạn.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (7, 4, 3, 'Kiểm tra áp suất bốn lốp. Hai lốp trước dưới ngưỡng.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (8, 4, 3, 'Thay bốn lốp và cân bằng. Kiểm tra van và lông vô tuyến không hỏng.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (9, 5, 3, 'Kiểm tra tổng thể động cơ, không thấy rò rỉ dầu.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (10, 5, 3, 'Thay dầu động cơ và bộ lọc dầu. Khuyến nghị thay dầu sau 6 tháng.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (11, 6, 3, 'Kiểm tra chơi phuộc, cần thay cả cặp trước.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (12, 7, 3, 'Vệ sinh khoang lái xe và thay lọc gió cabin.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (13, 8, 3, 'Đĩa phán mòn đến mức tối thiểu, phải thay.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (14, 8, 3, 'Thay má phanh trước và đĩa phanh trước. Đã đường xem lại.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (15, 9, 3, 'Ắc quy xuống cạn, đề xuất thay cả máy phát và ắc quy.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (16, 9, 3, 'Thay máy phát và ắc quy. Kiểm tra sạc ổn định.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (17, 10, 3, 'Đèn pha bị vàng do bóng cháy. Cần nâng cấp bộ đèn.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (18, 10, 3, 'Đang chờ khách duyệt báo giá trước khi lắp đèn.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (19, 11, 3, 'Khách muốn nâng cấp ánh sáng, cần báo giá nháp.');
INSERT INTO repair_logs (id, repair_order_id, technician_id, note) VALUES
  (20, 12, 3, 'Gương chiếu hậu bị trầy xước, chờ tiếp nhận và báo giá.');

-- ---------------------------------------------------------------------------
-- 10. Hoá đơn: 8 (6 đã thu đủ, 1 chưa thu, 1 thu một phần)
--     total = tổng unit_price x qty của hạng mục thuộc phiếu, do backend tính
-- ---------------------------------------------------------------------------
INSERT INTO invoices (id, repair_order_id, total, paid, status, created_at) VALUES
  (1, 1, 1170000, 1170000, 'PAID', '2026-02-14 09:20');
INSERT INTO invoices (id, repair_order_id, total, paid, status, created_at) VALUES
  (2, 2, 8700000, 8700000, 'PAID', '2026-04-03 10:05');
INSERT INTO invoices (id, repair_order_id, total, paid, status, created_at) VALUES
  (3, 3, 3200000, 3200000, 'PAID', '2026-06-21 14:40');
INSERT INTO invoices (id, repair_order_id, total, paid, status, created_at) VALUES
  (4, 5, 2005000, 2005000, 'PAID', '2026-10-18 11:30');
INSERT INTO invoices (id, repair_order_id, total, paid, status, created_at) VALUES
  (5, 8, 3160000, 3160000, 'PAID', '2026-07-09 10:40');
INSERT INTO invoices (id, repair_order_id, total, paid, status, created_at) VALUES
  (6, 9, 8000000, 8000000, 'PAID', '2026-09-02 13:20');
INSERT INTO invoices (id, repair_order_id, total, paid, status, created_at) VALUES
  (7, 10, 6100000, 0, 'UNPAID', '2026-11-12 09:15');
INSERT INTO invoices (id, repair_order_id, total, paid, status, created_at) VALUES
  (8, 11, 6600000, 3300000, 'PARTIAL', '2026-11-13 10:30');

-- ---------------------------------------------------------------------------
-- 11. Thanh toán: 8
-- ---------------------------------------------------------------------------
INSERT INTO payments (id, invoice_id, amount, method, paid_at) VALUES
  (1, 1, 585000, 'CASH', '2026-02-14 09:20');
INSERT INTO payments (id, invoice_id, amount, method, paid_at) VALUES
  (2, 1, 585000, 'TRANSFER', '2026-02-14 09:20');
INSERT INTO payments (id, invoice_id, amount, method, paid_at) VALUES
  (3, 2, 8700000, 'CASH', '2026-04-03 10:05');
INSERT INTO payments (id, invoice_id, amount, method, paid_at) VALUES
  (4, 3, 3200000, 'CARD', '2026-06-21 14:40');
INSERT INTO payments (id, invoice_id, amount, method, paid_at) VALUES
  (5, 4, 2005000, 'CASH', '2026-10-18 11:30');
INSERT INTO payments (id, invoice_id, amount, method, paid_at) VALUES
  (6, 5, 3160000, 'TRANSFER', '2026-07-09 10:40');
INSERT INTO payments (id, invoice_id, amount, method, paid_at) VALUES
  (7, 6, 8000000, 'CARD', '2026-09-02 13:20');
INSERT INTO payments (id, invoice_id, amount, method, paid_at) VALUES
  (8, 8, 3300000, 'ZALO', '2026-11-13 10:30');

-- ---------------------------------------------------------------------------
-- 12. Kết quả AI: 6 (mỗi chức năng 1 kết quả đã duyệt, 1 kết quả chờ duyệt)
-- ---------------------------------------------------------------------------
INSERT INTO ai_results (id, kind, repair_order_id, input_json, output_text, is_valid, review_status, reviewed_by, reviewed_at) VALUES
  (1, 'history', 1, '{"repair_order_id": 1, "nguon": "seed_data"}', 'Xe 30A-1111 Toyota Vios đã sửa chữa 5 lần gần nhất.
1. 14/02/2026: Thay dầu máy và lọc gió - hoàn tất
2. 03/04/2026: Thay máy phát điện - hoàn tất
3. 21/06/2026: Sửa phanh - hoàn tất
4. 30/08/2026: Thay lốp và cân bằng - hoàn tất
5. 18/10/2026: Bảo dưỡng động cơ - hoàn tất
Dữ liệu thiếu: Không có', 1, 'APPROVED', 2, '2026-11-15 09:00:00');
INSERT INTO ai_results (id, kind, repair_order_id, input_json, output_text, is_valid, review_status) VALUES
  (2, 'history', 12, '{"repair_order_id": 12, "nguon": "seed_data"}', 'Xe 30F-6666 Chevrolet Cruze chưa có lịch sử sửa chữa nào trong hệ thống.', 0, 'PENDING');
INSERT INTO ai_results (id, kind, repair_order_id, input_json, output_text, is_valid, review_status, reviewed_by, reviewed_at) VALUES
  (3, 'explain', 1, '{"repair_order_id": 1, "nguon": "seed_data"}', '1. Dịch vụ là gì: Thay dầu máy và lọc gió là hạng mục bảo dưỡng định kỳ, gồm thay dầu máy và thay bộ lọc gió để động cơ bớt hao mòn.
2. Hạng mục đang ghi nhận: Thay dầu máy và lọc gió; Dầu động cơ 5W-30.
3. Khách cần lưu ý: Chi phí dự kiến 1.080.000 đồng.', 1, 'APPROVED', 2, '2026-11-15 09:00:00');
INSERT INTO ai_results (id, kind, repair_order_id, input_json, output_text, is_valid, review_status) VALUES
  (4, 'explain', 7, '{"repair_order_id": 7, "nguon": "seed_data"}', '1. Dịch vụ là gì: Danh mục chưa có mô tả cho dịch vụ này.
2. Hạng mục đang ghi nhận: Nâng cấp ánh sáng.
3. Khách cần lưu ý: Không có', 0, 'PENDING');
INSERT INTO ai_results (id, kind, repair_order_id, input_json, output_text, is_valid, review_status, reviewed_by, reviewed_at) VALUES
  (5, 'quote', 10, '{"repair_order_id": 10, "nguon": "seed_data"}', 'Bảng báo giá nháp cho phiếu sửa chữa số 10.
- Nâng cấp ánh sáng x 2: 4.800.000
- Bóng đèn pha LED H7 x 2: 1.300.000
Tổng dự kiến: 6.100.000
Báo giá nháp, cần nhân viên kiểm tra trước khi sử dụng.', 1, 'APPROVED', 1, '2026-11-15 09:00:00');
INSERT INTO ai_results (id, kind, repair_order_id, input_json, output_text, is_valid, review_status) VALUES
  (6, 'quote', 12, '{"repair_order_id": 12, "nguon": "seed_data"}', 'Phiếu sửa chữa số 12 chưa có hạng mục nào được ghi nhận nên chưa thể lập báo giá nháp.', 0, 'PENDING');

-- ---------------------------------------------------------------------------
-- 13. Cửa hàng dụng cụ (MỞ RỘNG, ngoài phạm vi đề tài)
--     6 danh mục, 20 sản phẩm, 2 đơn hàng
-- ---------------------------------------------------------------------------
INSERT INTO shop_categories (id, name, slug) VALUES (1, 'Dụng cụ tay', 'dung-cu-tay');
INSERT INTO shop_categories (id, name, slug) VALUES (2, 'Dụng cụ điện', 'dung-cu-dien');
INSERT INTO shop_categories (id, name, slug) VALUES (3, 'Thiết bị kiểm tra', 'thiet-bi-kiem-tra');
INSERT INTO shop_categories (id, name, slug) VALUES (4, 'Dầu bôi trục và vòng bi', 'dau-boi-truc');
INSERT INTO shop_categories (id, name, slug) VALUES (5, 'Phụ kiện và vỏ xe', 'phu-kien');
INSERT INTO shop_categories (id, name, slug) VALUES (6, 'Dụng cụ chuyên dụng', 'dung-cu-chuyen-dung');

INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (1, 1, 'Bộ khoá vặn 12 chiếc', 'DCV-001', 380000, 25, 'Khoá vặn từ 8 đến 19 mm, đúc thép crôm.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (2, 1, 'Bộ khoá vặn lục giác 9 chiếc', 'DCV-002', 260000, 30, 'Khoá lục giác chuẩn, có đầu cầu.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (3, 1, 'Kìm cuối 8 inch', 'DCV-003', 145000, 45, 'Kìm cuối cách điện.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (4, 1, 'Búa móng ngựa 16 ounce', 'DCV-004', 320000, 18, 'Búa đầu thép, cán gỗ.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (5, 1, 'Xô 20 lít có nắp', 'DCV-005', 85000, 60, 'Xô nhựa HDPE dùng để chứa nhớt thải.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (6, 2, 'Máy khoan bê tông', 'DCD-001', 2450000, 8, 'Công suất 800W, kèm đầu khoan và mũi khoan.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (7, 2, 'Máy mài góc 100mm', 'DCD-002', 1680000, 12, 'Dùng để cắt và mài bề mặt kim loại.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (8, 2, 'Máy hàn thiếc 60W', 'DCD-003', 560000, 20, 'Hàn mạch điện và dây.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (9, 2, 'Đầu khoan từ 3 đến 10mm', 'DCD-004', 210000, 50, 'Bộ 8 đầu khoan, chuẩn côn chuẩn.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (10, 2, 'Đèn pin LED 1000W', 'DCD-005', 1200000, 14, 'Đèn chiếu sáng góc rộng, pin sạc.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (11, 3, 'Máy đo áp suất lốp', 'TBK-001', 890000, 22, 'Đo áp suất bằng đồng hồ, hiển thị kPa và psi.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (12, 3, 'Bộ dụng cụ chẩn đoán OBD', 'TBK-002', 950000, 16, 'Đọc mã lỗi ECU qua cổng OBD-II.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (13, 3, 'Máy đo áp lốp', 'TBK-003', 420000, 26, 'Đo áp suất lốp kỹ thuật số.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (14, 3, 'Đầu đo nhiệt độ dầu', 'TBK-004', 680000, 11, 'Cảm biến và màn hình hiển thị.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (15, 4, 'Mỡ chịu nhiệt 400g', 'DBT-001', 92000, 70, 'Mỡ cầu hữu cơ chịu nhiệt cao.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (16, 4, 'Dầu bôi trục 1 lít', 'DBT-002', 165000, 55, 'Dầu bôi trục và vòng bi chất lượng cao.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (17, 4, 'Bóng đèn pha LED H7', 'DBT-003', 650000, 35, 'Cặp bóng đèn LED trắng.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (18, 5, 'Gương chiếu hậu trái xe ô tô', 'PKC-001', 1450000, 10, 'Gương điện, có đèn báo rẽ.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (19, 6, 'Bọt rửa xe ô tô 5 lít', 'DCC-001', 155000, 40, 'Bọt rửa xe tạo nhiều bọt, không vết.');
INSERT INTO shop_products (id, category_id, name, sku, price, stock, description) VALUES
  (20, 6, 'Khăn lau xe chuyên dụng 30x50', 'DCC-002', 45000, 90, 'Sợi microfiber, hút nước tốt.');

INSERT INTO shop_orders (id, customer_name, phone, address, total, status) VALUES
  (1, 'Nguyễn Văn An', '0901000001', '12 Nguyễn Huệ, Hà Nội', 1750000, 'PAID');
INSERT INTO shop_orders (id, customer_name, phone, address, total, status) VALUES
  (2, 'Phạm Thị Dung', '0901000004', '23 Cầu Giấy, Hà Nội', 425000, 'PENDING');

INSERT INTO shop_order_items (id, order_id, product_id, qty, unit_price) VALUES
  (1, 1, 1, 1, 380000);
INSERT INTO shop_order_items (id, order_id, product_id, qty, unit_price) VALUES
  (2, 1, 13, 1, 420000);
INSERT INTO shop_order_items (id, order_id, product_id, qty, unit_price) VALUES
  (3, 1, 18, 1, 950000);
INSERT INTO shop_order_items (id, order_id, product_id, qty, unit_price) VALUES
  (4, 2, 3, 2, 145000);
INSERT INTO shop_order_items (id, order_id, product_id, qty, unit_price) VALUES
  (5, 2, 20, 3, 45000);

-- ---------------------------------------------------------------------------
-- 14. Bảo hành: 4 (SERVICE và PART đan xen, phủ đủ ACTIVE / EXPIRED)
--     Chỉ gắn với phiếu COMPLETED. scope XOR: SERVICE có service_id,
--     PART có part_id — đúng một trong hai.
-- ---------------------------------------------------------------------------
INSERT INTO warranties (id, repair_order_id, scope, service_id, part_id, months, start_date, end_date, status, note) VALUES
  (1, 1, 'SERVICE', 1, NULL, 6, '2026-02-14', '2026-08-14', 'EXPIRED', 'Bảo hành thay dầu động cơ 6 tháng.');
INSERT INTO warranties (id, repair_order_id, scope, service_id, part_id, months, start_date, end_date, status, note) VALUES
  (2, 2, 'PART', NULL, 5, 12, '2026-04-03', '2027-04-03', 'ACTIVE', 'Bảo hành máy phát ắc quy 12 tháng.');
INSERT INTO warranties (id, repair_order_id, scope, service_id, part_id, months, start_date, end_date, status, note) VALUES
  (3, 5, 'SERVICE', 5, NULL, 3, '2026-10-18', '2027-01-18', 'ACTIVE', 'Bảo hành bảo dưỡng định kỳ 3 tháng.');
INSERT INTO warranties (id, repair_order_id, scope, service_id, part_id, months, start_date, end_date, status, note) VALUES
  (4, 8, 'PART', NULL, 7, 6, '2026-07-09', '2027-01-09', 'ACTIVE', 'Bảo hành má phanh trước 6 tháng.');

-- ---------------------------------------------------------------------------
-- 15. Biên bản tiếp nhận (intake_records): 3 bản ghi mẫu cho phiếu 1, 10, 11
-- ---------------------------------------------------------------------------
INSERT INTO intake_records (id, repair_order_id, odometer_at_intake, fuel_level, exterior_condition, accessories, notes, created_by, created_at) VALUES
  (1, 1, 48500, 'THREE_QUARTER', 'Sơn zin đều, vết xước nhẹ cản sau bên phải.', 'Chìa khoá thông minh, lốp dự phòng, bộ kích theo xe.', 'Khách yêu cầu kiểm tra kỹ mức dầu và lọc gió.', 2, '2026-02-14 09:25');
INSERT INTO intake_records (id, repair_order_id, odometer_at_intake, fuel_level, exterior_condition, accessories, notes, created_by, created_at) VALUES
  (2, 10, 62300, 'HALF', 'Cụm đèn pha trước ố vàng, thân vỏ không móp méo.', 'Chìa khoá cơ, thảm sàn cao su.', 'Tiếp nhận kiểm tra nâng cấp cụm đèn pha LED.', 2, '2026-11-12 09:20');
INSERT INTO intake_records (id, repair_order_id, odometer_at_intake, fuel_level, exterior_condition, accessories, notes, created_by, created_at) VALUES
  (3, 11, 35800, 'FULL', 'Ngoại thất nguyên vẹn, kính chắn gió sạch.', 'Chìa khoá thông minh, camera hành trình Vietmap.', 'Khách yêu cầu lập báo giá nâng cấp ánh sáng trước khi thi công.', 2, '2026-11-13 10:35');

-- ---------------------------------------------------------------------------
-- 16. Báo giá chính thức (quotations & quotation_items): 3 bản ghi mẫu
--     Phiếu 1: APPROVED & đã áp dụng; Phiếu 10: APPROVED; Phiếu 11: SENT
-- ---------------------------------------------------------------------------
INSERT INTO quotations (id, repair_order_id, status, note, valid_until, total, created_by, approved_by, approved_at, created_at, applied_at, applied_by) VALUES
  (1, 1, 'APPROVED', 'Báo giá bảo dưỡng định kỳ 6 tháng (đã duyệt & áp dụng).', '2026-03-01', 1170000, 2, 1, '2026-02-14 09:30', '2026-02-14 09:22', '2026-02-14 09:35', 1);
INSERT INTO quotations (id, repair_order_id, status, note, valid_until, total, created_by, approved_by, approved_at, created_at, applied_at, applied_by) VALUES
  (2, 10, 'APPROVED', 'Báo giá nâng cấp đèn pha LED H7 cho xe 30C-3334.', '2026-11-30', 6100000, 2, 1, '2026-11-12 09:40', '2026-11-12 09:25', '2026-11-12 09:45', 1);
INSERT INTO quotations (id, repair_order_id, status, note, valid_until, total, created_by, approved_by, approved_at, created_at, applied_at, applied_by) VALUES
  (3, 11, 'SENT', 'Báo giá gói nâng cấp ánh sáng & vệ sinh khoang máy xe 30E-5556.', '2026-11-30', 6600000, 2, NULL, NULL, '2026-11-13 10:40', NULL, NULL);

INSERT INTO quotation_items (id, quotation_id, service_id, part_id, qty, unit_price) VALUES
  (1, 1, 1, NULL, 1, 450000);
INSERT INTO quotation_items (id, quotation_id, service_id, part_id, qty, unit_price) VALUES
  (2, 1, NULL, 1, 4, 180000);
INSERT INTO quotation_items (id, quotation_id, service_id, part_id, qty, unit_price) VALUES
  (3, 2, 7, NULL, 2, 2400000);
INSERT INTO quotation_items (id, quotation_id, service_id, part_id, qty, unit_price) VALUES
  (4, 2, NULL, 12, 2, 650000);
INSERT INTO quotation_items (id, quotation_id, service_id, part_id, qty, unit_price) VALUES
  (5, 3, 7, NULL, 1, 2400000);
INSERT INTO quotation_items (id, quotation_id, service_id, part_id, qty, unit_price) VALUES
  (6, 3, NULL, 12, 6, 650000);
INSERT INTO quotation_items (id, quotation_id, service_id, part_id, qty, unit_price) VALUES
  (7, 3, 8, NULL, 1, 300000);

COMMIT;

