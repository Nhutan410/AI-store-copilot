"""
AI-powered daily data simulator.
- OpenAI tạo kịch bản ngày (thời tiết, sự kiện, anomaly).
- Python generate transactions + snapshot + roster theo kịch bản.
- Hỗ trợ sinh dữ liệu từng ca (sáng/chiều/tối) dựa theo giờ thực tế.
- Sử dụng lịch sử feedback của ca trước để điều chỉnh tham số ca tiếp theo.
"""
import json
import random
import re
from datetime import date, datetime, timedelta
from engine import db, llm

CUSTOMER_TYPES = ["couple", "female_solo", "male_solo", "gift_buyer", "family"]

CATEGORY_CUSTOMER_MAP = {
    "couple":      ["wedding_ring", "engagement_ring", "necklace", "bracelet"],
    "female_solo": ["fashion_ring", "bracelet", "necklace", "earring"],
    "male_solo":   ["fashion_ring", "accessory", "necklace", "bracelet"],
    "gift_buyer":  ["earring", "bracelet", "accessory", "fashion_ring"],
    "family":      ["necklace", "bracelet", "earring", "fashion_ring", "accessory"],
}

# Tỷ lệ tích lũy doanh thu theo giờ (0–1)
HOUR_CUMULATIVE = {
    9: 0.06, 10: 0.14, 11: 0.23, 12: 0.30, 13: 0.36,
    14: 0.44, 15: 0.53, 16: 0.62, 17: 0.74, 18: 0.87,
    19: 0.97, 20: 0.99, 21: 1.00,
}

# Định nghĩa 3 ca theo CLAUDE.md
SHIFTS = [
    {"name": "morning",   "start": 9,  "end": 14, "label": "Ca sáng (09h–14h)"},
    {"name": "afternoon", "start": 14, "end": 20, "label": "Ca chiều (14h–20h)"},
    {"name": "evening",   "start": 20, "end": 22, "label": "Ca tối (20h–22h)"},
]

# Hiệu ứng của từng action lên tham số simulation ca tiếp theo
_ACTION_EFFECTS: dict = {
    "focus_wedding_sku":             {"wedding_couple_boost": 0.15, "label": "Tập trung nhẫn cưới"},
    "add_strong_staff_to_peak":      {"cr_boost": 0.10, "label": "Bổ sung NV mạnh"},
    "reassign_senior_to_peak":       {"cr_boost": 0.12, "wedding_couple_boost": 0.10, "label": "Senior vào cao điểm"},
    "reassign_staff_strong_category":{"cr_boost": 0.09, "label": "Phân NV đúng nhóm khách"},
    "change_sales_pitch":            {"cr_boost": 0.08, "label": "Đổi cách tư vấn"},
    "change_sales_pitch_self_reward":{"female_solo_adj": 0.05, "cr_boost": 0.06, "label": "Pitch tự thưởng"},
    "simplify_choice_set":           {"cr_boost": 0.07, "label": "Đơn giản hóa lựa chọn"},
    "focus_emotional_selling":       {"wedding_couple_boost": 0.08, "upsell_boost": 0.10, "label": "Bán cảm xúc"},
    "focus_high_margin_sku":         {"upsell_boost": 0.12, "label": "Tập trung SKU margin cao"},
    "suggest_installment_option":    {"upsell_boost": 0.15, "label": "Gợi ý trả góp"},
    "mini_activation":               {"traffic_boost": 0.15, "cr_boost": 0.05, "label": "Mini campaign"},
    "activate_closing_push":         {"cr_boost": 0.10, "upsell_boost": 0.08, "label": "Push cuối ngày"},
    "activate_social_sharing_incentive": {"traffic_boost": 0.10, "label": "Khuyến khích chia sẻ"},
    "pair_junior_with_senior":       {"cr_boost": 0.07, "label": "Ghép cặp NV"},
    "buddy_system_coaching":         {"cr_boost": 0.05, "label": "Coaching tại chỗ"},
    "suggest_proactive_greeting":    {"traffic_boost": 0.10, "label": "Chủ động chào hỏi"},
    "feature_slow_moving_sku":       {"upsell_boost": 0.05, "label": "Trưng bày hàng chậm"},
    "suggest_display_change":        {"upsell_boost": 0.04, "label": "Đổi vị trí trưng bày"},
    "focus_mid_price_sku":           {"upsell_boost": 0.06, "label": "Focus SKU tầm trung"},
    "coach_upsell_technique":        {"upsell_boost": 0.08, "label": "Coach upsell"},
}


# ─── OpenAI call ──────────────────────────────────────────────────────────────

_VI_ENFORCE = (
    "QUAN TRỌNG: Chỉ trả lời bằng tiếng Việt. Không dùng tiếng Trung hay ngôn ngữ khác.\n\n"
)

def _call_openai_for_scenario(prompt: str, temperature: float = 0.7) -> str:
    response = llm.generate_text(_VI_ENFORCE + prompt, temperature=temperature, max_tokens=512)
    if response.startswith("⚠️"):
        return ""
    return response


def check_openai() -> bool:
    return llm.is_openai_enabled()


# ─── Shift status helper ──────────────────────────────────────────────────────

def get_shift_status(now: datetime | None = None) -> dict:
    """
    Trả về trạng thái từng ca cho thời điểm now.
    completed: ca đã kết thúc hoàn toàn
    active:    ca đang diễn ra (chỉ generate đến giờ hiện tại)
    upcoming:  ca chưa bắt đầu (không generate)
    active_max_hour: giờ tối đa để generate (exclusive) khi có ca active
    """
    if now is None:
        now = datetime.now()
    h = now.hour
    status: dict = {"active_max_hour": h}
    for shift in SHIFTS:
        if h >= shift["end"]:
            status[shift["name"]] = "completed"
        elif h >= shift["start"]:
            status[shift["name"]] = "active"
        else:
            status[shift["name"]] = "upcoming"
    return status


# ─── Feedback adjustments ─────────────────────────────────────────────────────

def get_feedback_adjustments(store_id: str,
                              for_date: str | None = None,
                              lookback_hours: int = 48) -> dict:
    """
    Đọc lịch sử hành động đã áp dụng (accept) trong lookback_hours giờ qua.
    Trả về dict tham số điều chỉnh để apply vào simulation ca tiếp theo.
    """
    cutoff_ts = (datetime.now() - timedelta(hours=lookback_hours)).strftime("%Y-%m-%d %H:%M:%S")
    fb_list = db.get_action_feedback(store_id)

    # Lọc theo ngày nếu cần (chỉ lấy feedback trong ngày hôm nay)
    recent_accepted = [
        f for f in fb_list
        if f.get("decision") == "accept"
        and f.get("timestamp", "") >= cutoff_ts
        and (for_date is None or f.get("timestamp", "")[:10] == for_date)
    ]

    # Khởi tạo với giá trị neutral
    adj: dict = {
        "cr_boost":             1.0,   # Nhân với CR cơ bản của NV
        "wedding_couple_boost": 1.0,   # Nhân với xác suất couple mua nhẫn cưới
        "female_solo_adj":      0.0,   # Cộng vào tỷ lệ nữ độc thân
        "traffic_boost":        1.0,   # Nhân với traffic multiplier
        "upsell_boost":         1.0,   # Nhân với actual_price (giả lập upsell)
        "applied_actions":      [],    # Danh sách action đã áp dụng để log
    }

    for fb in recent_accepted:
        action_id = fb.get("action_id", "")
        effects = _ACTION_EFFECTS.get(action_id, {})
        for key, delta in effects.items():
            if key == "label":
                adj["applied_actions"].append(effects["label"])
            elif key in adj:
                if key == "female_solo_adj":
                    adj[key] += delta
                else:
                    adj[key] *= (1 + delta)

    # Giới hạn để tránh over-boost
    adj["cr_boost"]             = min(adj["cr_boost"], 1.40)
    adj["wedding_couple_boost"] = min(adj["wedding_couple_boost"], 1.80)
    adj["traffic_boost"]        = min(adj["traffic_boost"], 1.30)
    adj["upsell_boost"]         = min(adj["upsell_boost"], 1.35)
    adj["female_solo_adj"]      = max(-0.10, min(adj["female_solo_adj"], 0.15))

    return adj


# ─── Scenario generation ──────────────────────────────────────────────────────

def _parse_scenario(text: str) -> dict:
    def _extract(key: str, default: str) -> str:
        m = re.search(rf"{key}:\s*(.+)", text)
        return m.group(1).strip() if m else default

    def _float(s: str, default: float) -> float:
        try:
            return float(re.sub(r"[^\d.\-+]", "", s))
        except Exception:
            return default

    weather_raw = _extract("THOI_TIET", _extract("THỜI_TIẾT", "âm u"))
    traffic_mult = _float(_extract("TRAFFIC_MULT", "1.0"), 1.0)
    couple_adj = _float(_extract("COUPLE_ADJ", "+0.00"), 0.0)
    female_adj = _float(_extract("FEMALE_SOLO_ADJ", "+0.00"), 0.0)
    event = _extract("SU_KIEN", _extract("SỰ_KIỆN", "không có"))
    staff_issue = _extract("VAN_DE_NHAN_VIEN", _extract("VẤN_ĐỀ_NHÂN_VIÊN", "không có"))
    hot_cat = _extract("DANH_MUC_HOT", _extract("DANH_MỤC_HOT", "không có"))
    cat_mult = _float(_extract("CATEGORY_MULT", "1.0"), 1.0)
    promo_raw = _extract("PROMO", "không")
    description = _extract("MO_TA", _extract("MÔ_TẢ", "Ngày bình thường."))

    traffic_mult = max(0.50, min(1.60, traffic_mult))
    couple_adj = max(-0.15, min(0.20, couple_adj))
    female_adj = max(-0.12, min(0.15, female_adj))
    cat_mult = max(1.0, min(2.5, cat_mult))

    valid_cats = {"wedding_ring", "engagement_ring", "fashion_ring",
                  "bracelet", "necklace", "earring", "accessory", "watch"}
    if hot_cat.lower() not in valid_cats:
        hot_cat = None

    return {
        "weather": weather_raw,
        "traffic_mult": traffic_mult,
        "couple_adj": couple_adj,
        "female_solo_adj": female_adj,
        "event": event if "không" not in event.lower() else None,
        "staff_issue": staff_issue if "không" not in staff_issue.lower() else None,
        "hot_category": hot_cat,
        "hot_category_mult": cat_mult if hot_cat else 1.0,
        "promo_active": "có" in promo_raw.lower(),
        "description": description,
    }


def _random_scenario(store: dict, sim_date: date) -> dict:
    dow = sim_date.weekday()
    is_weekend = dow in (5, 6)
    is_monday = dow == 0
    day_of_month = sim_date.day

    weather_choices = ["nắng", "nắng", "âm u", "mưa nhẹ", "mưa to"]
    weather = random.choice(weather_choices)
    weather_mult = {"nắng": 1.05, "âm u": 0.95, "mưa nhẹ": 0.88, "mưa to": 0.70}[weather]

    base_mult = 1.35 if is_weekend else (0.75 if is_monday else 1.0)
    traffic_mult = base_mult * weather_mult * random.uniform(0.88, 1.12)

    if 1 <= day_of_month <= 5:
        traffic_mult *= 1.15
    elif day_of_month >= 25:
        traffic_mult *= 0.90

    events_pool = [
        "Sale cuối tuần tại TTTM", "Tuần lễ vàng PNJ",
        "Sự kiện khai trương gần đó", "Ngày lễ địa phương",
        None, None, None, None,
    ]
    event = random.choice(events_pool)
    if event:
        traffic_mult *= random.uniform(1.15, 1.40)

    couple_adj = random.uniform(-0.08, 0.12)
    female_adj = random.uniform(-0.06, 0.10)

    cats = ["wedding_ring", "fashion_ring", "bracelet", "necklace", "earring", None, None]
    hot_cat = random.choice(cats)
    cat_mult = random.uniform(1.2, 1.8) if hot_cat else 1.0

    staff_issues = [
        "Một TVV xin nghỉ phép đột xuất",
        "TVV mới phụ trách quầy chính vì senior bị ốm",
        None, None, None, None,
    ]
    staff_issue = random.choice(staff_issues)
    promo_active = random.random() < 0.25

    description = (
        f"Ngày {sim_date.strftime('%d/%m/%Y')}, thời tiết {weather}. "
        f"{'Có sự kiện: ' + event + '.' if event else 'Không có sự kiện đặc biệt.'}"
        f"{' ' + staff_issue + '.' if staff_issue else ''}"
    )

    return {
        "weather": weather,
        "traffic_mult": round(max(0.50, min(1.60, traffic_mult)), 2),
        "couple_adj": round(couple_adj, 3),
        "female_solo_adj": round(female_adj, 3),
        "event": event,
        "staff_issue": staff_issue,
        "hot_category": hot_cat,
        "hot_category_mult": round(cat_mult, 2),
        "promo_active": promo_active,
        "description": description,
    }


def generate_scenario(store_id: str, sim_date: date,
                      adjustments: dict | None = None,
                      progress_cb=None) -> dict:
    """Gọi OpenAI để tạo kịch bản ngày. Fallback random nếu chưa có API key/lỗi API.
    Nhận adjustments từ feedback ca trước để làm ngữ cảnh cho OpenAI."""
    store = db.get_store(store_id)
    if not store:
        return _random_scenario({"segment": "A"}, sim_date)

    if progress_cb:
        progress_cb("Đang tạo kịch bản với AI...")

    dow_vn = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm",
               "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"][sim_date.weekday()]

    # Thêm context feedback vào prompt OpenAI
    feedback_ctx = ""
    if adjustments and adjustments.get("applied_actions"):
        acts = ", ".join(adjustments["applied_actions"])
        feedback_ctx = f"\nCA TRƯỚC ĐÃ ÁP DỤNG: {acts}. Hãy phản ánh hiệu quả của các hành động này vào kịch bản ca tiếp theo.\n"

    prompt = f"""Bạn là hệ thống sinh kịch bản mô phỏng bán lẻ trang sức PNJ.

CỬA HÀNG: {store['name']} (Phân khúc {store['segment']}, {store['city']})
KHÁCH HÀNG THƯỜNG: {store.get('customer_profile', '')}
NGÀY MÔ PHỎNG: {sim_date.isoformat()} ({dow_vn})
TARGET NGÀY: {store['daily_target']:,} đồng
{feedback_ctx}
Tạo kịch bản thực tế với yếu tố BẤT THƯỜNG (có thể tốt hoặc xấu). Xuất theo ĐÚNG format:
---
THOI_TIET: [nắng|âm u|mưa nhẹ|mưa to]
TRAFFIC_MULT: [số từ 0.55 đến 1.55]
COUPLE_ADJ: [số từ -0.12 đến +0.15]
FEMALE_SOLO_ADJ: [số từ -0.10 đến +0.12]
SU_KIEN: [tên sự kiện ngắn bằng tiếng Việt hoặc không có]
VAN_DE_NHAN_VIEN: [mô tả ngắn bằng tiếng Việt hoặc không có]
DANH_MUC_HOT: [wedding_ring|fashion_ring|bracelet|necklace|earring|accessory hoặc không có]
CATEGORY_MULT: [số từ 1.0 đến 2.2]
PROMO: [có|không]
MO_TA: [2 câu tiếng Việt mô tả kịch bản ngày hôm đó]
---"""

    raw = _call_openai_for_scenario(prompt, temperature=0.75)
    if not raw:
        return _random_scenario(store, sim_date)

    scenario = _parse_scenario(raw)

    # Nếu parse thất bại (toàn default) thì dùng random
    if scenario["traffic_mult"] == 1.0 and not scenario.get("event"):
        fallback = _random_scenario(store, sim_date)
        fallback["description"] = scenario.get("description") or fallback["description"]
        return fallback

    return scenario


# ─── Traffic & hourly distribution ───────────────────────────────────────────

def _base_traffic(store: dict, sim_date: date) -> int:
    base = {"A": 130, "B": 95, "C": 70}[store["segment"]]
    dow = sim_date.weekday()
    if dow == 0:
        mult = 0.75
    elif dow in (5, 6):
        mult = 1.35
    else:
        mult = 1.0
    return max(8, int(base * mult))


def _hourly_distribution(total: int, max_hour: int = 22,
                         current_minute: int = 0) -> dict:
    """
    Phân bổ traffic đến thời điểm max_hour:current_minute.

    Các giờ trước max_hour được tính đầy đủ. Riêng max_hour chỉ được tính theo
    tỷ lệ số phút đã trôi qua, nhờ đó 09:45 vẫn có dữ liệu của 45 phút đầu ngày.
    """
    weights = {
        9: 0.06, 10: 0.08, 11: 0.09, 12: 0.07,
        13: 0.06, 14: 0.08, 15: 0.09, 16: 0.09,
        17: 0.12, 18: 0.13, 19: 0.10, 20: 0.02, 21: 0.01,
    }
    minute_fraction = max(0, min(current_minute, 59)) / 60
    valid_hours = {}
    for hour, weight in weights.items():
        if hour < max_hour:
            valid_hours[hour] = weight
        elif hour == max_hour and minute_fraction > 0:
            valid_hours[hour] = weight * minute_fraction

    if not valid_hours:
        return {}

    # Scale lại tổng traffic theo tỷ trọng giờ đã qua
    total_weight = sum(valid_hours.values())
    full_weight = sum(weights.values())
    scaled_total = max(0, int(total * total_weight / full_weight))

    dist = {}
    remaining = scaled_total
    hours = sorted(valid_hours.keys())
    for h in hours[:-1]:
        v = max(0, int(scaled_total * valid_hours[h] / total_weight * random.uniform(0.85, 1.15)))
        dist[h] = min(v, remaining)
        remaining -= dist[h]
    dist[hours[-1]] = max(0, remaining)
    return dist


# ─── Roster generation ────────────────────────────────────────────────────────

def _gen_roster_for_day(store_id: str, sim_date: date,
                         staff_issue: str | None) -> dict:
    staff_all = db.get_staff(store_id)
    seniors = [s["id"] for s in staff_all if s["level"] == "senior"]
    others = [s["id"] for s in staff_all if s["level"] != "senior"]
    all_ids = [s["id"] for s in staff_all]

    is_weekend = sim_date.weekday() in (5, 6)
    morning_size = 3 if is_weekend else 2
    afternoon_size = 4 if is_weekend else 3
    evening_size = 2

    has_senior_issue = bool(staff_issue) and random.random() < 0.6

    if store_id == "STR-002":
        bao_ngoc = "NV001"
        thu_huong = "NV007"
        wedding_seniors = [bao_ngoc, thu_huong]
        if has_senior_issue:
            morning_pool = [bao_ngoc] + [n for n in others if n != thu_huong]
            afternoon_pool = [n for n in all_ids if n not in wedding_seniors]
            evening_pool = [thu_huong] + [n for n in others if n not in morning_pool[:morning_size]]
        else:
            morning_pool = [n for n in all_ids if n not in [bao_ngoc, thu_huong]]
            afternoon_pool = [bao_ngoc, thu_huong] + others
            evening_pool = [n for n in all_ids
                            if n not in morning_pool[:morning_size]
                            and n not in afternoon_pool[:afternoon_size]]
        morning_staff = morning_pool[:morning_size]
        afternoon_staff = afternoon_pool[:afternoon_size]
        evening_staff = evening_pool[:evening_size]
    else:
        shuffled = list(all_ids)
        random.shuffle(shuffled)
        if has_senior_issue and seniors:
            senior_afternoon = []
            other_afternoon = [n for n in shuffled if n not in seniors]
        else:
            senior_afternoon = seniors[:1] if seniors else []
            other_afternoon = [n for n in shuffled if n not in senior_afternoon]

        morning_staff = (seniors[1:2] + others)[:morning_size]
        afternoon_staff = (senior_afternoon + other_afternoon)[:afternoon_size]
        evening_staff = [n for n in shuffled
                         if n not in morning_staff and n not in afternoon_staff][:evening_size]

    return {
        "date": sim_date.isoformat(),
        "store_id": store_id,
        "morning_staff": morning_staff,
        "morning_start": "09:00", "morning_end": "14:00",
        "afternoon_staff": afternoon_staff,
        "afternoon_start": "14:00", "afternoon_end": "20:00",
        "evening_staff": evening_staff,
        "evening_start": "20:00", "evening_end": "22:00",
    }


# ─── Transaction generation ───────────────────────────────────────────────────

def _pick_sku_sim(skus_inv: list, customer_type: str,
                  hot_category: str | None, hot_mult: float,
                  wedding_couple_boost: float = 1.0) -> dict | None:
    preferred_cats = CATEGORY_CUSTOMER_MAP.get(customer_type, ["fashion_ring"])
    eligible = [s for s in skus_inv
                if s["category"] in preferred_cats and s.get("stock", 0) > 0]

    # Couple → nhẫn cưới/đính hôn
    base_wedding_prob = 0.28 * wedding_couple_boost
    if customer_type == "couple" and random.random() < min(0.65, base_wedding_prob):
        wedding = [s for s in skus_inv
                   if s["category"] in ["wedding_ring", "engagement_ring"]
                   and s.get("stock", 0) > 0]
        if wedding:
            eligible = wedding

    if not eligible:
        eligible = [s for s in skus_inv if s.get("stock", 0) > 0]
    if not eligible:
        return None

    weights = []
    for s in eligible:
        w = s.get("cvr_local", s.get("cvr_history", 0.4))
        if hot_category and s["category"] == hot_category:
            w *= hot_mult
        pos = s.get("display_position", "standard")
        if pos == "front":
            w *= 1.3
        elif pos == "vault":
            w *= 0.6
        weights.append(max(0.01, w))

    return random.choices(eligible, weights=weights, k=1)[0]


def _gen_transactions_sim(store_id: str, store: dict, sim_date: date,
                           roster: dict, scenario: dict,
                           max_hour: int = 22,
                           current_minute: int = 0,
                           adjustments: dict | None = None) -> tuple[list, int]:
    """
    Sinh transactions cho một ngày (hoặc một phần ngày đến max_hour).
    adjustments: tham số điều chỉnh từ feedback ca trước.
    """
    adj = adjustments or {}
    cr_boost = adj.get("cr_boost", 1.0)
    wedding_couple_boost = adj.get("wedding_couple_boost", 1.0)
    female_solo_adj = adj.get("female_solo_adj", 0.0)
    traffic_boost = adj.get("traffic_boost", 1.0)
    upsell_boost = adj.get("upsell_boost", 1.0)

    skus_inv = db.get_skus_with_inventory(store_id)
    staff_map = {s["id"]: s for s in db.get_staff(store_id)}

    base_traffic = _base_traffic(store, sim_date)
    raw_traffic = max(5, int(base_traffic
                             * scenario["traffic_mult"]
                             * traffic_boost
                             * random.uniform(0.92, 1.08)))

    # Phân bổ traffic đến đúng giờ/phút hiện tại.
    hourly = _hourly_distribution(
        raw_traffic,
        max_hour=max_hour,
        current_minute=current_minute,
    )
    actual_traffic = sum(hourly.values())

    ds = sim_date.isoformat()

    # Tỷ lệ nhóm khách
    couple_base = 0.22
    female_base = 0.35
    couple_pct = max(0.05, min(0.55, couple_base + scenario.get("couple_adj", 0)))
    female_pct = max(0.10, min(0.55,
                               female_base + scenario.get("female_solo_adj", 0) + female_solo_adj))
    remaining = max(0.0, 1.0 - couple_pct - female_pct)
    ct_weights = [couple_pct, female_pct, remaining * 0.45, remaining * 0.35, remaining * 0.20]

    hot_cat = scenario.get("hot_category")
    hot_mult = scenario.get("hot_category_mult", 1.0)
    promo_rate = 0.18 if scenario.get("promo_active") else 0.10
    cr_calibration = 0.68

    inv_local = {s["id"]: s.get("stock", 0) for s in skus_inv}

    txns = []
    existing_count = db.count_transactions_total()
    txn_id = existing_count + 1

    for hour, count in hourly.items():
        if count == 0:
            continue
        if 9 <= hour < 14:
            shift = "morning"
            staff_ids = roster.get("morning_staff", [])
        elif 14 <= hour < 20:
            shift = "afternoon"
            staff_ids = roster.get("afternoon_staff", [])
        else:
            shift = "evening"
            staff_ids = roster.get("evening_staff", [])

        if not staff_ids:
            staff_ids = [s["id"] for s in db.get_staff(store_id)][:2]

        for _ in range(count):
            ctype = random.choices(CUSTOMER_TYPES, weights=ct_weights)[0]
            staff_id = random.choice(staff_ids)
            nv = staff_map.get(staff_id, {})
            base_cr = nv.get("avg_cr", 0.35)

            preferred = CATEGORY_CUSTOMER_MAP.get(ctype, [])
            strong = nv.get("strong_categories", [])
            if any(c in strong for c in preferred):
                cr = base_cr * 1.15
            else:
                cr = base_cr

            if scenario.get("staff_issue"):
                cr *= random.uniform(0.80, 0.95)

            # Áp dụng feedback boost
            cr *= cr_boost * cr_calibration

            if random.random() > cr:
                continue

            skus_avail = [s for s in skus_inv
                          if inv_local.get(s["id"], 0) > 0 or s["id"] == "PK-002"]
            sku = _pick_sku_sim(skus_avail, ctype, hot_cat, hot_mult,
                                 wedding_couple_boost=wedding_couple_boost)
            if not sku:
                continue

            if sku["id"] != "PK-002":
                inv_local[sku["id"]] = max(0, inv_local.get(sku["id"], 1) - 1)

            has_promo = random.random() < promo_rate
            base_price = sku["price"] * (0.93 if has_promo else 1.0)
            # Upsell boost: nhẹ tăng actual price (giả lập khách nâng cấp)
            actual_price = round(base_price * random.uniform(0.97, 1.0 + (upsell_boost - 1) * 0.5) / 1000) * 1000

            minute_limit = current_minute - 1 if hour == max_hour else 59
            minute = random.randint(0, max(0, minute_limit))
            second = random.randint(0, 59)
            ts = f"{ds} {hour:02d}:{minute:02d}:{second:02d}"

            txns.append({
                "id": f"TXN-{txn_id:06d}",
                "store_id": store_id,
                "date": ds,
                "timestamp": ts,
                "hour": hour,
                "shift": shift,
                "sku_id": sku["id"],
                "category": sku["category"],
                "quantity": 1,
                "unit_price": sku["price"],
                "actual_price": actual_price,
                "staff_id": staff_id,
                "customer_type": ctype,
                "has_promotion": has_promo,
                "simulated": True,
            })
            txn_id += 1

    return txns, actual_traffic


# ─── Snapshot computation ─────────────────────────────────────────────────────

def _compute_snapshot(store_id: str, store: dict, sim_date: date,
                       txns: list, traffic: int, roster: dict,
                       is_partial: bool = False) -> dict:
    staff_map = {s["id"]: s for s in db.get_staff(store_id)}
    ds = sim_date.isoformat()
    dow_vn = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm",
               "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"][sim_date.weekday()]

    total_rev = sum(t["actual_price"] for t in txns)
    num_txns = len(txns)
    target = store["daily_target"]
    cr = num_txns / traffic if traffic > 0 else 0
    aov = total_rev / num_txns if num_txns > 0 else 0

    cat_rev: dict = {}
    ct_count: dict = {}
    shift_rev: dict = {"morning": 0, "afternoon": 0, "evening": 0}
    staff_perf: dict = {}

    for t in txns:
        cat_rev[t["category"]] = cat_rev.get(t["category"], 0) + t["actual_price"]
        ct_count[t["customer_type"]] = ct_count.get(t["customer_type"], 0) + 1
        shift_rev[t["shift"]] = shift_rev.get(t["shift"], 0) + t["actual_price"]
        sid = t["staff_id"]
        if sid not in staff_perf:
            staff_perf[sid] = {
                "revenue": 0, "orders": 0,
                "name": staff_map.get(sid, {}).get("name", sid),
            }
        staff_perf[sid]["revenue"] += t["actual_price"]
        staff_perf[sid]["orders"] += 1

    return {
        "date": ds,
        "store_id": store_id,
        "target": target,
        "revenue": total_rev,
        "target_pct": total_rev / target if target > 0 else 0,
        "traffic": traffic,
        "num_transactions": num_txns,
        "conversion_rate": cr,
        "aov": aov,
        "category_revenue": cat_rev,
        "customer_type_count": ct_count,
        "shift_revenue": shift_rev,
        "staff_performance": staff_perf,
        "morning_staff": roster.get("morning_staff", []),
        "afternoon_staff": roster.get("afternoon_staff", []),
        "evening_staff": roster.get("evening_staff", []),
        "day_of_week": sim_date.strftime("%A"),
        "day_of_week_vn": dow_vn,
        "is_special_day": False,
        "special_day_multiplier": 1.0,
        "simulated": True,
        "is_partial_day": is_partial,
    }


# ─── Missing dates ────────────────────────────────────────────────────────────

def get_missing_dates(store_id: str) -> list[date]:
    """Trả về list ngày chưa có data từ ngày mới nhất đến hôm nay."""
    latest = db.get_latest_data_date(store_id)
    today = date.today()
    if not latest:
        return [today]
    latest_date = date.fromisoformat(latest)
    if latest_date >= today:
        return []
    missing = []
    d = latest_date + timedelta(days=1)
    while d <= today:
        missing.append(d)
        d += timedelta(days=1)
    return missing


# ─── Remove existing data for a date ─────────────────────────────────────────

def _clear_day_data(store_id: str, date_str: str):
    """Xóa transactions + snapshot cũ của một ngày trước khi regenerate."""
    from engine.db import _load, _save

    # Xóa transactions
    txns = _load("transactions.json", [])
    removed_txns = [
        t for t in txns
        if t["store_id"] == store_id and t["date"] == date_str
    ]
    db.restore_inventory_before_regeneration(store_id, removed_txns)
    txns_new = [t for t in txns if not (t["store_id"] == store_id and t["date"] == date_str)]
    _save("transactions.json", txns_new)

    # Xóa snapshot (append_snapshot sẽ thay thế, nhưng xóa trước để tránh duplicate)
    snaps = _load("snapshots.json", [])
    snaps_new = [s for s in snaps if not (s["store_id"] == store_id and s["date"] == date_str)]
    _save("snapshots.json", snaps_new)


# ─── Main simulation entry point ──────────────────────────────────────────────

def run_simulation(store_id: str, target_dates: list[date] | None = None,
                   progress_cb=None) -> dict:
    """
    Chạy simulation cho các ngày còn thiếu (hoặc target_dates cụ thể).

    Đối với ngày hôm nay:
    - Chỉ generate dữ liệu đến giờ hiện tại (không vượt quá thời gian thực)
    - Chia theo ca: ca sáng (09–14), ca chiều (14–20), ca tối (20–22)
    - Sử dụng feedback actions đã áp dụng trong ngày để điều chỉnh tham số

    Đối với ngày quá khứ:
    - Generate đầy đủ cả ngày (22:00)
    """
    store = db.get_store(store_id)
    if not store:
        return {"error": "Không tìm thấy cửa hàng."}

    if target_dates is None:
        target_dates = get_missing_dates(store_id)

    if not target_dates:
        return {"message": "Dữ liệu đã cập nhật đến hôm nay.", "dates_generated": 0}

    now = datetime.now()
    today = date.today()
    total_txns = 0
    scenarios_out = []

    for sim_date in target_dates:
        ds = sim_date.isoformat()
        is_today = (sim_date == today)

        if is_today:
            # Chỉ generate đến giờ hiện tại
            max_hour = now.hour
            current_minute = now.minute
            shift_status = get_shift_status(now)
            is_partial = True

            if max_hour < 9:
                if progress_cb:
                    progress_cb(f"Cửa hàng chưa mở cửa hôm nay (giờ hiện tại {now.hour:02d}:{now.minute:02d})")
                continue

            # Mô tả shift đang generate
            active_shifts = []
            for s in SHIFTS:
                st = shift_status.get(s["name"], "upcoming")
                if st in ("completed", "active"):
                    active_shifts.append(s["label"])
            shift_desc = ", ".join(active_shifts) if active_shifts else "không có ca nào"

            if progress_cb:
                progress_cb(
                    f"Ngày hôm nay {ds} — tạo dữ liệu đến {now.hour:02d}:{now.minute:02d} "
                    f"({shift_desc})"
                )

            # Lấy feedback adjustments từ actions đã áp dụng trong ngày hôm nay
            adjustments = get_feedback_adjustments(store_id, for_date=ds, lookback_hours=24)
            if progress_cb and adjustments.get("applied_actions"):
                acts = ", ".join(adjustments["applied_actions"])
                progress_cb(f"Áp dụng hiệu ứng từ ca trước: {acts}")
        else:
            # Ngày quá khứ: generate cả ngày
            max_hour = 22
            current_minute = 0
            is_partial = False
            adjustments = get_feedback_adjustments(store_id, for_date=ds, lookback_hours=48)
            if progress_cb:
                progress_cb(f"Đang tạo dữ liệu ngày {ds}...")

        # Xóa data cũ cho ngày này (để regenerate sạch)
        _clear_day_data(store_id, ds)

        replenished = db.replenish_inventory_for_simulation(store_id)
        if progress_cb and replenished:
            progress_cb(
                f"Đã nhập bù {replenished} SKU do tồn kho mô phỏng xuống quá thấp."
            )

        if progress_cb:
            progress_cb("Đang tạo kịch bản ngày với AI...")

        # 1. Sinh kịch bản (kèm feedback context)
        scenario = generate_scenario(store_id, sim_date, adjustments=adjustments,
                                     progress_cb=progress_cb)

        # 2. Sinh roster
        roster = _gen_roster_for_day(store_id, sim_date, scenario.get("staff_issue"))

        # 3. Sinh transactions (giới hạn đến max_hour, áp dụng adjustments)
        if progress_cb:
            progress_cb(
                f"Đang tạo giao dịch đến {max_hour:02d}:{current_minute:02d}..."
            )
        txns, traffic = _gen_transactions_sim(
            store_id, store, sim_date, roster, scenario,
            max_hour=max_hour,
            current_minute=current_minute,
            adjustments=adjustments,
        )

        # 4. Tính snapshot
        snapshot = _compute_snapshot(store_id, store, sim_date, txns, traffic, roster,
                                     is_partial=is_partial)

        # 5. Lưu vào DB
        db.append_transactions(txns)
        db.append_snapshot(snapshot)
        db.append_roster(roster)

        # 6. Cập nhật inventory
        db.bulk_update_inventory_after_sales(store_id, txns)

        total_txns += len(txns)

        # Thông tin shift để hiển thị trong UI
        shift_info = {}
        if is_today:
            for s in SHIFTS:
                st = shift_status.get(s["name"], "upcoming")
                shift_rev = snapshot.get("shift_revenue", {}).get(s["name"], 0)
                shift_info[s["name"]] = {"status": st, "revenue": shift_rev}

        scenarios_out.append({
            "date": ds,
            "scenario": scenario,
            "revenue": snapshot["revenue"],
            "target_pct": round(snapshot["target_pct"] * 100, 1),
            "traffic": traffic,
            "transactions": len(txns),
            "cr": round(snapshot["conversion_rate"] * 100, 1),
            "is_partial": is_partial,
            "max_hour": max_hour,
            "current_minute": current_minute,
            "shift_info": shift_info,
            "feedback_applied": adjustments.get("applied_actions", []),
        })

        if progress_cb:
            rev_m = snapshot["revenue"] / 1e6
            pct = snapshot["target_pct"] * 100
            partial_note = (
                f" (đến {max_hour:02d}:{current_minute:02d})"
                if is_partial else ""
            )
            progress_cb(
                f"✓ {ds}{partial_note}: {rev_m:.1f}M đ / {pct:.0f}% target "
                f"/ {len(txns)} giao dịch"
            )

    return {
        "dates_generated": len(scenarios_out),
        "total_transactions": total_txns,
        "scenarios": scenarios_out,
        "store_name": store["name"],
    }
