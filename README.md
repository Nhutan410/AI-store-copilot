# AI Store Copilot

Ứng dụng Streamlit hỗ trợ vận hành cửa hàng: xem dashboard, theo dõi dữ liệu trong ngày, chat với AI, quản lý cảnh báo/rule và mô phỏng dữ liệu demo.

## Tính năng chính

- Dashboard tổng quan doanh thu, đơn hàng, tỷ lệ chuyển đổi và tồn kho.
- Trang `Họp Ca Sáng` và `Trong hôm nay` cho vận hành theo ngày.
- Chat Copilot dùng OpenAI API.
- Rule Engine phát hiện vấn đề và gợi ý hành động.
- Trang thông báo, analytics và mô phỏng dữ liệu.
- Có đăng nhập bằng tài khoản cấu hình trong file `.env`.

## Yêu cầu

- Docker Desktop nếu chạy bằng Docker.
- Python 3.10+ nếu chạy trực tiếp không dùng Docker.
- OpenAI API key để dùng các tính năng AI.

## Cấu hình môi trường

Tạo file `.env` từ file mẫu:

```bash
cp .env.example .env
```

Mở file `.env` và điền:

```env
AUTH_USERNAME=your_username
AUTH_PASSWORD=your_password
OPENAI_API_KEY=sk-your-openai-key
```

File `.env` chứa thông tin nhạy cảm nên không commit lên GitHub.

## Chạy bằng Docker Compose

Đây là cách khuyên dùng sau khi clone code về máy:

```bash
docker compose up --build
```

Mở trình duyệt tại:

```text
http://localhost:8501
```

Dừng app:

```bash
docker compose down
```

## Chạy bằng Docker CLI

Build image:

```bash
docker build -t ai-store-copilot:latest .
```

Chạy container:

```bash
docker run --rm --env-file .env --name ai-store-copilot -p 8501:8501 ai-store-copilot:latest
```

Mở:

```text
http://localhost:8501
```

Nếu port `8501` đang bận, đổi host port sang `8502`:

```bash
docker run --rm --env-file .env --name ai-store-copilot -p 8502:8501 ai-store-copilot:latest
```

Khi đó mở:

```text
http://localhost:8502
```

Dừng container nếu đang chạy nền hoặc `Ctrl+C` không dừng được:

```bash
docker stop ai-store-copilot
```

## Chạy trực tiếp bằng Python

Tạo môi trường ảo:

```bash
python3 -m venv venv
source venv/bin/activate
```

Cài thư viện:

```bash
pip install -r requirements.txt
```

Tạo và điền file `.env`:

```bash
cp .env.example .env
```

Chạy app:

```bash
streamlit run app.py --server.port 8501
```

Mở:

```text
http://localhost:8501
```

## Cấu trúc thư mục

```text
.
├── app.py                 # Entry point Streamlit
├── engine/                # Logic dữ liệu, rule engine, OpenAI client
├── pages/                 # Các trang giao diện
├── data/                  # Dữ liệu JSON demo
├── docs/                  # Tài liệu giải thích thêm
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Lỗi thường gặp

**Port đã được sử dụng**

Nếu gặp lỗi `bind: address already in use` hoặc `port is already allocated`, đổi sang port khác:

```bash
docker run --rm --env-file .env --name ai-store-copilot -p 8502:8501 ai-store-copilot:latest
```

**App báo thiếu cấu hình đăng nhập**

Kiểm tra file `.env` đã có đủ:

```env
AUTH_USERNAME=...
AUTH_PASSWORD=...
```

**Tính năng AI không hoạt động**

Kiểm tra `OPENAI_API_KEY` trong file `.env` đã được điền đúng và container/app đã được chạy lại sau khi sửa file.

**Docker Compose không đọc cấu hình mới**

Chạy lại:

```bash
docker compose down
docker compose up --build
```
