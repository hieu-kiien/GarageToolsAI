-- =============================================================================
-- 005. quotation_applied - đánh dấu báo giá đã được áp dụng vào phiếu
--     Trước migration này, áp dụng báo giá có thể chạy nhiều lần (double-click,
--     retry) và nhân đôi hạng mục/doanh thu. Hai cột mới cho phép:
--     * chặn áp dụng lần hai ngay trong transaction (applied_at IS NULL),
--     * lưu ai áp dụng và lúc nào cho nhật ký.
--     Cột nullable + DEFAULT NULL: an toàn với dữ liệu cũ, không cần backfill.
--     Idempotent: chạy lại bao nhiêu lần cũng được.
-- =============================================================================
ALTER TABLE quotations ADD COLUMN applied_at TEXT;
ALTER TABLE quotations ADD COLUMN applied_by INTEGER REFERENCES users(id) ON DELETE RESTRICT;

-- Tạo báo giá mới cho phiếu: báo giá đã áp dụng không còn "đang mở".
CREATE INDEX IF NOT EXISTS idx_quotations_open
    ON quotations(repair_order_id) WHERE applied_at IS NULL;
