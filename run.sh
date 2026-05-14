#!/bin/bash
# Chạy AI Store Copilot trong môi trường venv
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Tạo virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt -q
fi

source venv/bin/activate

# Kiểm tra và tạo dữ liệu nếu chưa có
if [ ! -f "data/stores.json" ]; then
    echo "Sinh dữ liệu mẫu..."
    python data/seed_data.py
fi

echo "Khởi động AI Store Copilot tại http://localhost:8501"
streamlit run app.py --server.port 8501
