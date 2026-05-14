# AI Store Copilot — PNJ

Trợ lý AI vận hành cửa hàng trang sức PNJ. Phân tích dữ liệu bán hàng theo thời gian thực, phát hiện vấn đề bằng Rule Engine, và sinh báo cáo + đề xuất bằng ngôn ngữ tự nhiên tiếng Việt qua LLM local (Ollama).

---

## Mục lục

1. [Yêu cầu hệ thống](#1-yêu-cầu-hệ-thống)
2. [Cài đặt & Khởi động — macOS / Linux](#2-cài-đặt--khởi-động--macos--linux)
3. [Cài đặt & Khởi động — Windows](#3-cài-đặt--khởi-động--windows)
4. [Cấu trúc thư mục](#4-cấu-trúc-thư-mục)
5. [Luồng dữ liệu tổng quan](#5-luồng-dữ-liệu-tổng-quan)
6. [Chi tiết từng module](#6-chi-tiết-từng-module)
   - [data/seed_data.py](#61-dataseed_datapy--sinh-dữ-liệu-mẫu)
   - [engine/db.py](#62-enginedbpy--database-layer)
   - [engine/analytics.py](#63-engineanalyticspy--tính-toán-phân-tích)
   - [engine/rule_engine.py](#64-enginerule_enginepy--rule-engine)
   - [engine/llm.py](#65-enginellmpy--tích-hợp-llm)
   - [app.py](#66-apppy--streamlit-entry-point)
   - [pages/](#67-pages--6-trang-giao-diện)
7. [Luồng xử lý request theo trang](#7-luồng-xử-lý-request-theo-trang)
8. [12 Rules — Logic phát hiện vấn đề](#8-12-rules--logic-phát-hiện-vấn-đề)
9. [Dữ liệu demo](#9-dữ-liệu-demo)
10. [Mở rộng & Tùy chỉnh](#10-mở-rộng--tùy-chỉnh)

---

## 1. Yêu cầu hệ thống

| Thành phần | Phiên bản | Ghi chú |
|---|---|---|
| Python | ≥ 3.9 | Type hints `dict \| None` cần 3.10+ |
| Ollama | latest | Chạy local tại `localhost:11434` |
| Model LLM | `qwen2.5:7b` | Tải bằng `ollama pull qwen2.5:7b` |
| RAM | ≥ 8 GB | Model chiếm ~5 GB RAM |
| Disk | ≥ 6 GB | Model + virtualenv |

> **Lưu ý:** App vẫn chạy đầy đủ nếu Ollama offline — chỉ tắt các nút gọi AI. Toàn bộ biểu đồ và rule engine vẫn hoạt động bình thường.

---

## 2. Cài đặt & Khởi động — macOS / Linux

### Cách nhanh (dùng script)

```bash
git clone https://github.com/Nhutan410/AI-store-copilot.git
cd AI-store-copilot
chmod +x run.sh
./run.sh
```

Script tự động: tạo venv → cài packages → sinh data → khởi động app.

---

### Cài đặt thủ công từng bước

**Bước 1 — Clone repo:**
```bash
git clone https://github.com/Nhutan410/AI-store-copilot.git
cd AI-store-copilot
```

**Bước 2 — Tạo virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Bước 3 — Cài thư viện:**
```bash
pip install -r requirements.txt
```

**Bước 4 — Cài và khởi động Ollama:**
```bash
# Tải Ollama từ https://ollama.ai
ollama pull qwen2.5:7b            # ~4.7 GB, cần chờ
ollama serve                      # Giữ terminal này mở
```

**Bước 5 — Sinh dữ liệu mẫu** *(bỏ qua nếu repo đã có sẵn file JSON trong `data/`)*:
```bash
python data/seed_data.py
```

**Bước 6 — Chạy app:**
```bash
streamlit run app.py
# Mở trình duyệt tại http://localhost:8501
```

---

## 3. Cài đặt & Khởi động — Windows

> Đã test trên Windows 10/11 với Python 3.10+. Dùng **Command Prompt** hoặc **PowerShell** (không dùng Git Bash cho bước activate venv).

### Bước 0 — Cài đặt Python

1. Tải Python 3.10+ tại [python.org/downloads](https://www.python.org/downloads/)
2. Trong trình cài đặt: **tích chọn "Add Python to PATH"** trước khi bấm Install
3. Kiểm tra sau khi cài:
   ```cmd
   python --version
   ```

### Bước 1 — Cài đặt Git và clone repo

1. Tải Git tại [git-scm.com](https://git-scm.com/download/win), cài mặc định
2. Mở **Command Prompt** hoặc **PowerShell**, chạy:
   ```cmd
   git clone https://github.com/Nhutan410/AI-store-copilot.git
   cd AI-store-copilot
   ```

### Bước 2 — Tạo virtual environment

```cmd
python -m venv venv
venv\Scripts\activate
```

> Nếu gặp lỗi `execution policy` trong PowerShell, chạy trước:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Sau đó activate lại: `venv\Scripts\Activate.ps1`

### Bước 3 — Cài thư viện

```cmd
pip install -r requirements.txt
```

> Nếu pip báo lỗi SSL hoặc timeout, thêm flag mirror:
> ```cmd
> pip install -r requirements.txt -i https://pypi.org/simple/
> ```

### Bước 4 — Cài đặt Ollama

1. Tải Ollama cho Windows tại [ollama.ai](https://ollama.ai) — chọn bản `.exe`
2. Chạy file cài đặt, Ollama sẽ tự chạy nền sau khi cài
3. Mở **một cửa sổ Command Prompt mới** (giữ nguyên), chạy:
   ```cmd
   ollama pull qwen2.5:7b
   ```
   > Kích thước ~4.7 GB, cần chờ tùy tốc độ mạng

4. Kiểm tra Ollama đang chạy:
   ```cmd
   ollama list
   ```
   Phải thấy `qwen2.5:7b` trong danh sách.

### Bước 5 — Sinh dữ liệu mẫu *(bỏ qua nếu repo đã có sẵn file JSON trong `data/`)*

```cmd
python data\seed_data.py
```

Output mong đợi:
```
=== Sinh dữ liệu mẫu AI Store Copilot ===
[1/7] Lưu stores, staff, SKUs, rules, actions...
[2/7] Sinh lịch làm việc (roster) 31 ngày × 8 stores...
[3/7] Sinh giao dịch (transactions) 31 ngày × 8 stores...
       Tổng số giao dịch: 7,638
[4/7] Tính daily snapshots...
[5/7] Khởi tạo chat history, notifications, action feedback...
=== Hoàn tất! Dữ liệu đã sẵn sàng. ===
```

### Bước 6 — Chạy app

**Cách 1 — Dùng script tự động (khuyên dùng):**
```cmd
run.bat
```

**Cách 2 — Chạy thủ công:**
```cmd
venv\Scripts\activate
streamlit run app.py --server.port 8501
```

Mở trình duyệt tại **http://localhost:8501**

### Xử lý lỗi thường gặp trên Windows

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| `'python' is not recognized` | Python chưa vào PATH | Cài lại Python, tích "Add to PATH" |
| `Cannot be loaded because running scripts is disabled` | PowerShell policy | `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| `streamlit : The term 'streamlit' is not recognized` | venv chưa activate | Chạy `venv\Scripts\activate` trước |
| `Connection refused` khi dùng AI | Ollama chưa chạy | Mở Ollama app, hoặc chạy `ollama serve` |
| `UnicodeDecodeError` | Encoding Windows | Thêm biến môi trường: `set PYTHONIOENCODING=utf-8` rồi chạy lại |

---

---

## 4. Cấu trúc thư mục

```
ai_store_copilot/
│
├── app.py                    # Entry point Streamlit — sidebar, routing, CSS
├── requirements.txt
├── run.sh                    # Script chạy nhanh
│
├── data/
│   ├── seed_data.py          # Script sinh dữ liệu mẫu (chạy 1 lần)
│   ├── stores.json           # 8 cửa hàng PNJ
│   ├── staff.json            # 36 nhân viên
│   ├── skus.json             # 28 sản phẩm (SKU)
│   ├── rules.json            # 12 rules + confidence score (ghi đè khi có feedback)
│   ├── action_registry.json  # 25 actions có thể thực hiện
│   ├── transactions.json     # ~7,600 giao dịch (31 ngày × 8 stores)
│   ├── snapshots.json        # Tổng hợp ngày (248 bản ghi = 31 × 8)
│   ├── roster.json           # Lịch làm việc (248 bản ghi)
│   ├── chat_history.json     # Lịch sử chat theo store (runtime, ghi động)
│   ├── notifications.json    # Thông báo push (runtime, ghi động)
│   └── action_feedback.json  # Phản hồi CHT về actions (runtime, ghi động)
│
├── engine/
│   ├── __init__.py
│   ├── db.py                 # CRUD operations — đọc/ghi JSON files
│   ├── analytics.py          # Health score, baselines, trends, benchmarks
│   ├── rule_engine.py        # 12 rules deterministic + signal generation
│   └── llm.py                # Ollama client + 6 loại prompt tiếng Việt
│
└── pages/
    ├── __init__.py
    ├── dashboard.py          # Trang 1 — Tổng quan + AI báo cáo
    ├── chat.py               # Trang 2 — Chat Q&A tiếng Việt
    ├── morning.py            # Trang 3 — Brief họp ca sáng
    ├── actions.py            # Trang 4 — Accept/Skip actions + rule history
    ├── analytics_page.py     # Trang 5 — Charts 30 ngày + benchmark
    └── notifications.py      # Trang 6 — Feed thông báo
```

---

## 5. Luồng dữ liệu tổng quan

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NGUỒN DỮ LIỆU                                │
│  transactions.json  →  snapshots.json  ←  roster.json              │
│  (7,638 giao dịch)     (248 bản tổng hợp)  (lịch làm việc)        │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       engine/db.py                                   │
│  get_snapshot() / get_snapshots() / get_roster() / get_staff()     │
│  → Đọc JSON files, trả về dict/list Python                          │
└─────────────────────────────────────────────────────────────────────┘
                    │                    │
          ┌─────────┘                    └──────────┐
          ▼                                         ▼
┌──────────────────────┐               ┌────────────────────────┐
│  engine/analytics.py │               │  engine/rule_engine.py │
│  - calc_health_score │               │  - evaluate_rules()    │
│  - get_baseline()    │               │  - _build_context()    │
│  - get_*_trend()     │               │  - _check_rule()       │
│  - predict_eod_rev() │               │  → signals[] (cảnh báo)│
│  - get_sku_opport()  │               └────────────┬───────────┘
└──────────┬───────────┘                            │
           │                                        │
           └────────────────┬───────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       engine/llm.py                                  │
│  _build_store_context() → Nhúng tất cả số liệu vào prompt          │
│  → gen_health_report() / gen_root_cause() / chat_with_copilot()    │
│  → _call_ollama(prompt) → Ollama API → qwen2.5:7b                  │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Streamlit Pages (UI)                              │
│  dashboard.py / chat.py / morning.py / actions.py / analytics_page.py / notifications.py  │
└─────────────────────────────────────────────────────────────────────┘
```

**Nguyên tắc thiết kế quan trọng:**
- LLM **không tự bịa số liệu** — toàn bộ metrics được tính bởi `analytics.py` và `rule_engine.py` trước khi nhúng vào prompt
- Rule engine chạy **deterministic** (không có AI) → kết quả ổn định, không phụ thuộc vào Ollama
- Pages **không tự gọi LLM khi load** → load < 2 giây, chỉ gọi khi user bấm nút
- Kết quả LLM được **cache trong `st.session_state`** → không gọi lại khi scroll hoặc switch tab

---

## 6. Chi tiết từng module

### 6.1 `data/seed_data.py` — Sinh dữ liệu mẫu

**Mục đích:** Tạo toàn bộ dữ liệu demo có tính nhất quán và realistic. Chạy **một lần** khi setup.

**Các hằng số điều chỉnh behavior:**

| Hằng số | Giá trị | Ý nghĩa |
|---|---|---|
| `CR_CALIBRATION` | `0.68` | Hệ số calibration để revenue khớp với target thực tế |
| `COUPLE_WEDDING_PROB` | `0.26` | Xác suất cặp đôi mua nhẫn cưới/đính hôn |
| `CHEAP_PRICE_THRESHOLD` | `4,000,000đ` | Ngưỡng phân biệt "đồ rẻ" vs "đồ đắt" |
| `random.seed(42)` | fixed | Đảm bảo data reproducible mỗi lần chạy |

**Các hàm sinh dữ liệu:**

```
gen_roster(today)
  → Tạo lịch làm việc 31 ngày × 8 stores
  → STR-002 được tạo đặc biệt: 7/31 ngày ca chiều thiếu senior wedding
    (Bảo Ngọc bị đẩy sang ca sáng) để Rule Engine có pattern để phát hiện

gen_transactions(today, roster)
  → Cho mỗi ngày × store: tính traffic (base × weekday_mult × special_mult × noise)
  → Phân phối traffic theo giờ (weights: giờ 17-20h cao nhất)
  → Cho mỗi visitor: random ctype → staff CR × CR_CALIBRATION → chọn SKU
  → SKU được chọn theo xác suất CVR, ưu tiên hàng <4M (để AOV ~2-3M thực tế)
  → Cặp đôi có 26% cơ hội mua thẳng vào nhẫn cưới/đính hôn (expensive path)

gen_snapshots(today, transactions, roster)
  → Group transactions theo (store_id, date)
  → Tính: revenue, CR, AOV, category_revenue, customer_type_count,
           shift_revenue, staff_performance, shift_traffic
  → Đính kèm roster của ngày đó (morning/afternoon/evening_staff)
```

**Các pattern được đưa vào data (để AI phát hiện được):**
- Thứ 7/CN: traffic +30–40% vs ngày thường
- Thứ 2: traffic thấp nhất (×0.75)
- Đầu tháng (ngày 1–5): doanh thu +15%
- Cuối tháng (ngày ≥25): doanh thu −12%
- Ngày Valentine/8/3/20/10: traffic ×1.7–2.0
- Senior có CR cao hơn junior ~15–20 điểm %

---

### 6.2 `engine/db.py` — Database Layer

**Mục đích:** Tập trung toàn bộ I/O với JSON files. Pages và engines không đọc file JSON trực tiếp.

**Hàm đọc chính:**

```python
get_stores() → list[dict]
get_store(store_id) → dict | None
get_staff(store_id=None) → list[dict]
get_skus(segment=None) → list[dict]      # Lọc theo phân khúc A/B/C
get_snapshot(store_id, date_str) → dict | None
get_snapshots(store_id, days=30) → list[dict]   # Sắp xếp theo ngày tăng dần
get_transactions(store_id, date_str=None, days=30) → list[dict]
get_roster(store_id, date_str) → dict | None
get_rules() → list[dict]
get_action_registry() → list[dict]
```

**Hàm ghi runtime:**

```python
append_chat(store_id, role, content)     # Thêm message vào chat_history.json
clear_chat(store_id)                     # Xóa lịch sử chat của store
add_notification(store_id, title, body, type, urgency)
mark_notification_read(notif_id)
save_action_feedback(store_id, rule_id, action_id, decision, snapshot_before)
    → Sau khi lưu: tự gọi _update_rule_confidence() để cập nhật rules.json
```

**Cơ chế Learning Loop:**

```python
_update_rule_confidence(rule_id, decision):
    # Mỗi lần CHT "accept" → positive_feedback += 1
    # confidence = base(0.70) + (positive_feedback / total_feedback) * 0.25
    # Range: 0.70 – 0.95
```

---

### 6.3 `engine/analytics.py` — Tính toán phân tích

**Mục đích:** Tất cả tính toán số liệu, không có I/O trực tiếp ngoài đọc qua `db`.

**Health Score (0–100):**

```
Thành phần              Điểm tối đa  Công thức
─────────────────────────────────────────────────────
Doanh thu vs Target          40     min(40, target_pct × 40)
Tỷ lệ chuyển đổi (CR)       25     min(25, cr_ratio × 25)
Lưu lượng khách             15     min(15, traffic_ratio × 15)
Cơ cấu sản phẩm             10     min(10, wedding_engagement_pct/0.40 × 10)
Hiệu suất nhân viên         10     min(10, implicit_cr/0.35 × 10)
─────────────────────────────────────────────────────
Tổng                        100

Grade: A ≥85 | B ≥70 | C ≥55 | D <55
```

**Baseline (14 ngày trung bình):**
```python
get_baseline(store_id, metric="traffic", days=14)
    → Trung bình của metric trong N ngày gần nhất (loại trừ ngày hiện tại)

get_dow_baseline(store_id, day_of_week, metric, weeks=4)
    → Baseline chỉ tính các ngày cùng thứ trong 4 tuần gần nhất
    → Dùng để so sánh "Thứ Ba này vs Thứ Ba trung bình"
```

**Predictive Revenue:**
```python
predict_eod_revenue(store_id, current_revenue, current_hour)
    → Linear projection: revenue_eod = current_revenue / hour_weight[current_hour]
    → hour_weight: tỷ lệ doanh thu tích lũy đến từng giờ (lịch sử)
    → VD: 16h thường tích lũy 62% → nếu hiện tại có 50M → dự báo 80.6M
```

**SKU Opportunity Score:**
```python
get_sku_opportunity_scores(store_id, date_str)
    → opportunity_score = cvr_history × margin_pct × min(1.0, stock/10)
    → is_missed_opportunity: stock > 0 AND sku chưa bán trong 7 ngày qua
    → Sắp xếp giảm dần theo opportunity_score
```

---

### 6.4 `engine/rule_engine.py` — Rule Engine

**Mục đích:** Phát hiện vấn đề bằng logic deterministic (if/then), không dùng AI. Chạy **trước** khi gọi LLM.

**Luồng chính:**

```
evaluate_rules_for_store(store_id, date_str)
    │
    ├─→ db.get_snapshot()         # Lấy metrics ngày đó
    ├─→ db.get_roster()           # Lấy đội hình ca
    ├─→ analytics.compare_to_baseline()  # Tính ratios so với baseline
    │
    ├─→ _build_context()          # Tổng hợp tất cả vào dict "ctx"
    │     ctx chứa: wedding_revenue_pct, couple_traffic_pct,
    │               strong_wedding_staff_in_peak, senior_count_in_peak,
    │               traffic_ratio, cr_ratio, aov, day_of_month, ...
    │
    └─→ for rule in rules:
            _check_rule(rule, ctx)  # Kiểm tra điều kiện WHEN
            → triggered, details
        
        → signals[] sorted by urgency (HIGH→MEDIUM→LOW) rồi confidence
```

**Output signal format:**
```python
{
    "rule_id": "RULE-01",
    "rule_name": "Nhẫn cưới yếu trong cao điểm",
    "why": "Nhẫn cưới chiếm 40–50% doanh thu lý tưởng...",
    "actions": ["focus_wedding_sku", "add_strong_staff_to_peak"],
    "confidence": 0.85,
    "urgency": "HIGH",
    "details": "Nhẫn cưới đạt 11.7% doanh thu (ngưỡng 32%), 1 NV mạnh wedding ở ca chiều."
}
```

---

### 6.5 `engine/llm.py` — Tích hợp LLM

**Mục đích:** Gọi Ollama và quản lý tất cả prompt templates.

**Hàm trung tâm — Context Builder:**

```python
_build_store_context(store_id, date_str) → str
    # Tổng hợp ~500 chữ số liệu thực tế của store vào 1 chuỗi text
    # Gồm: doanh thu, CR, AOV, category mix, nhóm khách,
    #       đội hình ca, top NV, cảnh báo đang kích hoạt
    # → Nhúng trực tiếp vào mọi prompt (LLM không tự bịa số)
```

**6 loại prompt và temperature:**

| Hàm | Temperature | Mục đích |
|---|---|---|
| `gen_health_report()` | 0.25 | Báo cáo sức khỏe — cần chính xác |
| `gen_root_cause_analysis()` | 0.20 | Phân tích nguyên nhân — cần logic chặt |
| `gen_morning_brief()` | 0.50 | Brief họp ca — cần văn xuôi tự nhiên |
| `chat_with_copilot()` | 0.35 | Chat Q&A — cân bằng chính xác/tự nhiên |
| `gen_eod_summary()` | 0.30 | Tổng kết cuối ngày |
| `gen_notification_content()` | 0.30 | Nội dung thông báo ngắn |

**Cấu trúc prompt chung:**
```
[System role: AI là trợ lý PNJ, phục vụ cửa hàng X]
[Dữ liệu thực tế: _build_store_context()]
[Instruction: yêu cầu format output, độ dài, ngôn ngữ]
```

---

### 6.6 `app.py` — Streamlit Entry Point

**Mục đích:** Khởi tạo app, quản lý sidebar, điều hướng giữa 6 pages.

**Session state variables:**

| Key | Kiểu | Mục đích |
|---|---|---|
| `selected_store` | `str` | Store ID đang xem (default: `STR-002`) |
| `ollama_ok` | `bool` | Trạng thái kết nối Ollama (check 1 lần khi load) |
| `ollama_checked` | `bool` | Tránh kiểm tra lại nhiều lần |
| `current_page` | `str` | Page đang hiển thị |
| `llm_cache` | `dict` | Cache kết quả LLM — xóa khi đổi store |
| `feedback_given` | `dict` | Theo dõi actions đã feedback trong session |

**Page routing:**
```python
if page == "dashboard":    from pages.dashboard import render; render(store_id)
if page == "chat":         from pages.chat import render; render(store_id)
# ... etc
```

Import động (lazy) — tránh load tất cả pages khi khởi động.

---

### 6.7 `pages/` — 6 trang giao diện

| File | DATE dùng | Cache LLM | Ghi DB |
|---|---|---|---|
| `dashboard.py` | `2026-04-30` | health_report, root_cause | Không |
| `chat.py` | `2026-04-30` | Không (real-time) | chat_history |
| `morning.py` | `2026-04-30` (yesterday) | morning_brief | Không |
| `actions.py` | `2026-04-30` | Không | action_feedback, notifications |
| `analytics_page.py` | `2026-04-30` (cross-store) | Không | Không |
| `notifications.py` | `2026-04-30` | notif_content | notifications |

---

## 7. Luồng xử lý request theo trang

### Dashboard — khi user bấm "Tạo Báo Cáo AI"

```
User bấm nút
    → Kiểm tra ollama_ok (nếu False → disable nút)
    → Kiểm tra llm_cache[key] (nếu có → hiển thị ngay, không gọi lại)
    → st.spinner("AI đang phân tích...")
    → llm.gen_health_report(store_id, DATE)
        → _build_store_context()
            → db.get_snapshot()           # Metrics ngày đó
            → analytics.calc_health_score()
            → analytics.compare_to_baseline()
            → evaluate_rules_for_store()  # Nhúng signals vào context
        → _call_ollama(prompt, temperature=0.25)
            → POST http://localhost:11434/api/generate
            → Chờ response (10–60 giây)
        → Trả về string tiếng Việt
    → Lưu vào st.session_state.llm_cache[key]
    → st.rerun() để render kết quả
```

### Actions — khi user bấm "Chấp nhận"

```
User bấm "✅ Chấp nhận" tại rule RULE-01
    → db.save_action_feedback(store_id, "RULE-01", "focus_wedding_sku", "accept", snap)
        → Ghi vào action_feedback.json
        → _update_rule_confidence("RULE-01", "accept")
            → rules.json: positive_feedback += 1, recalculate confidence
    → db.add_notification(store_id, "Action được áp dụng...", ...)
        → Ghi vào notifications.json
    → st.session_state.feedback_given[key] = "accept"
    → st.rerun() → hiển thị badge "✅ Đã chấp nhận"
```

### Chat — khi user gửi câu hỏi

```
User nhập câu hỏi + bấm "Gửi"
    → db.append_chat(store_id, "user", message)  # Lưu vào chat_history.json
    → st.spinner("AI đang trả lời...")
    → llm.chat_with_copilot(store_id, DATE, message, history)
        → history[-6:] → lấy 6 turns gần nhất làm context hội thoại
        → _build_store_context() → dữ liệu store thực tế
        → _call_ollama(prompt, temperature=0.35, max_tokens=512)
    → db.append_chat(store_id, "assistant", response)
    → st.rerun() → render bubble chat mới
```

---

## 8. 12 Rules — Logic phát hiện vấn đề

| Rule | Trigger khi | Actions | Urgency |
|---|---|---|---|
| RULE-01 | Nhẫn cưới <32% DT + thiếu senior wedding ca chiều | focus_wedding_sku, add_strong_staff | HIGH |
| RULE-02 | Traffic ≥90% baseline NHƯNG CR <85% baseline | change_sales_pitch, simplify_choice | MEDIUM |
| RULE-03 | Doanh thu đến trưa <38% target | alert_manager, mini_activation | HIGH |
| RULE-04 | Không có senior nào trong giờ vàng 17–20h | reassign_senior_to_peak | HIGH |
| RULE-05 | Hàng margin thấp >55% doanh thu | focus_high_margin_sku, coach_upsell | MEDIUM |
| RULE-06 | Khách couple ≥35% NHƯNG nhẫn cưới+đính hôn <40% DT | focus_wedding, emotional_selling | MEDIUM |
| RULE-07 | Junior > senior × 2 trong giờ đông | pair_junior_with_senior | MEDIUM |
| RULE-08 | SKU tồn ≥10, CVR ≥40%, không bán 7 ngày | feature_slow_moving_sku | LOW |
| RULE-09 | Doanh thu 16h <55% target | urgent_alert, activate_closing_push | HIGH |
| RULE-10 | Thứ 2 + traffic sáng <60% baseline thứ 2 | proactive_greeting, social_incentive | MEDIUM |
| RULE-11 | Ngày ≥25 cuối tháng + AOV <4M | suggest_installment, focus_mid_price | MEDIUM |
| RULE-12 | Khách nữ độc thân ≥40% + nhẫn thời trang+lắc <25% DT | pitch_self_reward, feature_fashion | MEDIUM |

**Confidence tự học:**
- Bắt đầu: 0.68–0.90 (preset theo nghiệp vụ)
- Mỗi lần CHT Accept: `confidence = 0.70 + (accepted/total) × 0.25`
- Tối đa: 0.95 | Tối thiểu: 0.70

---

## 9. Dữ liệu demo

**Store chính demo:** STR-002 — PNJ Parkson Cantavil (TP.HCM, Segment A, target 92M/ngày)

**Ngày demo:** 2026-04-30 (Thứ Năm, cuối tháng)
- Revenue: 72.8M (79.2% target) → dưới target rõ rệt
- CR: 19.3% (thấp hơn baseline 30.9%)
- Wedding ring: chỉ 11.7% (target 32%) → RULE-01, RULE-03, RULE-09 trigger
- 6 rules kích hoạt (nhiều nhất trong dataset) → demo phong phú nhất

**Đổi ngày demo:** Mở từng file trong `pages/` và thay `DATE = "..."`.

**Tái tạo dữ liệu:** Chạy lại `python data/seed_data.py` — `random.seed(42)` đảm bảo kết quả giống hệt.

---

## 10. Mở rộng & Tùy chỉnh

### Thêm rule mới

1. Thêm vào `RULES` trong `data/seed_data.py`
2. Thêm case `if rid == "RULE-XX":` trong `_check_rule()` tại `rule_engine.py`
3. Chạy lại `python data/seed_data.py` để ghi rule vào `rules.json`

### Thêm store thực tế

1. Thêm vào `STORES` và `STAFF` trong `seed_data.py`
2. Chạy lại `seed_data.py`
3. App tự nhận store mới qua `db.get_stores()` → sidebar dropdown

### Đổi model LLM

Sửa `MODEL = "qwen2.5:7b"` trong `engine/llm.py` thành bất kỳ model nào đã pull về Ollama:
```bash
ollama pull llama3.2:3b    # Nhanh hơn, nhẹ hơn
ollama pull qwen2.5:14b    # Chất lượng cao hơn, chậm hơn
```

### Kết nối API thực tế

Thay các hàm `get_*` trong `engine/db.py` để đọc từ database thực (PostgreSQL, BigQuery...) thay vì JSON files. Interface hàm giữ nguyên — pages và engines không cần sửa.
