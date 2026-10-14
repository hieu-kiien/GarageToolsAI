# -*- coding: utf-8 -*-
"""Áp migrations vào garage.db hiện có (idempotent, có backup).

Cách chạy:  python database/migrations/run_missing.py [đường_dẫn_tệp_csqlite]

* Mỗi tệp .sql chạy một lần theo thứ tự tên; CREATE TABLE/INDEX dùng
  IF NOT EXISTS nên chạy lại vô hại.
* ALTER TABLE ... ADD COLUMN không có IF NOT EXISTS trong SQLite — trình chạy
  tự bỏ qua cột đã tồn tại cho MỌI bảng (không riêng `parts`), nên script
  chạy lại bao nhiêu lần cũng được.
* Nếu tệp CSDL chưa tồn tại, tạo mới từ schema.sql + seed_data.sql.
* Tự sao lưu `*.bak-pre-migrate` trước lần áp dụng đầu tiên.
"""
import io
import shutil
import sqlite3
import sys
from pathlib import Path

# Chỉ bọc stdout khi chạy trực tiếp (`python run_missing.py`). Khi được import
# bởi app.main lúc khởi động, việc thay sys.stdout sẽ phá capture của test
# runner (I/O operation on closed file).
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parents[2]
MIG = BASE / "database" / "migrations"
SCHEMA = BASE / "database" / "schema.sql"
SEED = BASE / "database" / "seed_data.sql"


def _cot_da_ton_tai(conn: sqlite3.Connection, bang: str, cot: str) -> bool:
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(%s)" % bang)]
    except sqlite3.Error:
        return False
    return cot in cols


def _bo_qua_alter_da_co(conn: sqlite3.Connection, sql: str, ten_file: str) -> str:
    """Bỏ mọi ALTER TABLE ... ADD COLUMN đã tồn tại cột (bất kỳ bảng nào)."""
    lines = []
    for line in sql.splitlines(keepends=True):
        s = line.strip()
        up = s.upper()
        if up.startswith("ALTER TABLE") and " ADD COLUMN" in up:
            parts = s.split()
            try:
                bang = parts[parts.index("TABLE") + 1]
                cot = parts[parts.index("COLUMN") + 1]
            except (ValueError, IndexError):
                lines.append(line)
                continue
            if _cot_da_ton_tai(conn, bang, cot):
                print(f"{ten_file}: bo qua (da co {bang}.{cot})")
                continue
        lines.append(line)
    return "".join(lines)


def chay(db_path: Path | None = None) -> None:
    db = db_path or (BASE / "garage.db")
    if not db.exists():
        print(f"Chua co {db.name} — tao moi tu schema + seed.")
        db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db)
        try:
            conn.executescript(SCHEMA.read_text(encoding="utf-8"))
            if SEED.exists():
                conn.executescript(SEED.read_text(encoding="utf-8"))
            conn.commit()
        finally:
            conn.close()

    backup = db.with_suffix(db.suffix + ".bak-pre-migrate")
    if not backup.exists():
        shutil.copy2(db, backup)
        print(f"Backup: {backup.name}")

    conn = sqlite3.connect(db)
    conn.execute("PRAGMA foreign_keys = ON")

    before = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    print("Truoc:", ", ".join(sorted(before)))

    for f in sorted(MIG.glob("*.sql")):
        sql = _bo_qua_alter_da_co(conn, f.read_text(encoding="utf-8"), f.name)
        try:
            conn.executescript(sql)
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


if __name__ == "__main__":
    chay(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
