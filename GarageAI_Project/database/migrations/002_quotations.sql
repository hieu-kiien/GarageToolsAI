-- =============================================================================
-- Migration 002: Báo giá chính thức (quotations + quotation_items)
-- Chạy: sqlite3 garage.db < database/migrations/002_quotations.sql
-- =============================================================================

CREATE TABLE IF NOT EXISTS quotations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_order_id  INTEGER NOT NULL REFERENCES repair_orders(id) ON DELETE RESTRICT,
    status           TEXT    NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT', 'SENT', 'APPROVED', 'REJECTED', 'EXPIRED')),
    note             TEXT,
    valid_until      TEXT,
    total            INTEGER NOT NULL DEFAULT 0 CHECK (total >= 0),
    created_by       INTEGER          REFERENCES users(id)    ON DELETE RESTRICT,
    approved_by      INTEGER          REFERENCES users(id)    ON DELETE RESTRICT,
    approved_at      TEXT,
    created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    CHECK (status <> 'APPROVED' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS idx_quotations_order  ON quotations(repair_order_id);
CREATE INDEX IF NOT EXISTS idx_quotations_status ON quotations(status);

CREATE TABLE IF NOT EXISTS quotation_items (
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
CREATE INDEX IF NOT EXISTS idx_qi_quotation ON quotation_items(quotation_id);
CREATE INDEX IF NOT EXISTS idx_qi_service   ON quotation_items(service_id);
CREATE INDEX IF NOT EXISTS idx_qi_part      ON quotation_items(part_id);
