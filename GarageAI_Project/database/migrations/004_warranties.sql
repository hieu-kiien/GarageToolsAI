-- =============================================================================
-- 004: Bảo hành (warranties)
--
-- Bảng mới, không đụng dữ liệu cũ. Chạy lại được nhờ IF NOT EXISTS.
-- Ràng buộc XOR (SERVICE xor PART) nằm ngay trong CHECK của CSDL.
-- =============================================================================
CREATE TABLE IF NOT EXISTS warranties (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_order_id  INTEGER NOT NULL REFERENCES repair_orders(id) ON DELETE RESTRICT,
    scope            TEXT    NOT NULL CHECK (scope IN ('SERVICE', 'PART')),
    service_id       INTEGER          REFERENCES services(id) ON DELETE RESTRICT,
    part_id          INTEGER          REFERENCES parts(id)    ON DELETE RESTRICT,
    months           INTEGER NOT NULL CHECK (months > 0),
    start_date       TEXT    NOT NULL,
    end_date         TEXT    NOT NULL,
    status           TEXT    NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'EXPIRED', 'CLAIMED', 'CANCELLED')),
    note             TEXT,
    created_by       INTEGER          REFERENCES users(id)   ON DELETE RESTRICT,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    CHECK (end_date > start_date),
    CHECK (
        (scope = 'SERVICE' AND service_id IS NOT NULL AND part_id IS NULL) OR
        (scope = 'PART'    AND part_id    IS NOT NULL AND service_id IS NULL)
    )
);
CREATE INDEX IF NOT EXISTS idx_warranties_order   ON warranties(repair_order_id);
CREATE INDEX IF NOT EXISTS idx_warranties_status  ON warranties(status);
CREATE INDEX IF NOT EXISTS idx_warranties_part    ON warranties(part_id);
CREATE INDEX IF NOT EXISTS idx_warranties_service ON warranties(service_id);
CREATE INDEX IF NOT EXISTS idx_warranties_end     ON warranties(end_date);
