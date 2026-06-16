"""
AI Store Copilot — PNJ
Entry point Streamlit. Sidebar navigation, store selector, session state.
"""
import hmac
import streamlit as st
import sys
import os
from dotenv import load_dotenv

# Đảm bảo import từ root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from engine import db
import engine.llm as _llm

AUTH_USERNAME = os.getenv("AUTH_USERNAME", "").strip()
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "")

st.set_page_config(
    page_title="AI Store Copilot — PNJ",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS tùy chỉnh ────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Font và màu nền chính */
.main { background-color: #0f1117; }
[data-testid="stSidebar"] { background-color: #1a1d27; }

/* Card metric */
.metric-card {
    background: linear-gradient(135deg, #1e2130 0%, #252836 100%);
    border: 1px solid #2d3250;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 6px 0;
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #e8c84a;
    line-height: 1.1;
}
.metric-label {
    font-size: 0.82rem;
    color: #8b92a5;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.metric-delta-up { color: #4ecca3; font-size: 0.85rem; }
.metric-delta-down { color: #ff6b6b; font-size: 0.85rem; }

/* Alert badges */
.badge-high { background:#ff6b6b22; color:#ff6b6b; border:1px solid #ff6b6b55;
              border-radius:6px; padding:2px 8px; font-size:0.78rem; font-weight:600; }
.badge-medium { background:#f7c94822; color:#f7c948; border:1px solid #f7c94855;
                border-radius:6px; padding:2px 8px; font-size:0.78rem; font-weight:600; }
.badge-low { background:#4ecca322; color:#4ecca3; border:1px solid #4ecca355;
             border-radius:6px; padding:2px 8px; font-size:0.78rem; font-weight:600; }

/* Chat bubbles */
.chat-user {
    background: #2d3250; border-radius: 12px 12px 4px 12px;
    padding: 10px 14px; margin: 6px 40px 6px 0;
    color: #e2e8f0; font-size: 0.95rem;
}
.chat-ai {
    background: linear-gradient(135deg, #1a2a1a, #1e2830);
    border: 1px solid #2d5a3a;
    border-radius: 4px 12px 12px 12px;
    padding: 10px 14px; margin: 6px 0 6px 40px;
    color: #e2e8f0; font-size: 0.95rem;
}

/* Section headers */
.section-header {
    font-size: 0.75rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: #8b92a5;
    border-bottom: 1px solid #2d3250; padding-bottom: 6px; margin: 16px 0 10px;
}

/* Health score gauge color */
.health-a { color: #4ecca3; }
.health-b { color: #e8c84a; }
.health-c { color: #f7a948; }
.health-d { color: #ff6b6b; }

/* Streamlit button override */
.stButton > button {
    border-radius: 8px; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ─── Session state defaults ───────────────────────────────────────────────────

def _init_state():
    defaults = {
        "authenticated": False,
        "selected_store": "STR-002",
        "ai_ok": False,
        "llm_cache": {},   # {cache_key: result}
        "openai_api_key": os.getenv("OPENAI_API_KEY", "").strip(),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# ─── Login gate ───────────────────────────────────────────────────────────────

def _check_login(username: str, password: str) -> bool:
    return (
        hmac.compare_digest(username.strip(), AUTH_USERNAME)
        and hmac.compare_digest(password, AUTH_PASSWORD)
    )


def _render_login():
    if not AUTH_USERNAME or not AUTH_PASSWORD:
        st.error("Thiếu cấu hình đăng nhập. Vui lòng khai báo AUTH_USERNAME và AUTH_PASSWORD trong file .env.")
        st.stop()

    st.markdown(
        """
<div style="max-width:420px;margin:8vh auto 18px auto;text-align:center">
  <div style="font-size:2.4rem;font-weight:800;color:#e8c84a;margin-bottom:6px">AI Store Copilot</div>
  <div style="color:#8b92a5;font-size:0.95rem">Đăng nhập để tiếp tục</div>
</div>
""",
        unsafe_allow_html=True,
    )

    _, col, _ = st.columns([1, 1.15, 1])
    with col:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            submitted = st.form_submit_button("Đăng nhập", use_container_width=True, type="primary")

        if submitted:
            if _check_login(username, password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Tên đăng nhập hoặc mật khẩu không đúng.")


if not st.session_state.authenticated:
    _render_login()
    st.stop()

# ─── AI availability check ───────────────────────────────────────────────────

# Sync OpenAI key từ session state vào module llm (chạy mỗi lần render)
_llm.set_openai_key(st.session_state.openai_api_key)

st.session_state.ai_ok = _llm.is_openai_enabled()

# Chỉ hiện cảnh báo khi chưa có OpenAI key.
if not st.session_state.ai_ok:
    st.warning(
        "⚠️ **Chưa có OpenAI API Key** — cấu hình `OPENAI_API_KEY` trong file `.env` "
        "hoặc biến môi trường trước khi chạy app. "
        "Toàn bộ dữ liệu và biểu đồ vẫn hoạt động bình thường.",
        icon="🤖"
    )

# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 💎 AI Store Copilot")
    st.markdown("<div style='color:#8b92a5;font-size:0.8rem;margin-bottom:16px'>PNJ · Phiên bản POC</div>",
                unsafe_allow_html=True)
    if st.button("Đăng xuất", key="btn_logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.llm_cache = {}
        st.rerun()
    st.markdown("---")

    stores = db.get_stores()
    if not stores:
        st.error("Chưa có dữ liệu. Chạy `python data/seed_data.py` trước.")
        st.stop()

    store_options = {s["id"]: f"{s['id']} · {s['name']}" for s in stores}
    selected = st.selectbox(
        "🏪 Chọn cửa hàng",
        options=list(store_options.keys()),
        format_func=lambda x: store_options[x],
        index=list(store_options.keys()).index(st.session_state.selected_store),
        key="store_selector",
    )
    if selected != st.session_state.selected_store:
        st.session_state.selected_store = selected
        st.session_state.llm_cache = {}
        st.rerun()

    store = db.get_store(st.session_state.selected_store)
    if store:
        st.markdown(f"""
<div style='background:#1e2130;border-radius:8px;padding:10px 12px;margin:8px 0;font-size:0.82rem;color:#8b92a5'>
<b style='color:#e2e8f0'>{store['name']}</b><br>
📍 {store['city']} &nbsp;|&nbsp; Phân khúc {store['segment']}<br>
🎯 Target: <b style='color:#e8c84a'>{store['daily_target']/1e6:.0f}M đ/ngày</b>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div class='section-header'>Điều hướng</div>", unsafe_allow_html=True)

    pages = {
        "🏠 Dashboard": "dashboard",
        "💬 Chat Copilot": "chat",
        "☀️ Họp Ca Sáng": "morning",
        "📅 Trong hôm nay": "today",
        "⚡ Actions & Rules": "actions",
        "📊 Analytics 30 Ngày": "analytics",
        "🔔 Thông Báo": "notifications",
        "🔄 Mô Phỏng Dữ Liệu": "simulator",
    }

    if "current_page" not in st.session_state:
        st.session_state.current_page = "dashboard"

    for label, page_id in pages.items():
        is_active = st.session_state.current_page == page_id
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, key=f"nav_{page_id}", use_container_width=True, type=btn_type):
            st.session_state.current_page = page_id
            st.rerun()

    st.markdown("---")
    from datetime import date as _date
    from engine import db as _db
    latest = _db.get_latest_data_date(st.session_state.selected_store)
    today_real = _date.today().isoformat()
    date_label = latest if latest else today_real
    gap_indicator = " ⚠️" if latest and latest < today_real else ""
    st.markdown(
        f"<div style='font-size:0.78rem;color:#8b92a5'>📅 Dữ liệu: {date_label}{gap_indicator}</div>",
        unsafe_allow_html=True
    )

# ─── Page routing ────────────────────────────────────────────────────────────

page = st.session_state.current_page
store_id = st.session_state.selected_store

if page == "dashboard":
    from pages.dashboard import render
    render(store_id)
elif page == "chat":
    from pages.chat import render
    render(store_id)
elif page == "morning":
    from pages.morning import render
    render(store_id)
elif page == "today":
    from pages.today import render
    render(store_id)
elif page == "actions":
    from pages.actions import render
    render(store_id)
elif page == "analytics":
    from pages.analytics_page import render
    render(store_id)
elif page == "notifications":
    from pages.notifications import render
    render(store_id)
elif page == "simulator":
    from pages.simulator_page import render
    render(store_id)
