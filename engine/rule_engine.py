"""
Rule Engine: chạy 12 rules, trả về danh sách signals triggered.
"""
from engine import db, analytics


def evaluate_rules(store_id: str, date_str: str) -> list[dict]:
    """
    Chạy toàn bộ rule engine cho store + ngày.
    Trả về list signals (rule triggered + actions + context).
    """
    snap = db.get_snapshot(store_id, date_str)
    if not snap:
        return []

    store = db.get_store(store_id)
    if not store:
        return []

    rules = db.get_rules()
    staff_all = db.get_staff(store_id)
    staff_map = {nv["id"]: nv for nv in staff_all}
    roster = db.get_roster(store_id, date_str)
    cmp = analytics.compare_to_baseline(store_id, date_str)

    ctx = _build_context(snap, store, staff_map, roster, cmp)
    signals = []

    for rule in rules:
        triggered, details = _check_rule(rule, ctx)
        if triggered:
            is_next_shift_alert = (details.startswith("[CHUẨN BỊ")
                                    or details.startswith("[DỰ BÁO"))
            signals.append({
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "why": rule["why"],
                "actions": rule["then"],
                "confidence": rule.get("confidence", 0.75),
                "urgency": _max_urgency(rule["then"]),
                "details": details,
                "is_next_shift_alert": is_next_shift_alert,
            })

    return sorted(signals, key=lambda x: (
        {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x["urgency"]],
        -x["confidence"]
    ))


def _build_context(snap: dict, store: dict, staff_map: dict,
                   roster: dict | None, cmp: dict) -> dict:
    import datetime as _dt

    cat_rev = snap.get("category_revenue", {})
    total_rev = snap.get("revenue", 1) or 1
    traffic = snap.get("traffic", 1) or 1
    ct_count = snap.get("customer_type_count", {})
    total_ct = sum(ct_count.values()) or 1

    wedding_rev = cat_rev.get("wedding_ring", 0)
    engagement_rev = cat_rev.get("engagement_ring", 0)
    wedding_pct = wedding_rev / total_rev
    wedding_engagement_pct = (wedding_rev + engagement_rev) / total_rev
    fashion_ring_pct = cat_rev.get("fashion_ring", 0) / total_rev
    bracelet_pct = cat_rev.get("bracelet", 0) / total_rev
    low_margin_cats = ["fashion_ring", "bracelet", "necklace", "earring", "accessory"]
    low_margin_rev = sum(cat_rev.get(c, 0) for c in low_margin_cats)
    low_margin_pct = low_margin_rev / total_rev

    couple_pct = ct_count.get("couple", 0) / total_ct
    female_solo_pct = ct_count.get("female_solo", 0) / total_ct

    # Roster analysis
    morning_staff_ids = roster.get("morning_staff", []) if roster else []
    afternoon_staff_ids = roster.get("afternoon_staff", []) if roster else []
    evening_staff_ids = roster.get("evening_staff", []) if roster else []

    # Xác định ca hiện tại và ca tiếp theo dựa trên giờ thực tế
    snap_date = snap.get("date", "")
    today_str = _dt.date.today().isoformat()
    is_today = (snap_date == today_str)

    now = _dt.datetime.now()
    current_hour = now.hour if is_today else 21  # Snapshot quá khứ → coi như cuối ngày

    if current_hour < 9:
        current_shift = None
        current_staff_ids = []
        next_shift = "morning"
        next_staff_ids = morning_staff_ids
    elif current_hour < 14:
        current_shift = "morning"
        current_staff_ids = morning_staff_ids
        next_shift = "afternoon"
        next_staff_ids = afternoon_staff_ids
    elif current_hour < 20:
        current_shift = "afternoon"
        current_staff_ids = afternoon_staff_ids
        next_shift = "evening"
        next_staff_ids = evening_staff_ids
    else:
        current_shift = "evening"
        current_staff_ids = evening_staff_ids
        next_shift = None
        next_staff_ids = []

    is_morning_shift = current_shift == "morning"
    is_afternoon_shift = current_shift == "afternoon"
    is_evening_shift = current_shift == "evening"
    is_peak_hour = is_today and current_hour >= 17
    is_midday = is_today and 11 <= current_hour <= 13
    is_next_shift_afternoon = next_shift == "afternoon"
    is_next_shift_evening = next_shift == "evening"

    wedding_strong = ["wedding_ring", "engagement_ring"]

    def _count_strong_wedding(ids):
        return sum(
            1 for sid in ids
            if any(c in staff_map.get(sid, {}).get("strong_categories", [])
                   for c in wedding_strong)
        )

    def _count_senior(ids):
        return sum(1 for sid in ids if staff_map.get(sid, {}).get("level") == "senior")

    def _count_junior(ids):
        return sum(1 for sid in ids if staff_map.get(sid, {}).get("level") == "junior")

    # Phân tích ca chiều (luôn cần để đánh giá ca cao điểm)
    strong_wedding_afternoon = _count_strong_wedding(afternoon_staff_ids)
    senior_afternoon = _count_senior(afternoon_staff_ids)
    junior_afternoon = _count_junior(afternoon_staff_ids)
    senior_evening = _count_senior(evening_staff_ids)

    # Phân tích ca tiếp theo (để sinh cảnh báo chuẩn bị trước)
    strong_wedding_next = _count_strong_wedding(next_staff_ids)
    senior_next = _count_senior(next_staff_ids)
    junior_next = _count_junior(next_staff_ids)

    # Ca hiện tại
    strong_wedding_current = _count_strong_wedding(current_staff_ids)
    senior_current = _count_senior(current_staff_ids)
    junior_current = _count_junior(current_staff_ids)

    baseline_traffic = cmp.get("baseline_traffic", traffic)
    traffic_ratio = cmp.get("traffic_ratio", 1.0)
    cr_ratio = cmp.get("cr_ratio", 1.0)

    target = store.get("daily_target", 92_000_000)
    target_pct = snap.get("target_pct", 0)
    aov = snap.get("aov", 0)

    # Tính pace thực tế dựa theo giờ hiện tại
    if is_today and current_hour >= 9:
        # Tỷ trọng doanh thu lý tưởng đến giờ hiện tại
        hour_cumulative = {
            9: 0.06, 10: 0.14, 11: 0.23, 12: 0.30, 13: 0.36,
            14: 0.44, 15: 0.53, 16: 0.62, 17: 0.74, 18: 0.87,
            19: 0.97, 20: 0.99, 21: 1.00,
        }
        expected_pct_by_now = hour_cumulative.get(min(current_hour, 21), 1.0)
        revenue_at_noon_pct = target_pct / max(expected_pct_by_now, 0.01) * 0.30 if current_hour >= 12 else target_pct
        revenue_at_16h_pct = target_pct / max(expected_pct_by_now, 0.01) * 0.62 if current_hour >= 16 else target_pct
    else:
        # Snapshot quá khứ: dùng target_pct thực tế
        revenue_at_noon_pct = target_pct * 0.35
        revenue_at_16h_pct = target_pct * 0.62

    dow = snap.get("day_of_week", "Monday")
    is_monday = dow == "Monday"
    day_of_month = int(snap.get("date", "2026-05-05").split("-")[2])
    morning_traffic_shift = snap.get("shift_traffic", {}).get("morning", 0)
    morning_traffic_ratio = morning_traffic_shift / (baseline_traffic * 0.25) if baseline_traffic else 1

    return {
        # Metrics doanh thu / traffic
        "wedding_revenue_pct": wedding_pct,
        "wedding_engagement_revenue_pct": wedding_engagement_pct,
        "fashion_ring_bracelet_pct": fashion_ring_pct + bracelet_pct,
        "low_margin_revenue_pct": low_margin_pct,
        "couple_traffic_pct": couple_pct,
        "female_solo_pct": female_solo_pct,
        "traffic_ratio": traffic_ratio,
        "cr_ratio": cr_ratio,
        "traffic": traffic,
        "baseline_traffic": baseline_traffic,
        "aov": aov,
        "target_pct": target_pct,
        "revenue_at_noon_pct": revenue_at_noon_pct,
        "revenue_at_16h_pct": revenue_at_16h_pct,
        # Nhân sự ca chiều (peak shift — luôn quan trọng)
        "strong_wedding_staff_in_peak": strong_wedding_afternoon,
        "senior_count_in_peak": senior_afternoon,
        "junior_count": junior_afternoon,
        "senior_count": max(1, senior_afternoon),
        "senior_count_evening": senior_evening,
        # Ca hiện tại
        "current_shift": current_shift,
        "strong_wedding_current": strong_wedding_current,
        "senior_current": senior_current,
        "junior_current": junior_current,
        # Ca tiếp theo
        "next_shift": next_shift,
        "strong_wedding_next": strong_wedding_next,
        "senior_next": senior_next,
        "junior_next": junior_next,
        # Flags thời gian (thực tế)
        "is_morning_shift": is_morning_shift,
        "is_afternoon_shift": is_afternoon_shift,
        "is_evening_shift": is_evening_shift,
        "is_next_shift_afternoon": is_next_shift_afternoon,
        "is_next_shift_evening": is_next_shift_evening,
        "is_peak_hour": is_peak_hour,
        "is_midday": is_midday,
        "is_today": is_today,
        # Ngữ cảnh ngày
        "is_monday": is_monday,
        "morning_traffic_ratio": morning_traffic_ratio,
        "day_of_month": day_of_month,
    }


def _check_rule(rule: dict, ctx: dict) -> tuple[bool, str]:
    rid = rule["id"]

    if rid == "RULE-01":
        # Ca chiều đang diễn ra: nhẫn cưới thấp + thiếu NV mạnh
        current_issue = (
            ctx["wedding_revenue_pct"] < 0.32
            and ctx["strong_wedding_staff_in_peak"] < 2
            and ctx["is_afternoon_shift"]
        )
        # Đầu ca chiều (14–17h): chưa có đủ NV wedding dù chưa đến cao điểm
        early_afternoon_prep = (
            ctx["is_afternoon_shift"]
            and not ctx["is_peak_hour"]
            and ctx["strong_wedding_staff_in_peak"] < 2
            and ctx["wedding_revenue_pct"] < 0.32
        )
        # Ca sáng: cảnh báo trước khi ca chiều bắt đầu
        morning_prep = (
            ctx["is_morning_shift"]
            and ctx["is_next_shift_afternoon"]
            and ctx["strong_wedding_next"] < 2
            and ctx["wedding_revenue_pct"] < 0.32
        )
        if current_issue:
            detail = (f"Nhẫn cưới đạt {ctx['wedding_revenue_pct']*100:.1f}% doanh thu "
                      f"(ngưỡng 32%), chỉ {ctx['strong_wedding_staff_in_peak']} NV mạnh wedding ở ca chiều hiện tại.")
        elif early_afternoon_prep:
            detail = (f"[CHUẨN BỊ CAO ĐIỂM] Ca chiều vừa bắt đầu, nhẫn cưới mới đạt "
                      f"{ctx['wedding_revenue_pct']*100:.1f}% và chỉ có {ctx['strong_wedding_staff_in_peak']} NV wedding mạnh — "
                      f"cần bổ sung trước 17h.")
        elif morning_prep:
            detail = (f"[CHUẨN BỊ CA CHIỀU] Nhẫn cưới hiện mới đạt {ctx['wedding_revenue_pct']*100:.1f}% — "
                      f"ca chiều sắp tới chỉ có {ctx['strong_wedding_next']} NV mạnh wedding. "
                      f"Điều chuyển trước khi 14h.")
        else:
            detail = ""
        return current_issue or early_afternoon_prep or morning_prep, detail

    if rid == "RULE-02":
        ok = ctx["traffic_ratio"] >= 0.90 and ctx["cr_ratio"] < 0.85
        detail = (f"Traffic {ctx['traffic_ratio']*100:.0f}% baseline, "
                  f"CR chỉ {ctx['cr_ratio']*100:.0f}% baseline.")
        return ok, detail

    if rid == "RULE-03":
        ok = ctx["revenue_at_noon_pct"] < 0.38 and ctx["is_midday"]
        detail = f"Pace đến trưa ước tính {ctx['revenue_at_noon_pct']*100:.0f}% target (ngưỡng 38%)."
        return ok, detail

    if rid == "RULE-04":
        # Đang trong giờ cao điểm 17–20h: không có senior
        current_issue = ctx["senior_count_in_peak"] == 0 and ctx["is_peak_hour"]
        # Đang đầu ca chiều (14–17h): cảnh báo trước khi vào giờ cao điểm trong cùng ca
        early_afternoon_prep = (
            ctx["is_afternoon_shift"]
            and not ctx["is_peak_hour"]
            and ctx["senior_count_in_peak"] == 0
        )
        # Ca sáng: cảnh báo ca chiều sắp tới không có senior
        morning_prep = (
            ctx["is_morning_shift"]
            and ctx["is_next_shift_afternoon"]
            and ctx["senior_next"] == 0
        )
        if current_issue:
            detail = "Ca cao điểm (17h–20h) hiện không có NV senior nào."
        elif early_afternoon_prep:
            detail = ("[CHUẨN BỊ CAO ĐIỂM] Ca chiều đang bắt đầu nhưng không có NV senior — "
                      "giờ cao điểm 17h–20h sẽ thiếu người dẫn dắt. Điều chuyển ngay.")
        elif morning_prep:
            detail = ("[CHUẨN BỊ CA CHIỀU] Ca chiều sắp tới không có NV senior nào. "
                      "Cần điều chuyển trước 14h.")
        else:
            detail = ""
        return current_issue or early_afternoon_prep or morning_prep, detail

    if rid == "RULE-05":
        ok = ctx["low_margin_revenue_pct"] > 0.55
        detail = f"Sản phẩm margin thấp chiếm {ctx['low_margin_revenue_pct']*100:.1f}% doanh thu (ngưỡng 55%)."
        return ok, detail

    if rid == "RULE-06":
        ok = (ctx["couple_traffic_pct"] >= 0.35
              and ctx["wedding_engagement_revenue_pct"] < 0.40)
        detail = (f"Khách couple {ctx['couple_traffic_pct']*100:.0f}% traffic, "
                  f"nhưng nhẫn cưới+đính hôn chỉ {ctx['wedding_engagement_revenue_pct']*100:.1f}%.")
        return ok, detail

    if rid == "RULE-07":
        # Ca hiện tại: junior quá nhiều so với senior khi traffic cao
        current_issue = (
            ctx["junior_current"] > ctx["senior_current"] * 2
            and ctx["traffic"] > ctx["baseline_traffic"]
            and ctx["current_shift"] is not None
        )
        # Ca tiếp theo: junior quá nhiều so với senior trong ca chiều cao điểm
        next_issue = (
            ctx["is_morning_shift"]
            and ctx["is_next_shift_afternoon"]
            and ctx["junior_next"] > ctx["senior_next"] * 2
            and ctx["traffic"] > ctx["baseline_traffic"] * 0.8
        )
        if current_issue:
            detail = (f"{ctx['junior_current']} junior vs {ctx['senior_current']} senior "
                      f"trong ca {ctx['current_shift']} — traffic đang cao hơn baseline.")
        elif next_issue:
            detail = (f"[CHUẨN BỊ CA CHIỀU] Ca chiều có {ctx['junior_next']} junior vs "
                      f"{ctx['senior_next']} senior — cần ghép cặp trước khi ca bắt đầu.")
        else:
            detail = ""
        return current_issue or next_issue, detail

    if rid == "RULE-08":
        # Kiểm tra SKU tồn chậm
        slow = _find_slow_skus(db.get_store_id_from_ctx())
        ok = len(slow) > 0
        detail = f"{len(slow)} SKU tồn cao (≥10) nhưng không bán trong 7 ngày qua." if ok else ""
        return ok, detail

    if rid == "RULE-09":
        ok = ctx["revenue_at_16h_pct"] < 0.55
        if ok and ctx["is_morning_shift"]:
            detail = (f"[DỰ BÁO] Nếu giữ pace hiện tại, đến 16h ước đạt "
                      f"{ctx['revenue_at_16h_pct']*100:.0f}% target. Ca chiều cần push mạnh.")
        elif ok:
            detail = f"Ước tính pace 16h chỉ đạt {ctx['revenue_at_16h_pct']*100:.0f}% target."
        else:
            detail = ""
        return ok, detail

    if rid == "RULE-10":
        ok = ctx["is_monday"] and ctx["morning_traffic_ratio"] < 0.60
        detail = f"Thứ 2, traffic sáng chỉ {ctx['morning_traffic_ratio']*100:.0f}% baseline thứ 2."
        return ok, detail

    if rid == "RULE-11":
        ok = ctx["day_of_month"] >= 25 and ctx["aov"] < 4_000_000
        detail = f"Ngày {ctx['day_of_month']} cuối tháng, AOV chỉ {ctx['aov']:,.0f}đ."
        return ok, detail

    if rid == "RULE-12":
        ok = (ctx["female_solo_pct"] >= 0.40
              and ctx["fashion_ring_bracelet_pct"] < 0.25)
        # Nếu đang là ca sáng, gắn thêm label chuẩn bị cho ca chiều
        if ok and ctx["is_morning_shift"] and ctx["is_next_shift_afternoon"]:
            detail = (f"[CHUẨN BỊ CA CHIỀU] Khách nữ độc thân đang chiếm "
                      f"{ctx['female_solo_pct']*100:.0f}% traffic nhưng nhẫn thời trang+lắc chỉ "
                      f"{ctx['fashion_ring_bracelet_pct']*100:.1f}%. Chuẩn bị pitch 'tự thưởng' cho ca chiều.")
        elif ok:
            detail = (f"Khách nữ độc thân {ctx['female_solo_pct']*100:.0f}% traffic, "
                      f"nhưng nhẫn thời trang+lắc chỉ {ctx['fashion_ring_bracelet_pct']*100:.1f}%.")
        else:
            detail = ""
        return ok, detail

    return False, ""


def _find_slow_skus(store_id: str | None = None) -> list:
    """Dùng per-store inventory để kiểm tra tồn kho thực của store đó."""
    if not store_id:
        return []
    skus = db.get_skus_with_inventory(store_id)
    txns_7d = db.get_transactions(store_id, days=7)
    sold = {t["sku_id"] for t in txns_7d}
    return [s for s in skus
            if s.get("stock", 0) >= 10
            and s["id"] not in sold
            and s.get("cvr_local", s.get("cvr_history", 0)) >= 0.40]


def evaluate_rules_for_store(store_id: str, date_str: str) -> list[dict]:
    db.get_store_id_from_ctx = lambda: store_id
    return evaluate_rules(store_id, date_str)


def _max_urgency(actions: list[str]) -> str:
    registry = {a["id"]: a for a in db.get_action_registry()}
    urgencies = [registry.get(a, {}).get("urgency", "LOW") for a in actions]
    if "HIGH" in urgencies:
        return "HIGH"
    if "MEDIUM" in urgencies:
        return "MEDIUM"
    return "LOW"


# ─── Forward-looking prep signals cho Morning Briefing ───────────────────────

def evaluate_today_prep_signals(store_id: str, date_today: str,
                                 snap_yesterday: dict | None) -> list[dict]:
    """
    Sinh signals hướng về tương lai cho buổi họp ca sáng.
    Kết hợp kết quả thực tế hôm qua với lịch nhân sự hôm nay.
    Trả về danh sách action cụ thể CHT cần thực hiện ngay hôm nay.
    """
    import datetime as _dt

    store = db.get_store(store_id)
    if not store:
        return []

    staff_map = {nv["id"]: nv for nv in db.get_staff(store_id)}
    roster_today = db.get_roster(store_id, date_today)
    signals: list[dict] = []

    # ── Phân tích lịch làm việc hôm nay ──────────────────────────────────────
    morning_ids = roster_today.get("morning_staff", []) if roster_today else []
    afternoon_ids = roster_today.get("afternoon_staff", []) if roster_today else []
    evening_ids = roster_today.get("evening_staff", []) if roster_today else []

    wedding_cats = ["wedding_ring", "engagement_ring"]

    def _wedding_strong(ids: list) -> int:
        return sum(1 for sid in ids
                   if any(c in staff_map.get(sid, {}).get("strong_categories", [])
                          for c in wedding_cats))

    def _senior(ids: list) -> int:
        return sum(1 for sid in ids
                   if staff_map.get(sid, {}).get("level") == "senior")

    def _junior(ids: list) -> int:
        return sum(1 for sid in ids
                   if staff_map.get(sid, {}).get("level") == "junior")

    def _names(ids: list) -> str:
        return ", ".join(staff_map.get(i, {}).get("name", i) for i in ids)

    ws_afternoon = _wedding_strong(afternoon_ids)
    sr_afternoon = _senior(afternoon_ids)
    jn_afternoon = _junior(afternoon_ids)

    # ── Ngữ cảnh ngày hôm nay ────────────────────────────────────────────────
    try:
        d = _dt.date.fromisoformat(date_today)
    except (ValueError, TypeError):
        d = _dt.date.today()
    dow = d.weekday()   # 0=Mon … 6=Sun
    dom = d.day
    dow_vn = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm",
              "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"][dow]
    is_weekend = dow >= 5
    is_monday = dow == 0
    is_end_month = dom >= 25
    is_start_month = 1 <= dom <= 5

    # ── Metrics từ hôm qua ───────────────────────────────────────────────────
    if snap_yesterday:
        cat_rev = snap_yesterday.get("category_revenue", {})
        total_rev = snap_yesterday.get("revenue", 1) or 1
        wedding_rev_yest = (cat_rev.get("wedding_ring", 0)
                            + cat_rev.get("engagement_ring", 0))
        wedding_pct_yest = wedding_rev_yest / total_rev
        cr_yest = snap_yesterday.get("conversion_rate", 0)
        aov_yest = snap_yesterday.get("aov", 0)
        ct = snap_yesterday.get("customer_type_count", {})
        total_ct = sum(ct.values()) or 1
        couple_pct_yest = ct.get("couple", 0) / total_ct
        female_solo_pct_yest = ct.get("female_solo", 0) / total_ct
        fashion_pct_yest = (cat_rev.get("fashion_ring", 0)
                            + cat_rev.get("bracelet", 0)) / total_rev
        baseline_cr = analytics.get_baseline(store_id, "conversion_rate", 14)
    else:
        # Không có dữ liệu hôm qua — chỉ sinh signals theo ngữ cảnh ngày
        wedding_pct_yest = cr_yest = aov_yest = 0
        couple_pct_yest = female_solo_pct_yest = fashion_pct_yest = 0
        baseline_cr = 0

    # ══════════════════════════════════════════════════════════════════════════
    # PREP-01: Nhẫn cưới thấp hôm qua + ca chiều thiếu NV wedding hôm nay
    # ══════════════════════════════════════════════════════════════════════════
    if snap_yesterday and wedding_pct_yest < 0.35 and ws_afternoon < 2:
        shortage = max(0, 2 - ws_afternoon)
        action_note = (
            f"Điều chuyển thêm {shortage} NV có kỹ năng nhẫn cưới vào ca 14h–20h."
            if shortage > 0 else "Nhắc NV tập trung đúng nhóm sản phẩm này."
        )
        signals.append({
            "signal_id": "PREP-01",
            "rule_name": "Bổ sung NV nhẫn cưới cho ca chiều",
            "urgency": "HIGH",
            "details": (
                f"Hôm qua nhẫn cưới chỉ đạt {wedding_pct_yest*100:.1f}% doanh thu "
                f"(cần ≥35%). Ca chiều hôm nay ({_names(afternoon_ids)}) "
                f"chỉ có {ws_afternoon}/2 NV mạnh wedding. {action_note}"
            ),
            "why": "Nhẫn cưới = 40–50% doanh thu lý tưởng. Thiếu NV mạnh ca cao điểm = miss target.",
            "actions": ["focus_wedding_sku", "add_strong_staff_to_peak"],
            "confidence": 0.88,
        })

    # ══════════════════════════════════════════════════════════════════════════
    # PREP-02: Ca chiều không có senior nào
    # ══════════════════════════════════════════════════════════════════════════
    if afternoon_ids and sr_afternoon == 0:
        signals.append({
            "signal_id": "PREP-02",
            "rule_name": "Ca chiều không có NV senior",
            "urgency": "HIGH",
            "details": (
                f"Ca chiều ({_names(afternoon_ids)}) không có NV senior nào. "
                f"Giờ cao điểm 17h–20h sẽ thiếu người dẫn dắt. "
                f"Cần điều chuyển ít nhất 1 senior vào ca chiều trước 14h."
            ),
            "why": "Senior tạo ra 40–45% doanh thu giờ cao điểm. Vắng mặt = mất ~10–15% doanh thu ngày.",
            "actions": ["reassign_senior_to_peak", "alert_manager"],
            "confidence": 0.92,
        })

    # ══════════════════════════════════════════════════════════════════════════
    # PREP-03: Tỷ lệ junior/senior ca chiều quá cao
    # ══════════════════════════════════════════════════════════════════════════
    if len(afternoon_ids) >= 3 and sr_afternoon > 0 and jn_afternoon > sr_afternoon * 2:
        signals.append({
            "signal_id": "PREP-03",
            "rule_name": "Cần ghép cặp junior–senior ca chiều",
            "urgency": "MEDIUM",
            "details": (
                f"Ca chiều có {jn_afternoon} junior / {sr_afternoon} senior "
                f"({jn_afternoon}:{sr_afternoon}). "
                f"Phân cặp rõ ràng ngay đầu ca: mỗi junior theo sát 1 senior."
            ),
            "why": "Tỷ lệ junior/senior cao làm giảm CR. Buddy system giúp junior học và tăng kết quả ngay.",
            "actions": ["pair_junior_with_senior", "buddy_system_coaching"],
            "confidence": 0.78,
        })

    # ══════════════════════════════════════════════════════════════════════════
    # PREP-04: CR hôm qua dưới baseline
    # ══════════════════════════════════════════════════════════════════════════
    if snap_yesterday and baseline_cr > 0 and cr_yest < baseline_cr * 0.88:
        gap_pct = abs(cr_yest / baseline_cr - 1) * 100
        signals.append({
            "signal_id": "PREP-04",
            "rule_name": "CR hôm qua dưới chuẩn — Cải thiện pitch",
            "urgency": "MEDIUM",
            "details": (
                f"CR hôm qua {cr_yest*100:.1f}% — thấp hơn baseline {baseline_cr*100:.1f}% "
                f"({gap_pct:.0f}% kém hơn). Hôm nay: đơn giản hóa lựa chọn (≤3 mẫu/lần), "
                f"tập trung khơi cảm xúc thay vì liệt kê tính năng sản phẩm."
            ),
            "why": "CR dưới baseline = vấn đề ở cách tư vấn, không phải thiếu khách.",
            "actions": ["change_sales_pitch", "simplify_choice_set", "focus_emotional_selling"],
            "confidence": 0.82,
        })

    # ══════════════════════════════════════════════════════════════════════════
    # PREP-05: Khách nữ solo cao nhưng fashion/bracelet thấp
    # ══════════════════════════════════════════════════════════════════════════
    if snap_yesterday and female_solo_pct_yest >= 0.38 and fashion_pct_yest < 0.22:
        signals.append({
            "signal_id": "PREP-05",
            "rule_name": "Cơ hội nhóm nữ độc thân bị bỏ lỡ",
            "urgency": "MEDIUM",
            "details": (
                f"Hôm qua {female_solo_pct_yest*100:.0f}% khách là nữ đến một mình nhưng "
                f"nhẫn thời trang + lắc chỉ chiếm {fashion_pct_yest*100:.1f}% doanh thu. "
                f"Hôm nay: đổi pitch sang 'tự thưởng cho bản thân' thay vì 'mua quà'."
            ),
            "why": "Pitch 'tự thưởng' tăng CR nhóm nữ solo 15–20%. Cần NV biết khai thác đúng cảm xúc.",
            "actions": ["change_sales_pitch_self_reward", "feature_trending_fashion_sku"],
            "confidence": 0.80,
        })

    # ══════════════════════════════════════════════════════════════════════════
    # PREP-06: Couple cao hôm qua nhưng wedding thấp (nếu PREP-01 chưa cover)
    # ══════════════════════════════════════════════════════════════════════════
    if (snap_yesterday and couple_pct_yest >= 0.25 and wedding_pct_yest < 0.40
            and not any(s["signal_id"] == "PREP-01" for s in signals)):
        signals.append({
            "signal_id": "PREP-06",
            "rule_name": "Khách couple cao — Tập trung nhẫn cưới",
            "urgency": "MEDIUM",
            "details": (
                f"Hôm qua {couple_pct_yest*100:.0f}% khách là cặp đôi nhưng nhẫn cưới+đính hôn "
                f"chỉ chiếm {wedding_pct_yest*100:.1f}% doanh thu. Hôm nay NV cần chủ động "
                f"nhận diện khách couple và dẫn dắt thử nhẫn sớm trong quá trình tư vấn."
            ),
            "why": "Couple vào mà không mua nhẫn = mất AOV cao nhất (15–25 triệu/đơn).",
            "actions": ["focus_wedding_sku", "focus_emotional_selling", "pair_junior_with_senior"],
            "confidence": 0.82,
        })

    # ══════════════════════════════════════════════════════════════════════════
    # PREP-07: Cuối tuần — đảm bảo đội hình peak
    # ══════════════════════════════════════════════════════════════════════════
    if is_weekend:
        yest_traffic = snap_yesterday.get("traffic", 0) if snap_yesterday else 0
        traffic_note = f" Hôm qua có {yest_traffic} lượt." if yest_traffic else ""
        signals.append({
            "signal_id": "PREP-07",
            "rule_name": f"{dow_vn} — Đảm bảo đội hình peak cuối tuần",
            "urgency": "MEDIUM",
            "details": (
                f"{dow_vn}: traffic cuối tuần thường cao hơn 30–40% ngày thường.{traffic_note} "
                f"Đảm bảo ca chiều (14h–20h) có đủ NV mạnh để xử lý lượng khách tăng."
            ),
            "why": "Cuối tuần là peak traffic — cơ hội doanh thu lớn nhất trong tuần, không đủ người = bỏ lỡ.",
            "actions": ["add_strong_staff_to_peak", "focus_wedding_sku"],
            "confidence": 0.85,
        })

    # ══════════════════════════════════════════════════════════════════════════
    # PREP-08: Thứ Hai — cần kích hoạt sớm
    # ══════════════════════════════════════════════════════════════════════════
    if is_monday:
        signals.append({
            "signal_id": "PREP-08",
            "rule_name": "Thứ Hai — Kích hoạt sớm từ 9h",
            "urgency": "MEDIUM",
            "details": (
                "Thứ Hai traffic thấp nhất tuần (kém 20–25% trung bình). "
                "Cần đội hình chủ động: đón khách từ lối vào, tạo không khí sôi nổi, "
                "proactive greeting ngay từ 9h sáng để giữ tinh thần team."
            ),
            "why": "Thứ 2 khó giữ hứng khởi cho team — CHT phải set tone từ đầu buổi.",
            "actions": ["suggest_proactive_greeting", "activate_social_sharing_incentive"],
            "confidence": 0.78,
        })

    # ══════════════════════════════════════════════════════════════════════════
    # PREP-09: Cuối tháng — kích hoạt tư vấn trả góp
    # ══════════════════════════════════════════════════════════════════════════
    if is_end_month and snap_yesterday and aov_yest < 4_500_000:
        signals.append({
            "signal_id": "PREP-09",
            "rule_name": "Cuối tháng — Kích hoạt trả góp 0%",
            "urgency": "MEDIUM",
            "details": (
                f"Ngày {dom}/tháng — cuối tháng khách thường e ngại chi tiêu lớn. "
                f"AOV hôm qua chỉ {aov_yest/1e6:.1f}M đ. "
                f"Nhắc team chủ động gợi ý trả góp 0% cho sản phẩm từ 5M trở lên."
            ),
            "why": "Trả góp 0% giúp khách vượt rào cản tâm lý cuối tháng, tăng chuyển đổi đáng kể.",
            "actions": ["suggest_installment_option", "focus_mid_price_sku"],
            "confidence": 0.75,
        })

    # ══════════════════════════════════════════════════════════════════════════
    # PREP-10: Đầu tháng — push sản phẩm cao cấp
    # ══════════════════════════════════════════════════════════════════════════
    if is_start_month:
        signals.append({
            "signal_id": "PREP-10",
            "rule_name": "Đầu tháng — Push sản phẩm premium",
            "urgency": "LOW",
            "details": (
                f"Ngày {dom} đầu tháng — lương vừa về, khách sẵn sàng chi tiêu hơn 15–20%. "
                f"Đây là thời điểm tốt để tư vấn nhẫn cưới, đính hôn và sản phẩm biên lợi nhuận cao."
            ),
            "why": "Pattern lịch sử: đầu tháng là đỉnh mua sắm trong tháng. Push premium SKU sẽ tăng AOV.",
            "actions": ["focus_wedding_sku", "focus_high_margin_sku"],
            "confidence": 0.72,
        })

    return sorted(signals, key=lambda x: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x["urgency"]])
