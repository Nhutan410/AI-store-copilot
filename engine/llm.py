"""
LLM client + prompt templates cho AI Store Copilot.
Hỗ trợ: OpenAI gpt-4o-mini (ưu tiên nếu có API key) hoặc Ollama qwen2.5:7b (local fallback).
"""
import json
import requests
from engine import db, analytics
from engine.rule_engine import evaluate_rules_for_store

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"
OPENAI_MODEL = "gpt-4o-mini"

_VI_ENFORCE = (
    "QUAN TRỌNG: Bạn PHẢI trả lời HOÀN TOÀN bằng tiếng Việt. "
    "Tuyệt đối không dùng tiếng Trung, tiếng Anh hay bất kỳ ngôn ngữ nào khác.\n\n"
)
_VI_REMIND = "\n\n(Nhắc nhở: Chỉ dùng tiếng Việt trong toàn bộ câu trả lời.)"

# Module-level OpenAI key — được set từ app.py mỗi lần render
_openai_api_key: str = ""


def set_openai_key(key: str) -> None:
    """Đặt OpenAI API key cho module. Gọi từ app.py sau mỗi lần render sidebar."""
    global _openai_api_key
    _openai_api_key = (key or "").strip()


def is_openai_enabled() -> bool:
    """Trả về True nếu OpenAI API key đã được nhập."""
    return bool(_openai_api_key)


# ─── Health checks ───────────────────────────────────────────────────────────

def check_ollama() -> bool:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def check_openai() -> bool:
    """Kiểm tra OpenAI API key có hợp lệ không (gọi models.list nhẹ)."""
    if not _openai_api_key:
        return False
    try:
        import openai
        client = openai.OpenAI(api_key=_openai_api_key)
        client.models.list()
        return True
    except Exception:
        return False


# ─── LLM callers ─────────────────────────────────────────────────────────────

def _call_ollama(prompt: str, temperature: float = 0.25,
                 max_tokens: int = 1024) -> str:
    full_prompt = _VI_ENFORCE + prompt + _VI_REMIND
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
            "stop": ["<|im_end|>", "[/INST]"],
        }
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        return "⚠️ Không kết nối được Ollama. Vui lòng kiểm tra Ollama đang chạy tại localhost:11434."
    except Exception as e:
        return f"⚠️ Lỗi khi gọi AI: {str(e)}"


def _call_openai(prompt: str, temperature: float = 0.25,
                 max_tokens: int = 1024) -> str:
    try:
        import openai
        client = openai.OpenAI(api_key=_openai_api_key)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _VI_ENFORCE.strip()},
                {"role": "user", "content": prompt + _VI_REMIND},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except ImportError:
        return "⚠️ Thư viện openai chưa được cài. Chạy: pip install openai"
    except Exception as e:
        return f"⚠️ Lỗi OpenAI: {str(e)}"


def _call_llm(prompt: str, temperature: float = 0.25,
              max_tokens: int = 1024) -> str:
    """Router: dùng OpenAI nếu có key, ngược lại dùng Ollama local."""
    if _openai_api_key:
        return _call_openai(prompt, temperature, max_tokens)
    return _call_ollama(prompt, temperature, max_tokens)


# ─── Context builder ─────────────────────────────────────────────────────────

def _build_feedback_summary(store_id: str) -> str:
    """Tóm tắt các hành động đã áp dụng gần đây và kết quả."""
    from datetime import datetime, timedelta
    fb_list = db.get_action_feedback(store_id)
    cutoff = (datetime.now() - timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")
    recent = [f for f in fb_list if f.get("timestamp", "") >= cutoff]
    if not recent:
        return ""
    lines = []
    for f in recent[-6:]:
        decision_vn = "✅ Đã áp dụng" if f["decision"] == "accept" else "⏭ Bỏ qua"
        outcome_vn = ""
        if f.get("outcome") == "positive":
            outcome_vn = " → Kết quả TỐT"
        elif f.get("outcome") == "negative":
            outcome_vn = " → Kết quả CHƯA TỐT"
        lines.append(f"  {decision_vn} [{f['rule_id']}] {f['action_id']}{outcome_vn}")
    return "--- LỊCH SỬ HÀNH ĐỘNG GẦN ĐÂY (48h) ---\n" + "\n".join(lines)


def _build_store_context(store_id: str, date_str: str) -> str:
    from datetime import datetime
    store = db.get_store(store_id)
    snap = db.get_snapshot(store_id, date_str)
    roster = db.get_roster(store_id, date_str)
    staff_map = {nv["id"]: nv for nv in db.get_staff(store_id)}
    health = analytics.calc_health_score(store_id, date_str)
    cmp = analytics.compare_to_baseline(store_id, date_str)
    signals = evaluate_rules_for_store(store_id, date_str)

    if not snap or not store:
        return "Không có dữ liệu cho ngày này."

    cat_rev = snap.get("category_revenue", {})
    total_rev = snap.get("revenue", 1) or 1
    ct = snap.get("customer_type_count", {})
    total_ct = sum(ct.values()) or 1
    perf = snap.get("staff_performance", {})

    # Shift status — biết đang ở ca nào
    now = datetime.now()
    h = now.hour
    if h < 9:
        current_shift_txt = "Chưa mở cửa"
    elif h < 14:
        current_shift_txt = f"Ca sáng (đến 14:00) — {h:02d}:{now.minute:02d}"
    elif h < 20:
        current_shift_txt = f"Ca chiều (đến 20:00) — {h:02d}:{now.minute:02d}"
    elif h < 22:
        current_shift_txt = f"Ca tối (đến 22:00) — {h:02d}:{now.minute:02d}"
    else:
        current_shift_txt = "Đã đóng cửa"

    # Dự báo EOD
    from engine.analytics import predict_eod_revenue
    predicted_eod = predict_eod_revenue(store_id, snap.get("revenue", 0), h)
    predicted_pct = predicted_eod / store["daily_target"] * 100 if store["daily_target"] else 0

    def staff_names(ids): return ", ".join(staff_map.get(i, {}).get("name", i) for i in ids)
    morning = staff_names(roster.get("morning_staff", []) if roster else [])
    afternoon = staff_names(roster.get("afternoon_staff", []) if roster else [])
    evening = staff_names(roster.get("evening_staff", []) if roster else [])

    top_staff = sorted(perf.items(), key=lambda x: x[1].get("revenue", 0), reverse=True)[:3]
    top_staff_txt = "\n".join(
        f"  - {staff_map.get(sid, {}).get('name', sid)}: "
        f"{v.get('revenue', 0)/1e6:.1f} triệu đồng / {v.get('orders', 0)} đơn"
        for sid, v in top_staff
    )

    alert_txt = "\n".join(
        f"  [{s['urgency']}] {s['rule_name']}: {s['details']}"
        for s in signals[:5]
    ) if signals else "  Không có cảnh báo."

    feedback_txt = _build_feedback_summary(store_id)

    ctx = f"""
=== DỮ LIỆU CỬA HÀNG ===
Cửa hàng: {store['name']} ({store['id']})
Ngày: {snap.get('day_of_week_vn', '')} {date_str}
Thời điểm hiện tại: {current_shift_txt}
Điểm sức khỏe: {health['score']}/100 (hạng {health['grade']})

--- DOANH THU ---
Doanh thu tích lũy: {snap['revenue']/1e6:.2f} triệu đồng
Target ngày: {store['daily_target']/1e6:.0f} triệu đồng
Đạt: {snap.get('target_pct', 0)*100:.1f}% target
Dự báo EOD: {predicted_eod/1e6:.1f} triệu ({predicted_pct:.0f}% target)
Traffic: {snap['traffic']} lượt (baseline 14 ngày: {cmp.get('baseline_traffic', 0):.0f} lượt)
Tỷ lệ chuyển đổi (CR): {snap.get('conversion_rate', 0)*100:.1f}% (baseline: {cmp.get('baseline_cr', 0)*100:.1f}%)
AOV: {snap.get('aov', 0)/1e6:.2f} triệu đồng

--- CƠ CẤU DOANH THU THEO SẢN PHẨM ---
Nhẫn cưới: {cat_rev.get('wedding_ring', 0)/1e6:.1f} triệu ({cat_rev.get('wedding_ring', 0)/total_rev*100:.1f}%)
Nhẫn đính hôn: {cat_rev.get('engagement_ring', 0)/1e6:.1f} triệu ({cat_rev.get('engagement_ring', 0)/total_rev*100:.1f}%)
Nhẫn thời trang: {cat_rev.get('fashion_ring', 0)/1e6:.1f} triệu ({cat_rev.get('fashion_ring', 0)/total_rev*100:.1f}%)
Lắc tay: {cat_rev.get('bracelet', 0)/1e6:.1f} triệu ({cat_rev.get('bracelet', 0)/total_rev*100:.1f}%)
Dây chuyền: {cat_rev.get('necklace', 0)/1e6:.1f} triệu ({cat_rev.get('necklace', 0)/total_rev*100:.1f}%)
Bông tai: {cat_rev.get('earring', 0)/1e6:.1f} triệu ({cat_rev.get('earring', 0)/total_rev*100:.1f}%)
Đồng hồ: {cat_rev.get('watch', 0)/1e6:.1f} triệu ({cat_rev.get('watch', 0)/total_rev*100:.1f}%)

--- NHÓM KHÁCH ---
Cặp đôi: {ct.get('couple', 0)} lượt ({ct.get('couple', 0)/total_ct*100:.0f}%)
Nữ độc thân: {ct.get('female_solo', 0)} lượt ({ct.get('female_solo', 0)/total_ct*100:.0f}%)
Nam độc thân: {ct.get('male_solo', 0)} lượt ({ct.get('male_solo', 0)/total_ct*100:.0f}%)
Mua quà: {ct.get('gift_buyer', 0)} lượt ({ct.get('gift_buyer', 0)/total_ct*100:.0f}%)
Gia đình: {ct.get('family', 0)} lượt ({ct.get('family', 0)/total_ct*100:.0f}%)

--- ĐỘI HÌNH ---
Ca sáng (09h–14h): {morning or 'Không có dữ liệu'}
Ca chiều (14h–20h): {afternoon or 'Không có dữ liệu'}
Ca tối (20h–22h): {evening or 'Không có dữ liệu'}

--- TOP NHÂN VIÊN ---
{top_staff_txt or 'Không có dữ liệu'}

--- DOANH THU THEO CA ---
Ca sáng: {snap.get('shift_revenue', {}).get('morning', 0)/1e6:.1f} triệu
Ca chiều: {snap.get('shift_revenue', {}).get('afternoon', 0)/1e6:.1f} triệu
Ca tối: {snap.get('shift_revenue', {}).get('evening', 0)/1e6:.1f} triệu

--- CẢNH BÁO ĐANG KÍCH HOẠT ---
{alert_txt}

{feedback_txt}
=========================
"""
    return ctx.strip()


# ─── Prompts ─────────────────────────────────────────────────────────────────

def gen_health_report(store_id: str, date_str: str) -> str:
    ctx = _build_store_context(store_id, date_str)
    store = db.get_store(store_id)
    store_name = store["name"] if store else store_id

    prompt = f"""Bạn là AI Store Copilot của PNJ — trợ lý thông minh giúp Cửa hàng trưởng vận hành hiệu quả hơn.
Bạn đang phân tích dữ liệu cửa hàng {store_name} cho ngày {date_str}.

{ctx}

Hãy viết BÁO CÁO SỨC KHỎE CỬA HÀNG. Yêu cầu:
1. Tóm tắt kết quả ngày trong 2-3 câu đầu (doanh thu, traffic, CR)
2. Liệt kê 2-3 điểm MẠNH nổi bật hôm nay
3. Liệt kê 2-3 điểm CẦN CẢI THIỆN với số liệu cụ thể
4. Đưa ra 3 GỢI Ý HÀNH ĐỘNG ưu tiên cho ngày mai/ca tới
5. Kết luận ngắn gọn

Viết ngắn gọn, dùng số liệu thực tế từ dữ liệu trên. Không bịa số. Dùng gạch đầu dòng khi liệt kê.
"""
    return _call_llm(prompt, temperature=0.25)


def gen_root_cause_analysis(store_id: str, date_str: str) -> str:
    ctx = _build_store_context(store_id, date_str)
    store = db.get_store(store_id)
    store_name = store["name"] if store else store_id
    snap = db.get_snapshot(store_id, date_str)
    target_pct = snap.get("target_pct", 0) * 100 if snap else 0

    prompt = f"""Bạn là AI Store Copilot của PNJ. Cửa hàng {store_name} hôm nay ({date_str}) đạt {target_pct:.1f}% target.

{ctx}

Hãy PHÂN TÍCH NGUYÊN NHÂN tại sao kết quả hôm nay như vậy. Yêu cầu:
1. Xác định 1-2 nguyên nhân CHÍNH (dựa trên số liệu thực tế)
2. Phân tích mối quan hệ nhân quả rõ ràng (VD: Vì A → dẫn đến B → gây ra C)
3. So sánh với baseline/ngày thường để thấy rõ vấn đề
4. Xác định YẾU TỐ CÓ THỂ KIỂM SOÁT vs YẾU TỐ BÊN NGOÀI
5. Đề xuất 1-2 hành động ngắn hạn có thể làm ngay

Phân tích logic, dùng số liệu thực từ dữ liệu trên. Ngắn gọn, dễ hiểu cho người không chuyên về data.
"""
    return _call_llm(prompt, temperature=0.2)


def _build_today_plan_context(store_id: str, date_today: str,
                               date_yesterday: str) -> str:
    """
    Xây dựng context kế hoạch hôm nay cho brief:
    roster thực tế + prep signals forward-looking + SKU opportunity.
    """
    from engine.rule_engine import evaluate_today_prep_signals
    import datetime as _dt

    store = db.get_store(store_id)
    snap_yesterday = db.get_snapshot(store_id, date_yesterday)
    roster_today = db.get_roster(store_id, date_today)
    staff_map = {nv["id"]: nv for nv in db.get_staff(store_id)}

    # Ngữ cảnh ngày
    try:
        d = _dt.date.fromisoformat(date_today)
    except (ValueError, TypeError):
        d = _dt.date.today()
    dow_vn = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm",
              "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"][d.weekday()]
    dom = d.day
    month_phase = "đầu tháng" if dom <= 5 else "giữa tháng" if dom <= 20 else "cuối tháng"

    # Roster
    def _shift_detail(ids: list) -> str:
        parts = []
        for sid in ids:
            nv = staff_map.get(sid, {})
            cats = ", ".join(
                c.replace("wedding_ring", "nhẫn cưới")
                 .replace("engagement_ring", "đính hôn")
                 .replace("fashion_ring", "nhẫn TT")
                 .replace("bracelet", "lắc")
                 .replace("necklace", "dây chuyền")
                 .replace("earring", "bông tai")
                 .replace("watch", "đồng hồ")
                for c in nv.get("strong_categories", [])
            )
            parts.append(f"{nv.get('name', sid)} [{nv.get('level','').upper()[:3]}] (mạnh: {cats})")
        return ", ".join(parts) if parts else "Chưa có lịch"

    if roster_today:
        morning_txt = _shift_detail(roster_today.get("morning_staff", []))
        afternoon_txt = _shift_detail(roster_today.get("afternoon_staff", []))
        evening_txt = _shift_detail(roster_today.get("evening_staff", []))
    else:
        morning_txt = afternoon_txt = evening_txt = "Chưa có lịch"

    # Prep signals (forward-looking)
    prep_signals = evaluate_today_prep_signals(store_id, date_today, snap_yesterday)
    if prep_signals:
        sigs_txt = "\n".join(
            f"  [{s['urgency']}] {s['rule_name']}: {s['details']}"
            for s in prep_signals[:5]
        )
    else:
        sigs_txt = "  Không có cảnh báo đặc biệt."

    # Top SKU opportunity
    top_skus = analytics.get_sku_opportunity_scores(store_id, date_yesterday)
    top_skus_txt = "\n".join(
        f"  - {s['name']} ({s['id']}): giá {s['price']/1e6:.1f}M, "
        f"CVR {s.get('cvr_local', s.get('cvr_history', 0))*100:.0f}%, "
        f"margin {s['margin_pct']*100:.0f}%, tồn {s.get('stock', 0)}"
        for s in top_skus[:3] if s.get("stock", 0) > 0
    ) or "  Không có dữ liệu."

    target = store["daily_target"] / 1e6 if store else 92

    return f"""=== KẾ HOẠCH HÔM NAY ({dow_vn} {date_today} — {month_phase}) ===
Target: {target:.0f} triệu đồng

ĐỘI HÌNH HÔM NAY:
  Ca sáng   (09h–14h): {morning_txt}
  Ca chiều  (14h–20h): {afternoon_txt}
  Ca tối    (20h–22h): {evening_txt}

ĐIỂM CẦN HÀNH ĐỘNG HÔM NAY (dựa trên dữ liệu thực):
{sigs_txt}

TOP SKU CƠ HỘI HÔM NAY:
{top_skus_txt}"""


def gen_morning_brief(store_id: str, date_yesterday: str,
                      date_today: str | None = None) -> str:
    """
    Tạo brief họp ca sáng.
    date_yesterday: ngày đã hoàn thành — dùng làm retrospective.
    date_today: ngày cần lên kế hoạch — dùng làm forward plan.
    """
    ctx_yesterday = _build_store_context(store_id, date_yesterday)
    store = db.get_store(store_id)
    store_name = store["name"] if store else store_id
    target = store["daily_target"] / 1e6 if store else 92

    today_ctx = ""
    if date_today:
        today_ctx = _build_today_plan_context(store_id, date_today, date_yesterday)

    prompt = f"""Bạn là AI Store Copilot của PNJ. Hãy tạo BRIEF HỌP CA SÁNG cho {store_name}.

=== KẾT QUẢ HÔM QUA ({date_yesterday}) ===
{ctx_yesterday}

{today_ctx}

Hãy viết BRIEF HỌP CA SÁNG để Cửa hàng trưởng đọc cho team nghe (2–3 phút đọc).
Yêu cầu bắt buộc:
- Dùng số liệu THỰC TẾ từ dữ liệu trên, KHÔNG bịa số.
- Phản ánh đúng đội hình hôm nay và các điểm cần hành động đã liệt kê.
- Viết văn xuôi tự nhiên, đời thường — như đang nói chuyện trực tiếp với team.

FORMAT:

**KẾT QUẢ HÔM QUA**
[3 câu: doanh thu đạt bao nhiêu % target, điểm mạnh và điểm chưa tốt nhất]

**MỤC TIÊU HÔM NAY — {target:.0f} triệu đồng**
[1–2 câu: mục tiêu + 1 điều đặc biệt quan trọng nhất hôm nay dựa trên dữ liệu]

**3 ƯU TIÊN HÀNH ĐỘNG**
1. [Ưu tiên cụ thể — từ dữ liệu thực, nêu rõ ai làm gì]
2. [Ưu tiên cụ thể]
3. [Ưu tiên cụ thể]

**TOP SKU CẦN ĐẨY HÔM NAY**
- [SKU với lý do ngắn gọn]
- [SKU với lý do ngắn gọn]
- [SKU với lý do ngắn gọn]

**LỜI ĐỘNG VIÊN**
[1–2 câu ấm áp, cụ thể — không sáo rỗng]
"""
    return _call_llm(prompt, temperature=0.5)


def chat_with_copilot(store_id: str, date_str: str,
                      user_message: str, history: list) -> str:
    ctx = _build_store_context(store_id, date_str)
    store = db.get_store(store_id)
    store_name = store["name"] if store else store_id

    # Build conversation history
    hist_txt = ""
    for msg in history[-6:]:  # giữ 6 turns gần nhất
        role = "CHT" if msg["role"] == "user" else "AI"
        hist_txt += f"{role}: {msg['content']}\n"

    prompt = f"""Bạn là AI Store Copilot của PNJ — trợ lý thông minh cho Cửa hàng trưởng {store_name}.
Ngày hôm nay: {date_str}

DỮ LIỆU THỰC TẾ CỬA HÀNG:
{ctx}

LỊCH SỬ CUỘC HỘI THOẠI:
{hist_txt}

CHT: {user_message}
AI:"""

    response = _call_llm(prompt, temperature=0.35, max_tokens=512)
    return response


def gen_eod_summary(store_id: str, date_str: str) -> str:
    ctx = _build_store_context(store_id, date_str)
    store = db.get_store(store_id)
    store_name = store["name"] if store else store_id
    health = analytics.calc_health_score(store_id, date_str)

    prompt = f"""Bạn là AI Store Copilot của PNJ. Đây là TÓM TẮT CUỐI NGÀY cho {store_name} — ngày {date_str}.
Điểm sức khỏe hôm nay: {health['score']}/100

{ctx}

Hãy viết TÓM TẮT CUỐI NGÀY gồm:
1. Kết quả tổng thể — đạt bao nhiêu % target, so sánh với hôm qua
2. 2 quyết định/hành động HIỆU QUẢ NHẤT hôm nay (nếu có data)
3. 1-2 điều CẦN LÀM TỐT HƠN ngày mai
4. Bài học rút ra ngắn gọn
5. Dự báo sơ bộ cho ngày mai dựa trên xu hướng

Giữ ngắn gọn, súc tích, đủ để đọc trong 1 phút. Cảm ơn team cuối bài.
"""
    return _call_llm(prompt, temperature=0.3)


def gen_notification_content(store_id: str, date_str: str,
                              notif_type: str) -> tuple[str, str]:
    """Trả về (title, body) cho notification theo loại."""
    ctx = _build_store_context(store_id, date_str)
    store = db.get_store(store_id)
    store_name = store["name"] if store else store_id

    type_map = {
        "morning": ("Báo cáo sáng 07:30",
                    "Tóm tắt kết quả hôm qua và 3 gợi ý hành động cho hôm nay"),
        "midday": ("Cập nhật giữa ca 11:30",
                   "Tiến độ doanh thu và gợi ý điều chỉnh nhỏ"),
        "afternoon": ("Cảnh báo trước cao điểm 15:30",
                      "Dự báo traffic và chuẩn bị đội hình tối ưu"),
        "eod": ("Tổng kết cuối ngày 21:15",
                "Kết quả và bài học cho ngày mai"),
    }
    title, desc = type_map.get(notif_type, ("Thông báo", ""))

    prompt = f"""Bạn là AI Store Copilot PNJ. Viết thông báo ngắn ({desc}) cho {store_name}.

{ctx}

Viết thông báo NGẮN (3-4 câu), dùng số liệu thực tế. Thẳng vào vấn đề, không dài dòng.
Chỉ trả lời phần nội dung thông báo, không cần tiêu đề.
"""
    body = _call_llm(prompt, temperature=0.3, max_tokens=256)
    return title, body
