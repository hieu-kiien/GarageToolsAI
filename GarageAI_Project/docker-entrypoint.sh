#!/bin/sh
# Docker entrypoint: sao lưu CSDL mẫu vào volume /data nếu chưa có,
# rồi khởi động uvicorn. Không xoá dữ liệu đã có.
set -e

DB="${DATABASE_PATH:-/data/garage.db}"
DIR=$(dirname "$DB")
mkdir -p "$DIR"

if [ ! -f "$DB" ]; then
  echo "CSDL chưa có tại $DB — sao từ image (đã seed lúc build)..."
  if [ -f /app/garage.db ]; then
    cp /app/garage.db "$DB"
  else
    python /app/database/init_db.py
    # init_db luôn ghi /app/garage.db
    cp /app/garage.db "$DB"
  fi
  echo "Đã tạo $DB"
else
  echo "Dùng CSDL có sẵn: $DB"
fi

exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
