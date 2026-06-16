"""
Trang 2 — Chat Copilot: hỏi đáp tự nhiên tiếng Việt.
"""
import streamlit as st
from engine import db
from engine import llm

SUGGESTED_QUESTIONS = [
    "Doanh thu hiện tại ngày hôm nay là bao nhiêu?",
    "Vì sao hôm qua nhẫn cưới bán chậm?",
    "Ca chiều hôm qua ổn không?",
    "Nhân viên nào hiệu quả nhất hôm qua?",
    "So với baseline, tỷ lệ chuyển đổi hôm qua thế nào?",
    "Hôm nay nên focus vào SKU nào?",
    "Nếu giữ đội hình này đến 20h, có đạt target không?",
    "Nhóm khách nữ độc thân đang chiếm bao nhiêu %?",
    "Bảo Ngọc hôm qua làm ca nào và kết quả ra sao?",
]


def render(store_id: str):
    st.markdown("## 💬 Chat Copilot")
    store = db.get_store(store_id)
    store_name = store["name"] if store else store_id
    data_date = db.get_latest_data_date(store_id) or db.today_str()

    st.markdown(
        f"<div style='color:#8b92a5;font-size:0.88rem;margin-bottom:12px'>"
        f"🏪 {store_name} &nbsp;|&nbsp; 📅 Dữ liệu mới nhất: {data_date} &nbsp;|&nbsp; "
        f"AI sẽ trả lời dựa trên số liệu thực tế của cửa hàng</div>",
        unsafe_allow_html=True
    )

    # Lấy lịch sử
    history = db.get_chat_history(store_id)

    # Hiển thị lịch sử
    chat_container = st.container()
    with chat_container:
        if not history:
            st.markdown("""
<div style="text-align:center;padding:40px 20px;color:#8b92a5">
<div style="font-size:2rem">💬</div>
<div style="font-size:1rem;margin-top:8px">Chưa có cuộc hội thoại nào.</div>
<div style="font-size:0.85rem;margin-top:4px">Chọn câu hỏi gợi ý bên dưới hoặc nhập câu hỏi của bạn.</div>
</div>""", unsafe_allow_html=True)
        else:
            for msg in history:
                if msg["role"] == "user":
                    st.markdown(f"""
<div style="display:flex;justify-content:flex-end;margin:6px 0">
<div style="background:#2d3250;border-radius:12px 12px 4px 12px;
            padding:10px 14px;max-width:75%;color:#e2e8f0;font-size:0.95rem">
{msg['content']}
</div>
</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
<div style="display:flex;justify-content:flex-start;margin:6px 0">
<div style="background:linear-gradient(135deg,#1a2a1a,#1e2830);border:1px solid #2d5a3a;
            border-radius:4px 12px 12px 12px;padding:10px 14px;max-width:85%;
            color:#e2e8f0;font-size:0.95rem;line-height:1.6">
{msg['content'].replace(chr(10), '<br>')}
</div>
</div>""", unsafe_allow_html=True)
                    if msg.get("timestamp"):
                        st.markdown(
                            f"<div style='color:#6b7280;font-size:0.72rem;margin:-4px 0 4px 14px'>"
                            f"{msg['timestamp']}</div>",
                            unsafe_allow_html=True
                        )

    # Câu hỏi gợi ý
    st.markdown("<div class='section-header'>💡 Câu hỏi gợi ý</div>", unsafe_allow_html=True)
    cols = st.columns(2)
    for i, q in enumerate(SUGGESTED_QUESTIONS):
        with cols[i % 2]:
            if st.button(q, key=f"suggest_{i}", use_container_width=True,
                         disabled=not st.session_state.ai_ok):
                _send_message(store_id, q, history)
                st.rerun()

    # Input chat
    st.markdown("<div class='section-header'>✍️ Nhập câu hỏi</div>", unsafe_allow_html=True)
    col_input, col_send = st.columns([5, 1])
    with col_input:
        user_input = st.text_input(
            "Hỏi AI Copilot...",
            key="chat_input",
            placeholder="VD: Tại sao doanh thu ca chiều lại thấp hơn hôm qua?",
            label_visibility="collapsed",
        )
    with col_send:
        send_clicked = st.button("Gửi ➤", key="btn_send",
                                 disabled=not st.session_state.ai_ok,
                                 use_container_width=True, type="primary")

    if not st.session_state.ai_ok:
        st.warning("⚠️ Cần OpenAI API Key để chat. Nhập key ở sidebar hoặc cấu hình OPENAI_API_KEY.")

    if send_clicked and user_input.strip():
        _send_message(store_id, user_input.strip(), history)
        st.rerun()

    # Nút xóa lịch sử
    st.markdown("---")
    col_clear, _ = st.columns([1, 4])
    with col_clear:
        if st.button("🗑️ Xóa lịch sử chat", key="btn_clear_chat"):
            db.clear_chat(store_id)
            st.rerun()


def _send_message(store_id: str, message: str, history: list):
    db.append_chat(store_id, "user", message)
    with st.spinner("AI đang trả lời..."):
        data_date = db.get_latest_data_date(store_id) or db.today_str()
        response = llm.chat_with_copilot(store_id, data_date, message, history)
    db.append_chat(store_id, "assistant", response)
