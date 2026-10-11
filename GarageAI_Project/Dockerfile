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

# Khởi tạo CSDL từ schema + dữ liệu mẫu
RUN python database/init_db.py

EXPOSE 8000

# Chạy không chế độ tự nạp lại, phù hợp môi trường thật
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]