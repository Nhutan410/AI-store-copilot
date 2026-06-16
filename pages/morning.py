"""
Trang 3 — Morning Briefing: brief họp ca sáng.
Hiển thị kết quả ngày đã hoàn thành + kế hoạch forward-looking cho hôm nay.
"""
import streamlit as st
from datetime import date as _date, timedelta
from engine import db, analytics
from engine.rule_engine import evaluate_rules_for_store, evaluate_today_prep_signals
from engine import llm


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_dates(store_id: str) -> tuple[str, str]:
    """Trả về (date_today, date_yesterday) dựa trên dữ liệu thực có."""
    latest = db.get_latest_data_date(store_id)
    if latest:
        d = _date.fromisoformat(latest)
        return latest, (d - timedelta(days=1)).isoformat()
    return db.today_str(), db.yesterday_str()


def _get_day_context(date_str: str) -> dict:
    """Trả về ngữ cảnh ngày: thứ, giai đoạn tháng, dự báo traffic."""
    try:
        d = _date.fromisoformat(date_str)
    except (ValueError, TypeError):
        d = _date.today()
    dow = d.weekday()
    dom = d.day
    dow_vn = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm",
              "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"][dow]
    if dom <= 5:
        month_phase = "đầu tháng"
        month_note = "💰 Lương vừa về — khách sẵn sàng chi tiêu"
    elif dom <= 20:
        month_phase = "giữa tháng"
        month_note = "📅 Giai đoạn ổn định"
    else:
        month_phase = "cuối tháng"
        month_note = "💳 Nên gợi ý trả góp 0%"

    if dow >= 5:
        traffic_forecast = "📈 Cao hơn 30–40% ngày thường"
    elif dow == 0:
        traffic_forecast = "📉 Thấp nhất tuần — cần kích hoạt sớm"
    else:
        traffic_forecast = "📊 Bình thường"

    return {
        "date_str": date_str,
        "dow_vn": dow_vn,
        "dom": dom,
        "month_phase": month_phase,
        "month_note": month_note,
        "traffic_forecast": traffic_forecast,
        "is_weekend": dow >= 5,
        "is_monday": dow == 0,
    }


def _analyze_shift(ids: list, staff_map: dict) -> dict:
    """Trả về phân tích đội hình cho 1 ca."""
    wedding_cats = ["wedding_ring", "engagement_ring"]
    wedding_strong = [
        sid for sid in ids
        if any(c in staff_map.get(sid, {}).get("strong_categories", [])
               for c in wedding_cats)
    ]
    seniors = [sid for sid in ids if staff_map.get(sid, {}).get("level") == "senior"]
    juniors = [sid for sid in ids if staff_map.get(sid, {}).get("level") == "junior"]
    return {
        "ids": ids,
        "wedding_strong_count": len(wedding_strong),
        "wedding_strong_names": [staff_map.get(i, {}).get("name", i) for i in wedding_strong],
        "senior_count": len(seniors),
        "junior_count": len(juniors),
    }


def _get_today_priorities(today_prep_signals: list, signals_yesterday: list,
                           staff_map: dict, roster_today: dict | None,
                           snap_yesterday: dict | None) -> list:
    """
    Tổng hợp 3 ưu tiên cho hôm nay từ prep signals (forward-looking).
    Fallback sang signals hôm qua nếu không đủ, sau đó mới dùng defaults thực tế.
    """
    priorities = []

    # Ưu tiên 1: Signals prep HIGH trước, rồi MEDIUM
    for sig in today_prep_signals:
        if len(priorities) >= 3:
            break
        priorities.append({
            "title": sig["rule_name"],
            "desc": sig["details"][:120] + "…" if len(sig["details"]) > 120 else sig["details"],
            "urgency": sig["urgency"],
            "actions": sig.get("actions", []),
            "source": "prep",
        })

    # Fallback: bài học từ hôm qua (không trùng title)
    if len(priorities) < 3:
        existing_titles = {p["title"] for p in priorities}
        for sig in signals_yesterday:
            if len(priorities) >= 3:
                break
            if sig["rule_name"] in existing_titles:
                continue
            priorities.append({
                "title": f"Cải thiện từ hôm qua: {sig['rule_name']}",
                "desc": sig["details"][:120] + "…" if len(sig["details"]) > 120 else sig["details"],
                "urgency": sig["urgency"],
                "actions": sig.get("actions", []),
                "source": "yesterday",
            })
            existing_titles.add(sig["rule_name"])

    # Fallback: dựa trên đội hình thực tế hôm nay
    if len(priorities) < 3 and roster_today:
        afternoon_ids = roster_today.get("afternoon_staff", [])
        wedding_names = [
            staff_map.get(sid, {}).get("name", sid) for sid in afternoon_ids
            if any(c in staff_map.get(sid, {}).get("strong_categories", [])
                   for c in ["wedding_ring", "engagement_ring"])
        ]
        if wedding_names:
            priorities.append({
                "title": "Tận dụng NV wedding mạnh ca chiều",
                "desc": f"{', '.join(wedding_names)} ở ca chiều — tập trung tư vấn nhẫn cưới/đính hôn trong khung 14h–20h.",
                "urgency": "MEDIUM",
                "actions": ["focus_wedding_sku"],
                "source": "roster",
            })

    if len(priorities) < 3:
        priorities.append({
            "title": "Theo dõi pace doanh thu",
            "desc": "Kiểm tra tiến độ doanh thu lúc 12h và 16h — điều chỉnh đội hình nếu pace chậm hơn 38%/55% target.",
            "urgency": "LOW",
            "actions": [],
            "source": "default",
        })

    return priorities[:3]


def _get_top_skus(store_id: str, date_str: str) -> list:
    """Top 3 SKU cần push dựa trên Opportunity Score thực tế."""
    scores = analytics.get_sku_opportunity_scores(store_id, date_str)
    top = [s for s in scores if s.get("stock", 0) > 0][:3]
    result = []
    for s in top:
        cvr = s.get("cvr_local", s.get("cvr_history", 0))
        stock = s.get("stock", 0)
        is_slow = s.get("is_slow_moving", False)
        reason_parts = []
        if cvr >= 0.5:
            reason_parts.append(f"CVR {cvr*100:.0f}%")
        if s["margin_pct"] >= 0.30:
            reason_parts.append(f"Margin {s['margin_pct']*100:.0f}%")
        if is_slow:
            reason_parts.append(f"Tồn {stock} — chưa bán 7+ ngày")
        elif stock <= 3:
            reason_parts.append(f"Tồn thấp ({stock})")
        result.append({
            "id": s["id"],
            "name": s["name"],
            "price": f"{s['price']/1e6:.1f}M",
            "reason": ", ".join(reason_parts[:2]) if reason_parts else "Opportunity score cao",
        })
    return result


def _render_staff_shift(shift_label: str, time_range: str, is_peak: bool,
                         analysis: dict, staff_map: dict):
    """Render một ca làm việc với badge phân tích."""
    ids = analysis["ids"]
    peak_badge = " 🔥" if is_peak else ""

    # Badge đội hình
    ws = analysis["wedding_strong_count"]
    sr = analysis["senior_count"]
    if is_peak:
        ws_color = "#4ecca3" if ws >= 2 else "#e8c84a" if ws == 1 else "#ff6b6b"
        ws_label = f"✅ {ws} NV wedding" if ws >= 2 else (f"⚠️ {ws} NV wedding (cần 2)" if ws == 1 else "❌ Thiếu NV wedding")
        sr_label = f"✅ {sr} senior" if sr >= 1 else "❌ Không có senior"
        sr_color = "#4ecca3" if sr >= 1 else "#ff6b6b"
        badge_html = (
            f"<span style='background:{ws_color}22;color:{ws_color};"
            f"border:1px solid {ws_color}55;border-radius:4px;"
            f"padding:1px 7px;font-size:0.72rem;margin-right:6px'>{ws_label}</span>"
            f"<span style='background:{sr_color}22;color:{sr_color};"
            f"border:1px solid {sr_color}55;border-radius:4px;"
            f"padding:1px 7px;font-size:0.72rem'>{sr_label}</span>"
        )
    else:
        badge_html = ""

    st.markdown(
        f"<div style='font-size:0.85rem;font-weight:700;color:#e2e8f0;margin:10px 0 4px'>"
        f"{shift_label}{peak_badge} <span style='color:#8b92a5;font-weight:400'>{time_range}</span>"
        f"</div>"
        + (f"<div style='margin-bottom:6px'>{badge_html}</div>" if badge_html else ""),
        unsafe_allow_html=True
    )

    if not ids:
        st.markdown("<div style='color:#8b92a5;font-size:0.82rem;padding-left:4px'>Chưa có lịch</div>",
                    unsafe_allow_html=True)
        return

    for sid in ids:
        nv = staff_map.get(sid, {})
        level = nv.get("level", "")
        level_color = {"senior": "#4ecca3", "mid": "#e8c84a", "junior": "#f7a948"}.get(level, "#8b92a5")
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
        is_wedding_strong = any(
            c in nv.get("strong_categories", [])
            for c in ["wedding_ring", "engagement_ring"]
        )
        name_color = "#e8c84a" if (is_peak and is_wedding_strong) else "#e2e8f0"
        st.markdown(
            f"<div style='padding:2px 0 2px 4px;font-size:0.83rem'>"
            f"<span style='color:{level_color};font-weight:700'>[{level.upper()[:3]}]</span>"
            f"&nbsp;<span style='color:{name_color}'>{nv.get('name', sid)}</span>"
            f"<br><span style='color:#6b7280;font-size:0.73rem;padding-left:32px'>{cats}</span>"
            f"</div>",
            unsafe_allow_html=True
        )


# ─── Main render ─────────────────────────────────────────────────────────────

def render(store_id: str):
    st.markdown("## ☀️ Họp Ca Sáng")
    store = db.get_store(store_id)
    if not store:
        st.error("Không tìm thấy cửa hàng.")
        return

    DATE_TODAY, DATE_YESTERDAY = _get_dates(store_id)

    # Load dữ liệu
    snap_yesterday = db.get_snapshot(store_id, DATE_YESTERDAY)
    health_yesterday = analytics.calc_health_score(store_id, DATE_YESTERDAY)
    signals_yesterday = evaluate_rules_for_store(store_id, DATE_YESTERDAY) if snap_yesterday else []
    today_prep_signals = evaluate_today_prep_signals(store_id, DATE_TODAY, snap_yesterday)
    roster_today = db.get_roster(store_id, DATE_TODAY)
    staff_map = {nv["id"]: nv for nv in db.get_staff(store_id)}
    day_ctx = _get_day_context(DATE_TODAY)

    # Phân tích đội hình các ca hôm nay
    if roster_today:
        morning_analysis = _analyze_shift(roster_today.get("morning_staff", []), staff_map)
        afternoon_analysis = _analyze_shift(roster_today.get("afternoon_staff", []), staff_map)
        evening_analysis = _analyze_shift(roster_today.get("evening_staff", []), staff_map)
    else:
        morning_analysis = afternoon_analysis = evening_analysis = _analyze_shift([], staff_map)

    # ─── Header ────────────────────────────────────────────────────────────────
    high_prep = [s for s in today_prep_signals if s["urgency"] == "HIGH"]
    alert_badge = ""
    if high_prep:
        alert_badge = (
            f"<span style='background:#ff6b6b22;color:#ff6b6b;border:1px solid #ff6b6b55;"
            f"border-radius:4px;padding:2px 8px;font-size:0.75rem;margin-left:10px'>"
            f"⚠️ {len(high_prep)} cảnh báo hôm nay</span>"
        )

    st.markdown(f"""
<div style="background:linear-gradient(135deg,#1a1d27,#252836);border:1px solid #2d3250;
            border-radius:12px;padding:18px 24px;margin-bottom:16px">
  <div style="font-size:0.75rem;color:#8b92a5;text-transform:uppercase;letter-spacing:0.1em">
    Brief Họp Ca Sáng</div>
  <div style="font-size:1.4rem;font-weight:700;color:#e8c84a;margin:4px 0">
    {store['name']} {alert_badge}</div>
  <div style="display:flex;gap:24px;flex-wrap:wrap;margin-top:6px">
    <div style="font-size:0.88rem;color:#8b92a5">
      📅 Kế hoạch ngày: <b style="color:#e2e8f0">{day_ctx['dow_vn']} {DATE_TODAY}</b>
    </div>
    <div style="font-size:0.88rem;color:#8b92a5">
      🎯 Target: <b style="color:#e8c84a">{store['daily_target']/1e6:.0f}M đồng</b>
    </div>
    <div style="font-size:0.88rem;color:#8b92a5">
      🗓 {day_ctx['month_phase'].capitalize()} · {day_ctx['traffic_forecast']}
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    # ─── SECTION 1: Kết quả hôm qua ─────────────────────────────────────────
    st.markdown(f"### 📊 Kết Quả Hôm Qua — {DATE_YESTERDAY}")
    if snap_yesterday:
        target_pct = snap_yesterday.get("target_pct", 0) * 100
        rev_color = "#4ecca3" if target_pct >= 95 else "#e8c84a" if target_pct >= 80 else "#ff6b6b"
        cmp = analytics.compare_to_baseline(store_id, DATE_YESTERDAY)
        cr_ratio = cmp.get("cr_ratio", 1.0)
        tr_ratio = cmp.get("traffic_ratio", 1.0)
        cr_color = "#4ecca3" if cr_ratio >= 1.0 else "#e8c84a" if cr_ratio >= 0.88 else "#ff6b6b"
        tr_color = "#4ecca3" if tr_ratio >= 1.0 else "#e8c84a" if tr_ratio >= 0.85 else "#ff6b6b"

        # Top issue hôm qua để giải thích tại sao
        top_issue = ""
        if signals_yesterday:
            top_sig = signals_yesterday[0]
            top_issue = (
                f"<div style='margin-top:12px;padding-top:10px;border-top:1px solid #2d3250;"
                f"font-size:0.82rem;color:#8b92a5'>"
                f"<b style='color:#e8c84a'>⚡ Vấn đề chính hôm qua:</b> "
                f"<span style='color:#b0b7c3'>{top_sig['rule_name']}</span> — "
                f"<span>{top_sig['details'][:120]}{'…' if len(top_sig['details'])>120 else ''}</span>"
                f"</div>"
            )

        cat_rev = snap_yesterday.get("category_revenue", {})
        total_rev = snap_yesterday.get("revenue", 1) or 1
        wedding_pct = (cat_rev.get("wedding_ring", 0) + cat_rev.get("engagement_ring", 0)) / total_rev
        w_color = "#4ecca3" if wedding_pct >= 0.35 else "#e8c84a" if wedding_pct >= 0.25 else "#ff6b6b"

        st.markdown(f"""
<div style="background:#1e2130;border-radius:8px;padding:14px 18px">
  <div style="display:flex;gap:24px;flex-wrap:wrap">
    <div>
      <div style="color:#8b92a5;font-size:0.75rem">Doanh thu</div>
      <div style="font-size:1.5rem;font-weight:700;color:{rev_color}">{snap_yesterday['revenue']/1e6:.1f}M đ</div>
      <div style="color:#8b92a5;font-size:0.78rem">{target_pct:.1f}% target</div>
    </div>
    <div>
      <div style="color:#8b92a5;font-size:0.75rem">Traffic</div>
      <div style="font-size:1.5rem;font-weight:700;color:{tr_color}">{snap_yesterday['traffic']}</div>
      <div style="color:#8b92a5;font-size:0.78rem">{tr_ratio*100:.0f}% baseline</div>
    </div>
    <div>
      <div style="color:#8b92a5;font-size:0.75rem">CR</div>
      <div style="font-size:1.5rem;font-weight:700;color:{cr_color}">{snap_yesterday['conversion_rate']*100:.1f}%</div>
      <div style="color:#8b92a5;font-size:0.78rem">{cr_ratio*100:.0f}% baseline</div>
    </div>
    <div>
      <div style="color:#8b92a5;font-size:0.75rem">Nhẫn cưới</div>
      <div style="font-size:1.5rem;font-weight:700;color:{w_color}">{wedding_pct*100:.1f}%</div>
      <div style="color:#8b92a5;font-size:0.78rem">doanh thu (cần ≥35%)</div>
    </div>
    <div>
      <div style="color:#8b92a5;font-size:0.75rem">Sức khỏe</div>
      <div style="font-size:1.5rem;font-weight:700;color:#e8c84a">{health_yesterday['score']}/100</div>
      <div style="color:#8b92a5;font-size:0.78rem">Hạng {health_yesterday['grade']}</div>
    </div>
  </div>
  {top_issue}
</div>""", unsafe_allow_html=True)
    else:
        st.info(f"Chưa có dữ liệu cho ngày {DATE_YESTERDAY}.")

    st.markdown("---")

    # ─── SECTION 2: Kế hoạch hôm nay ────────────────────────────────────────
    st.markdown(f"### 📋 Kế Hoạch Hôm Nay — {day_ctx['dow_vn']} {DATE_TODAY}")
    col_left, col_right = st.columns([3, 2])

    with col_left:
        # Ngữ cảnh ngày
        st.markdown(f"""
<div style="background:#252836;border-radius:8px;padding:10px 14px;margin-bottom:12px;
            display:flex;gap:20px;flex-wrap:wrap;font-size:0.85rem">
  <span>📅 <b style="color:#e8c84a">{day_ctx['dow_vn']}</b></span>
  <span>📆 Ngày {day_ctx['dom']} — <b style="color:#e8c84a">{day_ctx['month_phase']}</b></span>
  <span style="color:#8b92a5">{day_ctx['month_note']}</span>
  <span style="color:#8b92a5">|</span>
  <span style="color:#b0b7c3">{day_ctx['traffic_forecast']}</span>
</div>""", unsafe_allow_html=True)

        # 3 Ưu tiên hôm nay — từ dữ liệu thực
        st.markdown("#### ⭐ 3 Ưu Tiên Hôm Nay")
        priorities = _get_today_priorities(
            today_prep_signals, signals_yesterday, staff_map, roster_today, snap_yesterday
        )
        for i, p in enumerate(priorities, 1):
            color = {"HIGH": "#ff6b6b", "MEDIUM": "#e8c84a", "LOW": "#4ecca3"}[p.get("urgency", "MEDIUM")]
            source_note = ""
            if p.get("source") == "yesterday":
                source_note = "<span style='color:#555e72;font-size:0.72rem'> (bài học hôm qua)</span>"
            elif p.get("source") == "roster":
                source_note = "<span style='color:#555e72;font-size:0.72rem'> (dựa trên đội hình)</span>"
            st.markdown(f"""
<div style="background:#1e2130;border-left:3px solid {color};border-radius:0 8px 8px 0;
            padding:10px 14px;margin:6px 0">
  <div style="font-weight:700;color:#e2e8f0;font-size:0.9rem">{i}. {p['title']}{source_note}</div>
  <div style="color:#8b92a5;font-size:0.83rem;margin-top:3px">{p['desc']}</div>
</div>""", unsafe_allow_html=True)

        # Top SKU cần đẩy
        st.markdown("#### 🏷️ Top SKU Cần Đẩy Hôm Nay")
        top_skus = _get_top_skus(store_id, DATE_YESTERDAY)
        if top_skus:
            for sku in top_skus:
                st.markdown(f"""
<div style="background:#1e2130;border-radius:8px;padding:10px 14px;margin:5px 0;
            display:flex;justify-content:space-between;align-items:center">
  <div>
    <div style="font-weight:600;color:#e2e8f0;font-size:0.88rem">{sku['name']}</div>
    <div style="color:#8b92a5;font-size:0.78rem">{sku['id']} · {sku['reason']}</div>
  </div>
  <div style="color:#e8c84a;font-weight:700;font-size:0.95rem;white-space:nowrap;margin-left:10px">{sku['price']}</div>
</div>""", unsafe_allow_html=True)
        else:
            st.caption("Đang tính toán opportunity scores...")

        # Cảnh báo HIGH cần hành động ngay
        high_signals = [s for s in today_prep_signals if s["urgency"] == "HIGH"]
        if high_signals:
            st.markdown("#### ⚡ Hành Động Ngay")
            for sig in high_signals:
                st.markdown(f"""
<div style="background:#2a1a1a;border:1px solid #ff6b6b55;border-radius:8px;
            padding:10px 14px;margin:6px 0">
  <div style="color:#ff6b6b;font-weight:700;font-size:0.88rem">🚨 {sig['rule_name']}</div>
  <div style="color:#b0b7c3;font-size:0.82rem;margin-top:4px">{sig['details']}</div>
  <div style="color:#8b92a5;font-size:0.75rem;margin-top:6px;font-style:italic">
    Lý do: {sig['why']}</div>
</div>""", unsafe_allow_html=True)

    with col_right:
        st.markdown("#### 👥 Đội Hình Hôm Nay")
        if roster_today:
            _render_staff_shift("Ca Sáng", "09:00–14:00", False,
                                morning_analysis, staff_map)
            _render_staff_shift("Ca Chiều", "14:00–20:00", True,
                                afternoon_analysis, staff_map)
            _render_staff_shift("Ca Tối", "20:00–22:00", False,
                                evening_analysis, staff_map)
        else:
            st.info("Chưa có lịch hôm nay.")
            st.caption(f"Cần tạo roster cho {DATE_TODAY} trong simulator.")

        # Tóm tắt sức mạnh đội hình
        if roster_today:
            st.markdown("")
            ws_pm = afternoon_analysis["wedding_strong_count"]
            sr_pm = afternoon_analysis["senior_count"]

            def _badge(ok: bool, ok_text: str, fail_text: str) -> str:
                color = "#4ecca3" if ok else "#ff6b6b"
                text = ok_text if ok else fail_text
                return (
                    f"<div style='background:{color}15;border:1px solid {color}44;"
                    f"border-radius:6px;padding:5px 10px;margin:4px 0;"
                    f"font-size:0.80rem;color:{color}'>{text}</div>"
                )

            badges_html = (
                _badge(ws_pm >= 2,
                       f"✅ Ca chiều: {ws_pm} NV mạnh wedding",
                       f"⚠️ Ca chiều: chỉ {ws_pm}/2 NV mạnh wedding")
                + _badge(sr_pm >= 1,
                         f"✅ Ca chiều: có {sr_pm} senior",
                         "❌ Ca chiều: không có senior")
            )
            if afternoon_analysis["wedding_strong_names"]:
                names = ", ".join(afternoon_analysis["wedding_strong_names"])
                badges_html += (
                    f"<div style='font-size:0.78rem;color:#8b92a5;margin-top:4px'>"
                    f"Wedding strong ca chiều: <b style='color:#e8c84a'>{names}</b></div>"
                )

            st.markdown(
                f"<div style='background:#1e2130;border-radius:8px;padding:10px 14px'>"
                f"<div style='font-size:0.75rem;color:#8b92a5;margin-bottom:6px'>"
                f"PHÂN TÍCH CA CAO ĐIỂM (14H–20H)</div>"
                f"{badges_html}</div>",
                unsafe_allow_html=True
            )

        # MEDIUM signals (cần lưu ý)
        medium_signals = [s for s in today_prep_signals if s["urgency"] == "MEDIUM"]
        if medium_signals:
            st.markdown("#### 💡 Cần Lưu Ý")
            for sig in medium_signals[:3]:
                st.markdown(f"""
<div style="background:#1e2130;border-left:3px solid #e8c84a;
            border-radius:0 6px 6px 0;padding:8px 12px;margin:5px 0">
  <div style="font-size:0.83rem;font-weight:700;color:#e2e8f0">{sig['rule_name']}</div>
  <div style="font-size:0.78rem;color:#8b92a5;margin-top:2px">
    {sig['details'][:100]}{'…' if len(sig['details'])>100 else ''}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ─── SECTION 3: AI Brief ──────────────────────────────────────────────────
    st.markdown("### 🤖 Brief AI — Đọc Cho Team Nghe")
    cache_key = f"morning_brief_{store_id}_{DATE_TODAY}"

    if cache_key in st.session_state.llm_cache:
        brief_text = st.session_state.llm_cache[cache_key]
        st.markdown(f"""
<div style="background:#1a2a1a;border:1px solid #2d5a3a;border-radius:12px;
            padding:20px;font-size:0.95rem;color:#e2e8f0;line-height:1.8;white-space:pre-wrap">{brief_text}
</div>""", unsafe_allow_html=True)
        col_dl, col_reset, _ = st.columns([1, 1, 3])
        with col_dl:
            st.download_button(
                label="⬇️ Tải Brief",
                data=brief_text,
                file_name=f"brief_{store_id}_{DATE_TODAY}.txt",
                mime="text/plain",
                key="btn_dl_brief"
            )
        with col_reset:
            if st.button("🔄 Tạo lại", key="btn_regen_brief"):
                st.session_state.llm_cache.pop(cache_key, None)
                st.rerun()
    else:
        col_gen, _ = st.columns([1, 3])
        with col_gen:
            if st.button("✍️ AI Soạn Brief", key="btn_gen_brief",
                         disabled=not st.session_state.ai_ok,
                         type="primary", use_container_width=True):
                with st.spinner("AI đang soạn brief họp ca sáng..."):
                    brief = llm.gen_morning_brief(store_id, DATE_YESTERDAY, DATE_TODAY)
                    st.session_state.llm_cache[cache_key] = brief
                    st.rerun()
        if not st.session_state.ai_ok:
            st.caption("⚠️ Cần OpenAI API Key để soạn brief")
