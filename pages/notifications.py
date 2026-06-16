"""
Trang 6 — Notifications: feed thông báo theo thời gian.
"""
import streamlit as st
from engine import db
from engine import llm

DATE = "2026-04-30"

NOTIF_TEMPLATES = [
    ("morning", "07:30", "📊"),
    ("midday", "11:30", "📈"),
    ("afternoon", "15:30", "⚡"),
    ("eod", "21:15", "🌙"),
]


def render(store_id: str):
    st.markdown("## 🔔 Thông Báo")
    store = db.get_store(store_id)
    store_name = store["name"] if store else store_id

    col_action, _ = st.columns([2, 3])
    with col_action:
        with st.expander("➕ Tạo Thông Báo Demo"):
            st.markdown("Tạo thông báo AI theo các mốc thời gian trong ngày:")
            for notif_type, time_label, icon in NOTIF_TEMPLATES:
                if st.button(
                    f"{icon} Thông báo {time_label}",
                    key=f"gen_notif_{notif_type}",
                    disabled=not st.session_state.ai_ok,
                    use_container_width=True
                ):
                    with st.spinner(f"AI đang tạo thông báo {time_label}..."):
                        title, body = llm.gen_notification_content(store_id, DATE, notif_type)
                        db.add_notification(
                            store_id, title, body,
                            notif_type="summary" if notif_type in ("morning", "eod") else "tip",
                            urgency="MEDIUM"
                        )
                    st.success(f"✅ Đã tạo thông báo {time_label}!")
                    st.rerun()

            if not st.session_state.ai_ok:
                st.caption("⚠️ Cần OpenAI API Key")

            st.markdown("---")
            if st.button("📌 Tạo thông báo mẫu không cần AI", key="gen_demo_notifs",
                         use_container_width=True):
                _create_demo_notifications(store_id, store_name)
                st.success("✅ Đã tạo 4 thông báo mẫu!")
                st.rerun()

    st.markdown("---")

    # Filters
    col_filter, col_mark = st.columns([3, 1])
    with col_filter:
        filter_type = st.selectbox(
            "Lọc theo loại:",
            options=["Tất cả", "Cảnh báo (alert)", "Gợi ý (tip)", "Tổng kết (summary)", "Sức khỏe (health)"],
            key="notif_filter"
        )
    with col_mark:
        if st.button("✅ Đánh dấu tất cả đã đọc", key="mark_all_read",
                     use_container_width=True):
            notifs = db.get_notifications(store_id)
            for n in notifs:
                if not n.get("read"):
                    db.mark_notification_read(n["id"])
            st.rerun()

    # Notification feed
    notifs = db.get_notifications(store_id)

    type_filter_map = {
        "Tất cả": None,
        "Cảnh báo (alert)": "alert",
        "Gợi ý (tip)": "tip",
        "Tổng kết (summary)": "summary",
        "Sức khỏe (health)": "health",
    }
    filter_val = type_filter_map[filter_type]
    if filter_val:
        notifs = [n for n in notifs if n.get("type") == filter_val]

    if not notifs:
        st.markdown("""
<div style="text-align:center;padding:60px 20px;color:#8b92a5">
<div style="font-size:2.5rem">🔔</div>
<div style="font-size:1rem;margin-top:8px">Chưa có thông báo nào.</div>
<div style="font-size:0.85rem;margin-top:4px">Tạo thông báo demo bằng nút phía trên.</div>
</div>""", unsafe_allow_html=True)
        return

    unread_count = sum(1 for n in notifs if not n.get("read"))
    if unread_count > 0:
        st.markdown(f"<div style='color:#e8c84a;font-size:0.88rem;margin-bottom:8px'>"
                    f"🔴 {unread_count} thông báo chưa đọc</div>", unsafe_allow_html=True)

    for notif in notifs:
        _render_notification(notif)


def _render_notification(notif: dict):
    notif_type = notif.get("type", "tip")
    urgency = notif.get("urgency", "MEDIUM")
    is_read = notif.get("read", False)

    type_config = {
        "alert": {"icon": "⚠️", "color": "#ff6b6b", "label": "Cảnh báo"},
        "tip": {"icon": "💡", "color": "#e8c84a", "label": "Gợi ý"},
        "summary": {"icon": "📊", "color": "#4ecca3", "label": "Tổng kết"},
        "health": {"icon": "❤️", "color": "#667eea", "label": "Sức khỏe"},
    }
    cfg = type_config.get(notif_type, type_config["tip"])

    opacity = "0.6" if is_read else "1"
    border_opacity = "44" if is_read else "aa"

    st.markdown(f"""
<div style="background:#1e2130;border:1px solid {cfg['color']}{border_opacity};border-radius:12px;
            padding:14px 18px;margin:8px 0;opacity:{opacity}">
<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
<div style="display:flex;align-items:center;gap:10px">
<span style="font-size:1.3rem">{cfg['icon']}</span>
<div>
<div style="font-weight:700;color:#e2e8f0;font-size:0.95rem">{notif['title']}</div>
<div style="font-size:0.75rem;color:#6b7280;margin-top:2px">{notif.get('created_at','')}</div>
</div>
</div>
<div style="display:flex;gap:6px;align-items:center">
<span style="background:{cfg['color']}22;color:{cfg['color']};border:1px solid {cfg['color']}55;
     border-radius:4px;padding:1px 8px;font-size:0.72rem;font-weight:600">{cfg['label']}</span>
{'<span style="color:#6b7280;font-size:0.72rem">Đã đọc</span>' if is_read else ''}
</div>
</div>
<div style="color:#c9d1d9;font-size:0.88rem;line-height:1.6;white-space:pre-line">{notif['body']}</div>
</div>""", unsafe_allow_html=True)

    if not is_read:
        col1, _ = st.columns([1, 6])
        with col1:
            if st.button("Đánh dấu đọc", key=f"read_{notif['id']}", use_container_width=True):
                db.mark_notification_read(notif["id"])
                st.rerun()


def _create_demo_notifications(store_id: str, store_name: str):
    demo_notifs = [
        (
            "📊 Báo cáo sáng 07:30",
            "Hôm qua cửa hàng đạt 85.2% target (78.4M/92M đồng). Traffic thấp hơn baseline 12.5% "
            "nhưng CR cải thiện nhẹ. ⚠️ Nhẫn cưới chỉ đạt 23.2% doanh thu — cần tập trung hôm nay. "
            "Hôm nay ca chiều có Bảo Ngọc + Thu Hương — đây là cơ hội vàng!",
            "summary", "MEDIUM"
        ),
        (
            "📈 Cập nhật giữa ca 11:30",
            "Doanh thu đến 11h30 ước đạt 28M đồng (≈30% target). Traffic sáng 42 lượt — đúng baseline thứ Tư. "
            "CR ca sáng 38% — ổn định. Cần tăng tốc trong ca chiều. "
            "💡 Gợi ý: Chuẩn bị Bảo Ngọc tư vấn nhóm khách couple đang tăng.",
            "tip", "MEDIUM"
        ),
        (
            "⚡ Cảnh báo trước cao điểm 15:30",
            "Dự báo traffic 17h–20h hôm nay: 45–55 lượt (thấp hơn 10% do thời tiết âm u). "
            "⚠️ RULE-01 kích hoạt: Nhẫn cưới đang thấp — cần push ngay khi ca chiều bắt đầu. "
            "✅ Đội hình tốt: Bảo Ngọc + Thu Hương sẵn sàng ở ca chiều.",
            "alert", "HIGH"
        ),
        (
            "🌙 Tổng kết cuối ngày 21:15",
            "Kết quả ngày hôm nay đang trong quá trình tổng hợp. "
            "Dựa trên pace đến 20h: ước đạt 88–92M đồng. "
            "💡 Bài học hôm nay: Ca chiều có đội hình mạnh → nhẫn cưới tốt hơn hôm qua rõ rệt. "
            "Cảm ơn cả team vì nỗ lực hôm nay! 🎉",
            "summary", "LOW"
        ),
    ]
    for title, body, t, urgency in demo_notifs:
        db.add_notification(store_id, title, body, t, urgency)
