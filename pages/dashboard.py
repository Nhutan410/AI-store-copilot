"""
Trang 1 — Dashboard: tổng quan sức khỏe cửa hàng.
"""
from datetime import date, timedelta

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from engine import db, analytics
from engine.rule_engine import evaluate_rules_for_store
from engine import llm


def _cache_key(key: str, store_id: str, date_str: str) -> str:
    return f"{key}_{store_id}_{date_str}"


def _resolve_dashboard_dates(store_id: str) -> tuple[str, str, bool]:
    """
    Trả về (ngày báo cáo, ngày hiện tại theo dữ liệu, có đúng snapshot hôm qua).

    Snapshot mới nhất được xem là dữ liệu của hôm nay. Dashboard ưu tiên ngày
    liền trước để thống nhất với phần "Kết quả hôm qua" của Họp ca sáng.
    """
    latest = db.get_latest_data_date(store_id)
    if not latest:
        today = date.today()
        return (today - timedelta(days=1)).isoformat(), today.isoformat(), False

    latest_date = date.fromisoformat(latest)
    previous = (latest_date - timedelta(days=1)).isoformat()
    if db.get_snapshot(store_id, previous):
        return previous, latest, True
    return latest, latest, False


def render(store_id: str):
    st.markdown("## 🏠 Dashboard — Tổng quan cửa hàng")
    store = db.get_store(store_id)
    if not store:
        st.error("Không tìm thấy cửa hàng.")
        return

    report_date, data_today, is_yesterday = _resolve_dashboard_dates(store_id)
    snap = db.get_snapshot(store_id, report_date)
    if not snap:
        st.warning("Chưa có dữ liệu. Chạy `python data/seed_data.py` để khởi tạo.")
        return

    period_label = "Hôm qua" if is_yesterday else "Ngày dữ liệu mới nhất"
    st.caption(
        f"Kết quả {period_label.lower()}: {report_date} · "
        f"Ngày hiện tại theo dữ liệu: {data_today}"
    )

    health = analytics.calc_health_score(store_id, report_date)
    cmp = analytics.compare_to_baseline(store_id, report_date)
    signals = evaluate_rules_for_store(store_id, report_date)

    # ─── Row 1: KPI Cards ─────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)

    target_pct = snap.get("target_pct", 0) * 100
    cr = snap.get("conversion_rate", 0) * 100
    baseline_cr = cmp.get("baseline_cr", 0) * 100
    cr_delta = cr - baseline_cr
    traffic = snap.get("traffic", 0)
    baseline_tr = cmp.get("baseline_traffic", 1)
    tr_delta_pct = (traffic / baseline_tr - 1) * 100 if baseline_tr else 0
    aov = snap.get("aov", 0)

    with col1:
        score_color = {"A": "#4ecca3", "B": "#e8c84a", "C": "#f7a948", "D": "#ff6b6b"}[health["grade"]]
        st.markdown(f"""
<div class="metric-card">
<div class="metric-label">Điểm Sức Khỏe</div>
<div class="metric-value" style="color:{score_color}">{health['score']}<span style="font-size:1rem;color:#8b92a5">/100</span></div>
<div style="font-size:0.85rem;color:{score_color}">Hạng {health['grade']}</div>
</div>""", unsafe_allow_html=True)

    with col2:
        color = "#4ecca3" if target_pct >= 95 else "#e8c84a" if target_pct >= 80 else "#ff6b6b"
        st.markdown(f"""
<div class="metric-card">
<div class="metric-label">% Target {period_label}</div>
<div class="metric-value" style="color:{color}">{target_pct:.1f}%</div>
<div style="font-size:0.82rem;color:#8b92a5">{snap['revenue']/1e6:.1f}M / {store['daily_target']/1e6:.0f}M đ</div>
</div>""", unsafe_allow_html=True)

    with col3:
        delta_color = "#4ecca3" if cr_delta >= 0 else "#ff6b6b"
        delta_sign = "+" if cr_delta >= 0 else ""
        st.markdown(f"""
<div class="metric-card">
<div class="metric-label">Tỷ lệ Chuyển đổi</div>
<div class="metric-value">{cr:.1f}%</div>
<div style="font-size:0.82rem;color:{delta_color}">{delta_sign}{cr_delta:.1f}pp vs baseline</div>
</div>""", unsafe_allow_html=True)

    with col4:
        tr_color = "#4ecca3" if tr_delta_pct >= 0 else "#ff6b6b"
        tr_sign = "+" if tr_delta_pct >= 0 else ""
        st.markdown(f"""
<div class="metric-card">
<div class="metric-label">Traffic Khách</div>
<div class="metric-value">{traffic}</div>
<div style="font-size:0.82rem;color:{tr_color}">{tr_sign}{tr_delta_pct:.1f}% vs baseline</div>
</div>""", unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
<div class="metric-card">
<div class="metric-label">AOV Trung bình</div>
<div class="metric-value" style="font-size:1.5rem">{aov/1e6:.2f}M đ</div>
<div style="font-size:0.82rem;color:#8b92a5">{snap['num_transactions']} giao dịch</div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── Row 2: Health gauge + Alerts ────────────────────────────────────
    col_gauge, col_alerts = st.columns([1, 2])

    with col_gauge:
        st.markdown("#### 📊 Health Score")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health["score"],
            domain={"x": [0, 1], "y": [0, 1]},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#8b92a5"},
                "bar": {"color": score_color},
                "bgcolor": "#1e2130",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 55], "color": "rgba(255,107,107,0.13)"},
                    {"range": [55, 70], "color": "rgba(247,169,72,0.13)"},
                    {"range": [70, 85], "color": "rgba(232,200,74,0.13)"},
                    {"range": [85, 100], "color": "rgba(78,204,163,0.13)"},
                ],
            },
            number={"font": {"color": score_color, "size": 40}},
            title={"text": f"Hạng {health['grade']}", "font": {"color": "#8b92a5", "size": 14}},
        ))
        fig_gauge.update_layout(
            paper_bgcolor="#1e2130", font_color="#e2e8f0",
            height=220, margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Components breakdown
        for comp, val in health["components"].items():
            st.markdown(f"""
<div style="display:flex;justify-content:space-between;font-size:0.8rem;
            padding:3px 0;border-bottom:1px solid #2d3250">
<span style="color:#8b92a5">{comp}</span>
<span style="color:#e8c84a;font-weight:600">{val:.1f}</span>
</div>""", unsafe_allow_html=True)

    with col_alerts:
        st.markdown(f"#### ⚡ Cảnh Báo Đang Kích Hoạt ({len(signals)})")
        if not signals:
            st.success("✅ Không có cảnh báo nào. Cửa hàng đang vận hành tốt!")
        else:
            for sig in signals[:5]:
                urgency_color = {"HIGH": "#ff6b6b", "MEDIUM": "#f7c948", "LOW": "#4ecca3"}[sig["urgency"]]
                urgency_label = {"HIGH": "Khẩn", "MEDIUM": "Trung bình", "LOW": "Thấp"}[sig["urgency"]]
                with st.container():
                    st.markdown(f"""
<div style="background:#1e2130;border-left:3px solid {urgency_color};border-radius:0 8px 8px 0;
            padding:10px 14px;margin:6px 0">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
<b style="color:#e2e8f0;font-size:0.9rem">{sig['rule_name']}</b>
<span style="background:{urgency_color}22;color:{urgency_color};border:1px solid {urgency_color}55;
      border-radius:4px;padding:1px 8px;font-size:0.75rem;font-weight:700">{urgency_label}</span>
</div>
<div style="color:#8b92a5;font-size:0.82rem">{sig['details']}</div>
<div style="color:#6b7280;font-size:0.78rem;margin-top:4px">
Độ tin cậy: {sig['confidence']*100:.0f}% &nbsp;|&nbsp;
Actions: {', '.join(sig['actions'][:2])}{'...' if len(sig['actions']) > 2 else ''}
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ─── Row 3: Revenue chart 7 ngày + Category mix ──────────────────────
    col_chart, col_cat = st.columns([3, 2])

    with col_chart:
        st.markdown(f"#### 📈 Doanh Thu 7 Ngày Đến {report_date}")
        trend = [
            item for item in analytics.get_revenue_trend(store_id, 30)
            if item["date"] <= report_date
        ][-7:]
        if trend:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[t["date"] for t in trend],
                y=[t["revenue"] / 1e6 for t in trend],
                name="Doanh thu",
                marker_color=["#4ecca3" if t["target_pct"] >= 95
                               else "#e8c84a" if t["target_pct"] >= 80
                               else "#ff6b6b" for t in trend],
                text=[f"{t['target_pct']:.0f}%" for t in trend],
                textposition="outside",
                textfont={"size": 10, "color": "#e2e8f0"},
            ))
            fig.add_trace(go.Scatter(
                x=[t["date"] for t in trend],
                y=[store["daily_target"] / 1e6] * len(trend),
                name="Target",
                line={"color": "#e8c84a", "dash": "dash", "width": 2},
                mode="lines",
            ))
            fig.update_layout(
                paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
                font_color="#e2e8f0", height=280,
                xaxis={"gridcolor": "#2d3250", "title": ""},
                yaxis={"gridcolor": "#2d3250", "title": "Triệu đồng"},
                legend={"bgcolor": "#1e2130"},
                margin=dict(l=10, r=10, t=10, b=10),
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_cat:
        st.markdown("#### 🏷️ Cơ Cấu Doanh Thu")
        cat_rev = snap.get("category_revenue", {})
        if cat_rev:
            cat_names = {
                "wedding_ring": "Nhẫn cưới",
                "engagement_ring": "Nhẫn đính hôn",
                "fashion_ring": "Nhẫn thời trang",
                "bracelet": "Lắc tay",
                "necklace": "Dây chuyền",
                "earring": "Bông tai",
                "watch": "Đồng hồ",
                "accessory": "Phụ kiện",
            }
            labels = [cat_names.get(k, k) for k, v in cat_rev.items() if v > 0]
            values = [v for v in cat_rev.values() if v > 0]
            colors = ["#e8c84a", "#f7a948", "#4ecca3", "#667eea", "#6bcb77", "#ff6b6b", "#c77dff", "#48cae4"]

            fig_pie = go.Figure(go.Pie(
                labels=labels, values=values,
                hole=0.5,
                marker_colors=colors[:len(labels)],
                textinfo="percent",
                textfont_size=11,
                hovertemplate="%{label}: %{value:,.0f}đ<br>%{percent}<extra></extra>",
            ))
            fig_pie.update_layout(
                paper_bgcolor="#1e2130", font_color="#e2e8f0",
                height=280, showlegend=True,
                legend={"bgcolor": "#1e2130", "font": {"size": 10}},
                margin=dict(l=0, r=0, t=10, b=10),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # ─── Row 4: AI Actions ────────────────────────────────────────────────
    col_ai1, col_ai2 = st.columns(2)

    with col_ai1:
        st.markdown("#### 🤖 Báo Cáo Sức Khỏe AI")
        cache_key = _cache_key("health_report", store_id, report_date)
        if cache_key in st.session_state.llm_cache:
            st.markdown(st.session_state.llm_cache[cache_key])
        else:
            if st.button("📝 Tạo Báo Cáo AI", key="btn_health_report",
                         disabled=not st.session_state.ai_ok, use_container_width=True):
                with st.spinner("AI đang phân tích dữ liệu..."):
                    result = llm.gen_health_report(store_id, report_date)
                    st.session_state.llm_cache[cache_key] = result
                    st.rerun()
            if not st.session_state.ai_ok:
                st.caption("⚠️ Cần OpenAI API Key để dùng tính năng này")

    with col_ai2:
        st.markdown("#### 🔍 Phân Tích Nguyên Nhân AI")
        cache_key2 = _cache_key("root_cause", store_id, report_date)
        if cache_key2 in st.session_state.llm_cache:
            st.markdown(st.session_state.llm_cache[cache_key2])
        else:
            if st.button("🔎 Tạo Phân Tích Nguyên Nhân", key="btn_root_cause",
                         disabled=not st.session_state.ai_ok, use_container_width=True):
                with st.spinner("AI đang phân tích nguyên nhân..."):
                    result = llm.gen_root_cause_analysis(store_id, report_date)
                    st.session_state.llm_cache[cache_key2] = result
                    st.rerun()
            if not st.session_state.ai_ok:
                st.caption("⚠️ Cần OpenAI API Key để dùng tính năng này")

    # Xóa cache
    if any(k in st.session_state.llm_cache for k in [
        _cache_key("health_report", store_id, report_date),
        _cache_key("root_cause", store_id, report_date),
    ]):
        if st.button("🔄 Làm mới phân tích", key="btn_refresh_ai"):
            for k in [
                _cache_key("health_report", store_id, report_date),
                _cache_key("root_cause", store_id, report_date),
            ]:
                st.session_state.llm_cache.pop(k, None)
            st.rerun()

    # ─── Row 5: Target result + Staff ─────────────────────────────────────
    st.markdown("---")
    col_pred, col_staff = st.columns(2)

    with col_pred:
        target_gap = snap["revenue"] - store["daily_target"]
        st.markdown(f"#### 🎯 Kết Quả Target {period_label}")
        st.markdown(f"""
<div style="background:#1e2130;border-radius:8px;padding:14px 16px">
<div style="color:#8b92a5;font-size:0.82rem">Doanh thu thực tế ngày {report_date}</div>
<div style="font-size:2rem;font-weight:700;color:#e8c84a">{snap['revenue']/1e6:.1f}M đ</div>
<div style="font-size:0.85rem;color:#8b92a5">
Target: {store['daily_target']/1e6:.0f}M đ &nbsp;|&nbsp;
Gap: <span style="color:{'#4ecca3' if target_gap >= 0 else '#ff6b6b'}">
{target_gap/1e6:+.1f}M đ
</span>
</div>
</div>""", unsafe_allow_html=True)

        # Staff heatmap — efficiency matrix
        st.markdown(f"**Hiệu suất nhân viên {period_label.lower()}**")
        perf = snap.get("staff_performance", {})
        staff_map = {nv["id"]: nv for nv in db.get_staff(store_id)}
        if perf:
            rows = []
            for sid, v in perf.items():
                nv = staff_map.get(sid, {})
                rows.append({
                    "Tên": nv.get("name", sid),
                    "Doanh thu": f"{v['revenue']/1e6:.1f}M",
                    "Đơn": v["orders"],
                    "Level": nv.get("level", ""),
                })
            import pandas as pd
            df = pd.DataFrame(rows).sort_values("Doanh thu", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True,
                         height=min(200, len(rows) * 35 + 40))

    with col_staff:
        st.markdown(f"#### 👥 Đội Hình Hôm Nay ({data_today})")
        roster_today = db.get_roster(store_id, data_today)
        staff_map_all = {nv["id"]: nv for nv in db.get_staff(store_id)}

        if roster_today:
            for shift_key, shift_label, time_range in [
                ("morning_staff", "Ca Sáng", "09:00–14:00"),
                ("afternoon_staff", "Ca Chiều", "14:00–20:00"),
                ("evening_staff", "Ca Tối", "20:00–22:00"),
            ]:
                ids = roster_today.get(shift_key, [])
                st.markdown(f"**{shift_label}** `{time_range}`")
                for sid in ids:
                    nv = staff_map_all.get(sid, {})
                    level_color = {"senior": "#4ecca3", "mid": "#e8c84a", "junior": "#f7a948"}.get(
                        nv.get("level", ""), "#8b92a5")
                    cats = ", ".join(nv.get("strong_categories", []))
                    st.markdown(f"""
<div style="display:flex;align-items:center;gap:8px;padding:3px 0">
<span style="color:{level_color};font-weight:600;font-size:0.78rem;min-width:50px">
{nv.get('level','').upper()}</span>
<span style="color:#e2e8f0;font-size:0.88rem">{nv.get('name', sid)}</span>
<span style="color:#6b7280;font-size:0.75rem">({cats})</span>
</div>""", unsafe_allow_html=True)
                st.markdown("")
        else:
            st.info("Chưa có lịch làm việc hôm nay.")
