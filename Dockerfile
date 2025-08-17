# Dùng Python 3.11
FROM python:3.11-slim

# Tạo thư mục app
WORKDIR /app

# Cài dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Chạy app
CMD ["python", "api.py"]
