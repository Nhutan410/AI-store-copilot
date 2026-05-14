@echo off
REM Chay AI Store Copilot tren Windows
cd /d "%~dp0"

IF NOT EXIST venv (
    echo Tao virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt -q
) ELSE (
    call venv\Scripts\activate.bat
)

IF NOT EXIST data\stores.json (
    echo Sinh du lieu mau...
    python data\seed_data.py
)

echo Khoi dong AI Store Copilot tai http://localhost:8501
streamlit run app.py --server.port 8501
