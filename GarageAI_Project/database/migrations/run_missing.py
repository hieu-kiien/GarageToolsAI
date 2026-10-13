# -*- coding: utf-8 -*-
"""Áp migrations 001-004 vào garage.db hiện có (idempotent, có backup)."""
import io
import shutil
import sqlite3
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parents[2]
DB = BASE / "garage.db"
MIG = BASE / "database" / "migrations"

backup = DB.with_suffix(".db.bak-pre-migrate")
if not backup.exists():
    shutil.copy2(DB, backup)
    print(f"Backup: {backup.name}")

conn = sqlite3.connect(DB)
conn.execute("PRAGMA foreign_keys = ON")

before = {r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
print("Truoc:", ", ".join(sorted(before)))

for f in sorted(MIG.glob("*.sql")):
    sql = f.read_text(encoding="utf-8")
    # ALTER TABLE ADD COLUMN không có IF NOT EXISTS -> bỏ qua cột đã tồn tại.
    lines = []
    for line in sql.splitlines(keepends=True):
        s = line.strip()
        if s.upper().startswith("ALTER TABLE PARTS ADD COLUMN"):
            col = s.split()[-1]
            cols = [r[1] for r in conn.execute("PRAGMA table_info(parts)")]
            if col in cols:
                print(f"{f.name}: bo qua (da co cot {col})")
                continue
        lines.append(line)
    try:
        conn.executescript("".join(lines))
        conn.commit()
        print(f"{f.name}: OK")
    except Exception as e:  # noqa: BLE001
        print(f"{f.name}: LOI {e}")
        raise

after = {r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
print("Sau:", ", ".join(sorted(after)))
print("Them moi:", ", ".join(sorted(after - before)) or "(khong)")

for t in ("intake_records", "stock_transactions", "quotations", "warranties"):
    n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"{t}: {n} dong")
lech = conn.execute("""
    SELECT COUNT(*) FROM parts p
     WHERE p.stock > 0
       AND COALESCE((SELECT SUM(qty) FROM stock_transactions t WHERE t.part_id = p.id), -1) <> p.stock
""").fetchone()[0]
print("Phu tung lech so:", lech)
conn.close()
