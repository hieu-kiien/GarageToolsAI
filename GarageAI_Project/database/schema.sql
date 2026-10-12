-- =============================================================================
-- GarageTools AI  |  CƠ SỞ DỮ LIỆU
-- File     : database/schema.sql
-- Đặc tả   : Báo cáo mục 4.2 (danh sách bảng) và mục 4.3 (ràng buộc dữ liệu)
-- Sơ đồ    : Hình 5 - Sơ đồ ERD
-- Engine   : SQLite 3
--
-- LƯU Ý QUAN TRỌNG VỀ TIỀN TỆ
--   Mọi cột tiền (price, total, paid, amount, unit_price) dùng INTEGER tính bằng
--   đồng, KHÔNG dùng số thực. Lý do: số thực gây sai số tiền làm tròn khi cộng
--   nhiều dòng. Backend chỉ chia để hiển thị, không chia trong CSDL.
--
-- LƯU Ý QUAN TRỌNG VỀ GIÁ
--   repair_order_items.unit_price là giá được CHỐT tại thời điểm thêm hạng mục,
--   không phải giá tra động từ bảng services hoặc parts. Nếu tra động, một lần
--   sửa giá dịch vụ sẽ làm thay đổi cả những hóa đơn đã phát hành trước đó.
--
-- LƯU Ý VỀ KHÓA NGOẠI
--   SQLite KHÔNG tự kiểm tra khóa ngoại. Ứng dụng PHẢI bật bằng câu lệnh:
--       PRAGMA foreign_keys = ON;
--   Ngay sau khi mở kết nối, trước mọi truy vấn.
--
--   Các khóa ngoại bảo vệ lịch sử giao dịch dùng ON DELETE RESTRICT (mặc định):
--   không cho xóa khách, xe, phiếu hoặc hạng mục đã phát sinh giao dịch. Muốn
--   ẩn bản ghi thì chuyển trạng thái, không xóa.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- =============================================================================
-- 1. users - tài khoản người dùng và vai trò
--    4 vai trò nghiệp vụ theo ma trận phân quyền tại mục 9.2
-- =============================================================================
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,          -- dạng thuật toán$số vòng$muối$hash, KHÔNG lưu mật khẩu thô
    full_name     TEXT    NOT NULL,
    email         TEXT,
    role          TEXT    NOT NULL
        CHECK (role IN ('MANAGER', 'RECEPTIONIST', 'TECHNICIAN', 'CASHIER')),
    is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    -- Tăng mỗi lần đổi mật khẩu hoặc khoá tài khoản: mọi phiên đang mở có
    -- auth_version cũ sẽ mất hiệu lực ngay ở lần kiểm tra kế tiếp.
    auth_version  INTEGER NOT NULL DEFAULT 1 CHECK (auth_version >= 1),
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_users_role ON users(role);

-- =============================================================================
-- 2. customers - khách hàng
-- =============================================================================
CREATE TABLE customers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    phone      TEXT    NOT NULL UNIQUE,
    email      TEXT,
    address    TEXT,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customers_name  ON customers(name);

-- =============================================================================
-- 3. vehicles - phương tiện
--    plate là định danh tra cứu, có UNIQUE để chặn biển số trùng
-- =============================================================================
CREATE TABLE vehicles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    plate       TEXT    NOT NULL UNIQUE,
    brand       TEXT    NOT NULL,
    model       TEXT    NOT NULL,
    year        INTEGER CHECK (year IS NULL OR year BETWEEN 1900 AND 2100),
    vin         TEXT    UNIQUE,               -- số khung / VIN, NULL nếu chưa biết
    color       TEXT,
    odometer    INTEGER CHECK (odometer IS NULL OR odometer >= 0),  -- km hiện tại
    is_active   INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_vehicles_customer ON vehicles(customer_id);

-- =============================================================================
-- 4. appointments - lịch hẹn
--    Giữ cả customer_id và vehicle_id: customer_id là dữ liệu dẫn xuất để tra
--    cứu nhanh theo khách và cho phép đặt lịch trước khi chốt xe. Backend phải
--    kiểm tra customer_id khớp với customer_id của xe khi xe đã được chọn.
--    Ràng buộc duy nhất trên (vehicle_id, scheduled_at) là chỉ số, không phải
--    UNIQUE: việc chặn trùng lịch do tầng nghiệp vụ đảm nhiệm để báo đúng lý do.
-- =============================================================================
CREATE TABLE appointments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id  INTEGER NOT NULL REFERENCES customers(id)  ON DELETE RESTRICT,
    vehicle_id   INTEGER          REFERENCES vehicles(id)   ON DELETE RESTRICT,
    scheduled_at TEXT    NOT NULL,          -- định dạng chuẩn YYYY-MM-DD HH:MM
    notes        TEXT,
    status       TEXT    NOT NULL DEFAULT 'SCHEDULED'
        CHECK (status IN ('SCHEDULED', 'CONFIRMED', 'CANCELLED', 'DONE')),
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_appointments_vehicle ON appointments(vehicle_id);
CREATE INDEX idx_appointments_status  ON appointments(status);
CREATE INDEX idx_appointments_time    ON appointments(scheduled_at);

-- =============================================================================
-- 5. services - danh mục dịch vụ sửa chữa
--    description được phép NULL để phục vụ ca kiểm thử dữ liệu thiếu của AI02
-- =============================================================================
CREATE TABLE services (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT,
    price       INTEGER NOT NULL CHECK (price >= 0),
    is_active   INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_services_name   ON services(name);
CREATE INDEX idx_services_active ON services(is_active);

-- =============================================================================
-- 6. parts - danh mục phụ tùng và tồn kho
--    stock được phép bằng 0 để phục vụ ca kiểm thử hết hàng
-- =============================================================================
CREATE TABLE parts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    sku         TEXT,
    stock       INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    price       INTEGER NOT NULL CHECK (price >= 0),
    description TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_parts_name   ON parts(name);
CREATE INDEX idx_parts_active ON parts(is_active);
CREATE INDEX idx_parts_stock  ON parts(stock);

-- =============================================================================
-- 7. repair_orders - phiếu sửa chữa
--    Sáu trạng thái theo Hình 10, cộng thêm CANCELLED cho nhánh hủy
-- =============================================================================
CREATE TABLE repair_orders (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id       INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE RESTRICT,
    technician_id    INTEGER          REFERENCES users(id)    ON DELETE RESTRICT,
    status           TEXT    NOT NULL DEFAULT 'RECEIVED'
        CHECK (status IN ('RECEIVED', 'INSPECTING', 'ESTIMATING',
                          'REPAIRING', 'COMPLETED', 'CANCELLED')),
    technical_notes  TEXT,
    -- Nghiệm thu: ghi lại khi khách hàng ký nhận xe sau sửa chữa.
    acceptance_note  TEXT,
    accepted_by      INTEGER          REFERENCES users(id)    ON DELETE RESTRICT,
    acceptance_at    TEXT,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    -- Nếu đã nghiệm thu thì phải có cả người nghiệm thu và thời điểm.
    CHECK (acceptance_at IS NULL OR accepted_by IS NOT NULL)
);
CREATE INDEX idx_repair_orders_vehicle    ON repair_orders(vehicle_id);
CREATE INDEX idx_repair_orders_technician ON repair_orders(technician_id);
CREATE INDEX idx_repair_orders_status     ON repair_orders(status);
-- Báo cáo và danh sách đều sắp xếp theo thời điểm tạo.
CREATE INDEX idx_repair_orders_created    ON repair_orders(created_at DESC);

-- =============================================================================
-- 8. repair_order_items - hạng mục dịch vụ và phụ tùng của phiếu
--
--    RÀNG BUỘC QUAN TRỌNG NHẤT CỦA TOÀN BỘ CƠ SỞ DỮ LIỆU:
--    mỗi hạng mục hoặc là dịch vụ, hoặc là phụ tùng - ĐÚNG MỘT TRONG HAI.
--    Không được cả hai (hàng mục không xác định), không được cả hai rỗng
--    (hạng mục rỗng).
--
--    unit_price là bản chốt giá tại thời điểm thêm, không phải khóa ngoại tra
--    động. Xem phần giải thích đầu file.
-- =============================================================================
CREATE TABLE repair_order_items (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_order_id  INTEGER NOT NULL REFERENCES repair_orders(id) ON DELETE RESTRICT,
    service_id       INTEGER          REFERENCES services(id)   ON DELETE RESTRICT,
    part_id          INTEGER          REFERENCES parts(id)      ON DELETE RESTRICT,
    qty              INTEGER NOT NULL DEFAULT 1 CHECK (qty > 0),
    unit_price       INTEGER NOT NULL CHECK (unit_price >= 0),
    CHECK (
        (service_id IS NOT NULL AND part_id IS NULL) OR
        (service_id IS NULL     AND part_id IS NOT NULL)
    )
);
CREATE INDEX idx_roi_repair_order ON repair_order_items(repair_order_id);
CREATE INDEX idx_roi_service       ON repair_order_items(service_id);
CREATE INDEX idx_roi_part          ON repair_order_items(part_id);

-- =============================================================================
-- 9. repair_logs - nhật ký kỹ thuật
-- =============================================================================
CREATE TABLE repair_logs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_order_id  INTEGER NOT NULL REFERENCES repair_orders(id) ON DELETE RESTRICT,
    technician_id    INTEGER          REFERENCES users(id)        ON DELETE RESTRICT,
    note             TEXT    NOT NULL,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_repair_logs_order ON repair_logs(repair_order_id);

-- =============================================================================
-- 9b. intake_records - biên bản tiếp nhận xe
--     Ghi lại tình trạng xe tại thời điểm khách giao xe cho garage:
--     số km, mức nhiên liệu, ngoại thất, phụ kiện kèm theo…
--     Mỗi phiếu sửa chữa chỉ có MỘT biên bản tiếp nhận (UNIQUE repair_order_id).
-- =============================================================================
CREATE TABLE intake_records (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_order_id   INTEGER NOT NULL UNIQUE REFERENCES repair_orders(id) ON DELETE RESTRICT,
    odometer_at_intake INTEGER CHECK (odometer_at_intake IS NULL OR odometer_at_intake >= 0),
    fuel_level        TEXT    NOT NULL DEFAULT 'UNKNOWN'
        CHECK (fuel_level IN ('EMPTY', 'QUARTER', 'HALF', 'THREE_QUARTER', 'FULL', 'UNKNOWN')),
    exterior_condition TEXT,                  -- mô tả ngoại thất: trầy xước, móp…
    accessories       TEXT,                   -- phụ kiện kèm theo: chìa khoá, camera…
    notes             TEXT,
    created_by        INTEGER          REFERENCES users(id)    ON DELETE RESTRICT,
    created_at        TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_intake_order ON intake_records(repair_order_id);

-- =============================================================================
-- 9c. quotations - báo giá chính thức
--     Một phiếu sửa chữa có thể có nhiều báo giá (bản nháp, gửi, duyệt…).
--     total do BACKEND tính từ quotation_items, không nhận từ giao diện.
--     Chỉ một báo giá APPROVED cho mỗi phiếu (kiểm tra ở tầng dịch vụ).
-- =============================================================================
CREATE TABLE quotations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_order_id  INTEGER NOT NULL REFERENCES repair_orders(id) ON DELETE RESTRICT,
    status           TEXT    NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT', 'SENT', 'APPROVED', 'REJECTED', 'EXPIRED')),
    note             TEXT,
    valid_until      TEXT,                   -- hiệu lực đến (YYYY-MM-DD), NULL = không giới hạn
    total            INTEGER NOT NULL DEFAULT 0 CHECK (total >= 0),
    created_by       INTEGER          REFERENCES users(id)    ON DELETE RESTRICT,
    approved_by      INTEGER          REFERENCES users(id)    ON DELETE RESTRICT,
    approved_at      TEXT,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    CHECK (status <> 'APPROVED' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL))
);
CREATE INDEX idx_quotations_order  ON quotations(repair_order_id);
CREATE INDEX idx_quotations_status ON quotations(status);

-- =============================================================================
-- 9d. quotation_items - hạng mục của báo giá
--     Ràng buộc XOR giống repair_order_items: mỗi dòng hoặc dịch vụ, hoặc phụ
--     tùng — đúng một trong hai. unit_price chốt tại thời điểm thêm.
-- =============================================================================
CREATE TABLE quotation_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    quotation_id    INTEGER NOT NULL REFERENCES quotations(id) ON DELETE RESTRICT,
    service_id      INTEGER          REFERENCES services(id)   ON DELETE RESTRICT,
    part_id         INTEGER          REFERENCES parts(id)      ON DELETE RESTRICT,
    qty             INTEGER NOT NULL DEFAULT 1 CHECK (qty > 0),
    unit_price      INTEGER NOT NULL CHECK (unit_price >= 0),
    CHECK (
        (service_id IS NOT NULL AND part_id IS NULL) OR
        (service_id IS NULL     AND part_id IS NOT NULL)
    )
);
CREATE INDEX idx_qi_quotation ON quotation_items(quotation_id);
CREATE INDEX idx_qi_service   ON quotation_items(service_id);
CREATE INDEX idx_qi_part      ON quotation_items(part_id);

-- =============================================================================
-- 10. invoices - hóa đơn của phiếu
--     Quan hệ 1-1 với repair_orders nên UNIQUE(repair_order_id).
--     total do BACKEND tính từ repair_order_items, KHÔNG nhận từ giao diện.
--     paid là số tiền đã thu, luôn <= total.
-- =============================================================================
CREATE TABLE invoices (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_order_id  INTEGER NOT NULL UNIQUE REFERENCES repair_orders(id) ON DELETE RESTRICT,
    total            INTEGER NOT NULL CHECK (total >= 0),
    paid             INTEGER NOT NULL DEFAULT 0 CHECK (paid >= 0),
    status           TEXT    NOT NULL DEFAULT 'UNPAID'
        CHECK (status IN ('UNPAID', 'PARTIAL', 'PAID')),
    created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    CHECK (paid <= total)
);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_created ON invoices(created_at DESC);

-- =============================================================================
-- 11. payments - lịch sử thanh toán
--     Cho phép nhiều khoản trên một hoá đơn. Tổng các khoản không được vượt
--     invoices.total - quy tắc này do BACKEND kiểm tra trước khi ghi vì
--     SQLite không hỗ trợ ràng buộc giá trị tổng giữa hai bảng.
-- =============================================================================
CREATE TABLE payments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id  INTEGER NOT NULL REFERENCES invoices(id) ON DELETE RESTRICT,
    amount      INTEGER NOT NULL CHECK (amount > 0),
    method      TEXT    NOT NULL
        CHECK (method IN ('CASH', 'CARD', 'TRANSFER', 'ZALO')),
    paid_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_payments_invoice ON payments(invoice_id);

-- =============================================================================
-- 12. ai_results - kết quả AI và trạng thái Human Review
--     Mọi kết quả đều sinh ra ở trạng thái PENDING và phải được duyệt.
--     input_json lưu dữ liệu đã gửi lên model để phục vụ truy vết.
-- =============================================================================
CREATE TABLE ai_results (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    kind             TEXT    NOT NULL
        CHECK (kind IN ('history', 'explain', 'quote')),
    repair_order_id  INTEGER          REFERENCES repair_orders(id) ON DELETE RESTRICT,
    input_json       TEXT    NOT NULL,
    output_text      TEXT,
    is_valid         INTEGER NOT NULL DEFAULT 0 CHECK (is_valid IN (0, 1)),
    review_status    TEXT    NOT NULL DEFAULT 'PENDING'
        CHECK (review_status IN ('PENDING', 'APPROVED', 'REJECTED')),
    reviewed_by      INTEGER          REFERENCES users(id) ON DELETE RESTRICT,
    reviewed_at      TEXT,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    CHECK (review_status = 'PENDING' OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL))
);
CREATE INDEX idx_ai_results_order  ON ai_results(repair_order_id);
CREATE INDEX idx_ai_results_status ON ai_results(review_status);

-- =============================================================================
-- 13-16. CỬA HÀNG DỤNG CỤ - phần MỞ RỘNG, nằm ngoài phạm vi đề tài
--        Ba bảng đầu và ba bảng sau không phải nghiệp vụ lõi của đề tài.
-- =============================================================================

CREATE TABLE shop_categories (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT    NOT NULL,
    slug  TEXT    NOT NULL UNIQUE
);

CREATE TABLE shop_products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES shop_categories(id) ON DELETE RESTRICT,
    name        TEXT    NOT NULL,
    sku         TEXT    NOT NULL UNIQUE,
    price       INTEGER NOT NULL CHECK (price >= 0),
    stock       INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    description TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_shop_products_active  ON shop_products(is_active);
CREATE INDEX idx_shop_products_name     ON shop_products(name);

CREATE TABLE shop_orders (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT    NOT NULL,
    phone         TEXT    NOT NULL,
    address       TEXT    NOT NULL,
    total         INTEGER NOT NULL CHECK (total >= 0),
    status        TEXT    NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'PAID', 'SHIPPED', 'CANCELLED')),
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE shop_order_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER NOT NULL REFERENCES shop_orders(id)  ON DELETE RESTRICT,
    product_id  INTEGER NOT NULL REFERENCES shop_products(id) ON DELETE RESTRICT,
    qty         INTEGER NOT NULL CHECK (qty > 0),
    unit_price  INTEGER NOT NULL CHECK (unit_price >= 0)
);
CREATE INDEX idx_shop_order_items_order   ON shop_order_items(order_id);
CREATE INDEX idx_shop_order_items_product ON shop_order_items(product_id);

-- =============================================================================
-- TRÌNH TỰ LÀM VIỆC KHI PHÁT SINH NGHIỆP VỤ
-- -----------------------------------------------------------------------------
-- 1. Tiếp nhận:  tạo repair_orders (RECEIVED) -> thêm hạng mục khi kỹ thuật viên
--                xác định được dịch vụ hoặc phụ tùng (chốt unit_price tại đây).
-- 2. Báo giá:    chuyển ESTIMATING -> REPAIRING sau khi duyệt giá.
-- 3. Hoàn tất:  REPAIRING -> COMPLETED. CHỈ lập hoá đơn được khi phiếu COMPLETED.
-- 4. Thanh toán: ghi từng khoản vào payments, cập nhật invoices.paid. Backend
--                phải chặn khi tổng payments vượt invoices.total.
-- 5. Đóng hồ sơ: chỉ khi invoices.status = 'PAID'.
-- =============================================================================