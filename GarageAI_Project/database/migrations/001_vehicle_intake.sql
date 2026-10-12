-- =============================================================================
-- Migration 001: Xe (VIN/màu/odo) + tiếp nhận + nghiệm thu
-- Chạy: sqlite3 garage.db < database/migrations/001_vehicle_intake.sql
-- An toàn: chỉ ALTER TABLE ADD COLUMN (không xoá cột cũ), chạy được nhiều lần.
-- =============================================================================

-- 1. vehicles: thêm VIN, màu, số km
ALTER TABLE vehicles ADD COLUMN vin      TEXT;
ALTER TABLE vehicles ADD COLUMN color    TEXT;
ALTER TABLE vehicles ADD COLUMN odometer INTEGER;

-- UNIQUE cho vin: SQLite cho phép thêm index UNIQUE sau khi đã có cột.
CREATE UNIQUE INDEX IF NOT EXISTS idx_vehicles_vin ON vehicles(vin);

-- 2. repair_orders: thêm nghiệm thu
ALTER TABLE repair_orders ADD COLUMN acceptance_note TEXT;
ALTER TABLE repair_orders ADD COLUMN accepted_by     INTEGER;
ALTER TABLE repair_orders ADD COLUMN acceptance_at   TEXT;

-- 3. intake_records: biên bản tiếp nhận xe
CREATE TABLE IF NOT EXISTS intake_records (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_order_id    INTEGER NOT NULL UNIQUE REFERENCES repair_orders(id) ON DELETE RESTRICT,
    odometer_at_intake INTEGER CHECK (odometer_at_intake IS NULL OR odometer_at_intake >= 0),
    fuel_level         TEXT    NOT NULL DEFAULT 'UNKNOWN'
        CHECK (fuel_level IN ('EMPTY', 'QUARTER', 'HALF', 'THREE_QUARTER', 'FULL', 'UNKNOWN')),
    exterior_condition TEXT,
    accessories        TEXT,
    notes              TEXT,
    created_by         INTEGER          REFERENCES users(id) ON DELETE RESTRICT,
    created_at         TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_intake_order ON intake_records(repair_order_id);
