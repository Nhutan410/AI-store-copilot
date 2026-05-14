"""
Trang 4 — Actions & Rule Engine: quản lý rules, accept/skip actions.
"""
import streamlit as st
from engine import db, analytics
from engine.rule_engine import evaluate_rules_for_store

DATE = db.today_str()
YESTERDAY = db.yesterday_str()


def _resolve_date(store_id: str) -> tuple[str, bool]:
    """Trả về (date_str, is_fallback). Fallback sang hôm qua nếu hôm nay chưa có snapshot."""
    if db.get_snapshot(store_id, DATE):
        return DATE, False
    if db.get_snapshot(store_id, YESTERDAY):
        return YESTERDAY, True
    return DATE, False


def render(store_id: str):
    st.markdown("## ⚡ Actions & Rule Engine")

    # Kiểm tra outcome của các action đã Accept có snapshot ngày hôm sau
    db.evaluate_pending_outcomes(store_id)

    tab1, tab2, tab3 = st.tabs(["🚨 Actions Hôm Nay", "📋 Toàn Bộ Rules", "📈 Lịch Sử Feedback"])

    with tab1:
        _render_active_actions(store_id)

    with tab2:
        _render_all_rules(store_id)

    with tab3:
        _render_feedback_history(store_id)


def _render_active_actions(store_id: str):
    st.markdown("### Actions Đang Kích Hoạt Hôm Nay")

    effective_date, is_fallback = _resolve_date(store_id)

    if is_fallback:
        st.warning(
            f"⚠️ Chưa có dữ liệu hôm nay ({DATE}). "
            f"Đang hiển thị actions dựa trên dữ liệu **hôm qua ({effective_date})**. "
            f"Nhấn **Cập nhật ca hiện tại** ở trang Simulator để có dữ liệu mới nhất."
        )
    elif not db.get_snapshot(store_id, effective_date):
        st.info("ℹ️ Chưa có dữ liệu snapshot. Vui lòng chạy Simulator để tạo dữ liệu.")
        return

    st.markdown(
        f"<div style='color:#8b92a5;font-size:0.85rem;margin-bottom:12px'>"
        f"Dựa trên dữ liệu ngày {effective_date} — Chấp nhận hoặc bỏ qua từng action</div>",
        unsafe_allow_html=True
    )

    signals = evaluate_rules_for_store(store_id, effective_date)
    action_registry = {a["id"]: a for a in db.get_action_registry()}
    snap = db.get_snapshot(store_id, effective_date)

    if not signals:
        st.success("✅ Không có action nào cần thực hiện. Cửa hàng đang hoạt động tốt!")
        return

    feedback_given = st.session_state.get("feedback_given", {})

    for sig in signals:
        urgency_color = {"HIGH": "#ff6b6b", "MEDIUM": "#f7c948", "LOW": "#4ecca3"}[sig["urgency"]]
        urgency_vn = {"HIGH": "🔴 Khẩn", "MEDIUM": "🟡 Quan trọng", "LOW": "🟢 Tham khảo"}[sig["urgency"]]
        next_shift_badge = " 🔜 Ca tiếp theo" if sig.get("is_next_shift_alert") else ""

        with st.expander(f"{urgency_vn}{next_shift_badge} — {sig['rule_name']} (tin cậy {sig['confidence']*100:.0f}%)", expanded=True):
            col_info, col_actions = st.columns([3, 2])

            with col_info:
                st.markdown(f"""
<div style="background:#1e2130;border-left:3px solid {urgency_color};
            border-radius:0 8px 8px 0;padding:12px 16px">
<div style="color:#8b92a5;font-size:0.8rem;margin-bottom:4px">Nguyên nhân phát hiện:</div>
<div style="color:#e2e8f0;font-size:0.88rem;margin-bottom:8px">{sig['details']}</div>
<div style="color:#8b92a5;font-size:0.8rem;margin-bottom:4px">Lý do (WHY):</div>
<div style="color:#c9d1d9;font-size:0.85rem;font-style:italic">{sig['why']}</div>
</div>""", unsafe_allow_html=True)

            with col_actions:
                st.markdown("**Hành động đề xuất:**")
                for action_id in sig["actions"]:
                    action = action_registry.get(action_id, {"name": action_id, "type": "ops", "urgency": "MEDIUM"})
                    type_icon = {"product": "🏷️", "staff": "👥", "ops": "⚙️", "selling": "💡"}.get(action.get("type", ""), "•")
                    a_urgency_color = {"HIGH": "#ff6b6b", "MEDIUM": "#f7c948", "LOW": "#4ecca3"}.get(action.get("urgency", ""), "#8b92a5")
                    st.markdown(f"""
<div style="background:#252836;border-radius:6px;padding:6px 10px;margin:4px 0;
            font-size:0.82rem;border-left:2px solid {a_urgency_color}">
{type_icon} {action.get('name', action_id)}
</div>""", unsafe_allow_html=True)

                # Feedback buttons
                fb_key = f"{sig['rule_id']}_{store_id}"
                if fb_key in feedback_given:
                    decision = feedback_given[fb_key]
                    icon = "✅" if decision == "accept" else "⏭️"
                    label = "Đã chấp nhận" if decision == "accept" else "Đã bỏ qua"
                    color = "#4ecca3" if decision == "accept" else "#8b92a5"
                    st.markdown(f"<div style='color:{color};font-weight:600;margin-top:8px'>{icon} {label}</div>",
                                unsafe_allow_html=True)
                else:
                    col_acc, col_skip = st.columns(2)
                    with col_acc:
                        if st.button("✅ Chấp nhận", key=f"accept_{sig['rule_id']}",
                                     use_container_width=True, type="primary"):
                            db.save_action_feedback(
                                store_id, sig["rule_id"],
                                sig["actions"][0] if sig["actions"] else "",
                                "accept", snap
                            )
                            feedback_given[fb_key] = "accept"
                            st.session_state.feedback_given = feedback_given
                            db.add_notification(
                                store_id,
                                f"✅ Action được áp dụng: {sig['rule_name']}",
                                f"CHT đã chấp nhận action. Theo dõi kết quả trong 2h tới.",
                                notif_type="tip", urgency=sig["urgency"]
                            )
                            st.rerun()
                    with col_skip:
                        if st.button("⏭️ Bỏ qua", key=f"skip_{sig['rule_id']}",
                                     use_container_width=True):
                            db.save_action_feedback(
                                store_id, sig["rule_id"],
                                sig["actions"][0] if sig["actions"] else "",
                                "skip", snap
                            )
                            feedback_given[fb_key] = "skip"
                            st.session_state.feedback_given = feedback_given
                            st.rerun()


def _render_all_rules(store_id: str):
    st.markdown("### Toàn Bộ 12 Rules Trong Hệ Thống")
    rules = db.get_rules()
    signals = evaluate_rules_for_store(store_id, DATE)
    triggered_ids = {s["rule_id"] for s in signals}

    for rule in rules:
        is_triggered = rule["id"] in triggered_ids
        status_color = "#ff6b6b" if is_triggered else "#4ecca3"
        status_label = "🔴 Đang kích hoạt" if is_triggered else "🟢 Không kích hoạt"
        confidence = rule.get("confidence", 0.75)
        confidence_color = "#4ecca3" if confidence >= 0.80 else "#e8c84a" if confidence >= 0.70 else "#ff6b6b"

        with st.expander(f"{rule['id']} — {rule['name']}  |  {status_label}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Điều kiện:** `{rule['when']}`")
                st.markdown(f"**Actions:** {', '.join(rule['then'])}")
                st.markdown(f"**Lý do:** _{rule['why']}_")
            with col2:
                total_out  = rule.get("outcome_count", 0)
                pos_out    = rule.get("positive_outcomes", 0)
                neg_out    = rule.get("negative_outcomes", 0)
                pos_rate   = (pos_out / total_out * 100) if total_out > 0 else 0
                st.markdown(f"""
<div style="background:#1e2130;border-radius:8px;padding:12px">
<div style="margin-bottom:8px">
<span style="color:#8b92a5;font-size:0.78rem">Độ tin cậy</span><br>
<span style="color:{confidence_color};font-size:1.4rem;font-weight:700">{confidence*100:.0f}%</span>
</div>
<div style="margin-bottom:4px">
<span style="color:#8b92a5;font-size:0.78rem">Kết quả thực tế</span><br>
<span style="color:#4ecca3">📈 {pos_out}</span>
<span style="color:#8b92a5"> / </span>
<span style="color:#ff6b6b">📉 {neg_out}</span>
{"" if total_out == 0 else f"<span style='color:#8b92a5;font-size:0.78rem'> ({pos_rate:.0f}% hiệu quả)</span>"}
</div>
<div style="background:#252836;border-radius:4px;height:6px;margin-top:6px">
<div style="background:{confidence_color};height:6px;border-radius:4px;width:{confidence*100:.0f}%"></div>
</div>
</div>""", unsafe_allow_html=True)


def _render_feedback_history(store_id: str):
    st.markdown("### Lịch Sử Feedback — Actions Đã Áp Dụng")
    feedback = db.get_action_feedback(store_id)
    rules_map = {r["id"]: r for r in db.get_rules()}
    action_map = {a["id"]: a for a in db.get_action_registry()}

    if not feedback:
        st.info("Chưa có feedback nào. Hãy Accept/Skip các action ở tab đầu tiên.")
        return

    accepted = [f for f in feedback if f["decision"] == "accept"]
    skipped  = [f for f in feedback if f["decision"] == "skip"]
    positive = [f for f in accepted if f.get("outcome") == "positive"]
    negative = [f for f in accepted if f.get("outcome") == "negative"]
    pending  = [f for f in accepted if f.get("outcome") is None]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Đã Chấp Nhận", len(accepted))
    with col2:
        st.metric("📈 Hiệu quả", len(positive))
    with col3:
        st.metric("📉 Không hiệu quả", len(negative))
    with col4:
        st.metric("⏳ Chờ kết quả", len(pending))

    if accepted:
        rate = len(positive) / (len(positive) + len(negative)) * 100 if (positive or negative) else None
        if rate is not None:
            st.markdown(
                f"<div style='color:#8b92a5;font-size:0.85rem;margin:4px 0 12px'>"
                f"Tỷ lệ thành công khi áp dụng: "
                f"<span style='color:#4ecca3;font-weight:700'>{rate:.0f}%</span> "
                f"({len(positive)}/{len(positive)+len(negative)} actions)</div>",
                unsafe_allow_html=True
            )

    st.markdown(
        "<div style='color:#8b92a5;font-size:0.8rem;margin-bottom:12px'>"
        "⏳ Chờ kết quả = đã Accept nhưng chưa có snapshot ngày hôm sau để so sánh. "
        "Bỏ qua không ảnh hưởng đến confidence.</div>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    for fb in reversed(feedback[-20:]):
        rule = rules_map.get(fb.get("rule_id", ""), {})
        action = action_map.get(fb.get("action_id", ""), {})
        decision = fb["decision"]
        outcome = fb.get("outcome")

        if decision == "skip":
            border_color, icon, label = "#8b92a5", "⏭️", "Bỏ qua"
        elif outcome == "positive":
            border_color, icon, label = "#4ecca3", "📈", "Hiệu quả"
        elif outcome == "negative":
            border_color, icon, label = "#ff6b6b", "📉", "Không hiệu quả"
        else:
            border_color, icon, label = "#f7c948", "⏳", "Chờ kết quả"

        st.markdown(f"""
<div style="background:#1e2130;border-radius:8px;padding:10px 14px;margin:5px 0;
            border-left:3px solid {border_color}">
<div style="display:flex;justify-content:space-between;align-items:center">
  <span style="color:{border_color};font-weight:700">{icon} {label}</span>
  <span style="color:#8b92a5;font-size:0.8rem">{fb.get('timestamp','')}</span>
</div>
<div style="color:#e2e8f0;font-size:0.85rem;margin-top:4px">
  Rule: {rule.get('name', fb.get('rule_id',''))}
</div>
<div style="color:#8b92a5;font-size:0.8rem">
  Action: {action.get('name', fb.get('action_id',''))}
</div>
</div>""", unsafe_allow_html=True)

    # Rule confidence chart
    st.markdown("---")
    st.markdown("**Confidence Score Các Rules:**")
    rules = db.get_rules()
    import plotly.graph_objects as go
    fig = go.Figure(go.Bar(
        x=[r["id"] for r in rules],
        y=[r.get("confidence", 0.75) * 100 for r in rules],
        marker_color=["#4ecca3" if r.get("confidence", 0.75) >= 0.80
                      else "#e8c84a" if r.get("confidence", 0.75) >= 0.70
                      else "#ff6b6b" for r in rules],
        text=[f"{r.get('confidence', 0.75)*100:.0f}%" for r in rules],
        textposition="outside",
    ))
    fig.update_layout(
        paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
        font_color="#e2e8f0", height=280,
        xaxis={"gridcolor": "#2d3250"},
        yaxis={"gridcolor": "#2d3250", "range": [0, 110], "title": "Confidence %"},
        margin=dict(l=10, r=10, t=20, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)
