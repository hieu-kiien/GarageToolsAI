# Ảnh chạy ứng dụng GarageTools AI
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Ho_Chi_Minh

WORKDIR /app

# Cài thư viện trước để tận dụng cache tầng của Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Khởi tạo CSDL mẫu lúc build (entrypoint sẽ copy sang /data nếu volume trống)
RUN python database/init_db.py \
    && chmod +x docker-entrypoint.sh

EXPOSE 8000

# Chạy không chế độ tự nạp lại, phù hợp môi trường thật
ENTRYPOINT ["./docker-entrypoint.sh"]
