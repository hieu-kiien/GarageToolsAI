-- =============================================================================
-- 003: Kho ledger (stock_transactions) + parts.min_stock
--
-- Bất biến cần giữ: parts.stock == SUM(stock_transactions.qty) theo part_id.
-- Trước khi thêm ledger, mọi phụ tùng đang có stock nhưng chưa có dòng nào,
-- nên migration phải ghi số dư mở đầu (một dòng ADJUSTMENT đúng bằng stock).
--
-- Chạy lại được: bảng được tạo IF NOT EXISTS, cột được thêm chỉ khi thiếu,
-- số dư mở đầu chỉ được ghi khi ledger còn trống cho phụ tùng đó.
-- =============================================================================
CREATE TABLE IF NOT EXISTS stock_transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id         INTEGER NOT NULL REFERENCES parts(id)         ON DELETE RESTRICT,
    qty             INTEGER NOT NULL,
    reason          TEXT    NOT NULL CHECK (reason IN
                        ('RECEIPT', 'USAGE', 'RETURN', 'ADJUSTMENT')),
    repair_order_id INTEGER          REFERENCES repair_orders(id) ON DELETE RESTRICT,
    note            TEXT,
    created_by      INTEGER          REFERENCES users(id)         ON DELETE RESTRICT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_stock_tx_part   ON stock_transactions(part_id);
CREATE INDEX IF NOT EXISTS idx_stock_tx_reason ON stock_transactions(reason);
CREATE INDEX IF NOT EXISTS idx_stock_tx_order  ON stock_transactions(repair_order_id);
CREATE INDEX IF NOT EXISTS idx_stock_tx_time   ON stock_transactions(created_at);

-- Thêm cột min_stock nếu chưa có (SQLite < 3.35 không hỗ trợ ADD COLUMN IF NOT
-- EXISTS, nên phải kiểm tra pragma trước).
-- Migration này được áp dụng bằng code Python (app/migrate.py) nên việc
-- kiểm tra cột tồn tại do code đảm nhiệm; đây chỉ là kịch bản SQL thuần.
ALTER TABLE parts ADD COLUMN min_stock INTEGER NOT NULL DEFAULT 0;
CREATE INDEX IF NOT EXISTS idx_parts_min_stock ON parts(min_stock);

-- Số dư mở đầu: với mỗi phụ tùng CÒN stock và CHƯA có dòng ledger nào,
-- ghi một dòng ADJUSTMENT đúng bằng stock hiện tại.
INSERT INTO stock_transactions (part_id, qty, reason, note)
SELECT p.id, p.stock, 'ADJUSTMENT', 'Số dư mở đầu khi nâng cấp hệ thống.'
  FROM parts p
 WHERE p.stock > 0
   AND NOT EXISTS (SELECT 1 FROM stock_transactions t WHERE t.part_id = p.id);
