"""
Trang Mô Phỏng Dữ Liệu — tạo dữ liệu ngày thực tế bằng OpenAI.
Hỗ trợ sinh dữ liệu từng ca theo giờ thực tế và phản ánh feedback.
"""
import streamlit as st
from datetime import date, datetime, timedelta
from engine import db, analytics, simulator
from engine.rule_engine import evaluate_rules_for_store


def _weather_icon(weather: str) -> str:
    w = weather.lower()
    if "mưa to" in w:
        return "⛈️"
    if "mưa" in w:
        return "🌧️"
    if "âm u" in w:
        return "☁️"
    return "☀️"


def render(store_id: str):
    st.markdown("## 🔄 Mô Phỏng Dữ Liệu Thực Tế")

    store = db.get_store(store_id)
    if not store:
        st.error("Không tìm thấy cửa hàng.")
        return

    today = date.today()
    latest = db.get_latest_data_date(store_id)
    missing_dates = simulator.get_missing_dates(store_id)
    openai_ok = simulator.check_openai()

    # ─── Trạng thái hiện tại ──────────────────────────────────────────────────
    col_info, col_action = st.columns([3, 2])

    with col_info:
        st.markdown("### 📊 Trạng thái dữ liệu")
        latest_label = latest or "Chưa có data"
        today_label = today.isoformat()

        status_color = "#4ecca3" if not missing_dates else "#e8c84a"
        gap_text = (f"{len(missing_dates)} ngày chưa có dữ liệu"
                    if missing_dates else "Đã cập nhật đến hôm nay")

        st.markdown(f"""
<div style="background:#1e2130;border-radius:10px;padding:16px 20px;margin-bottom:12px">
<div style="display:flex;gap:24px;flex-wrap:wrap">
<div>
  <div style="color:#8b92a5;font-size:0.78rem">Ngày mới nhất có data</div>
  <div style="font-size:1.2rem;font-weight:700;color:#e2e8f0">{latest_label}</div>
</div>
<div>
  <div style="color:#8b92a5;font-size:0.78rem">Hôm nay thực tế</div>
  <div style="font-size:1.2rem;font-weight:700;color:#e8c84a">{today_label}</div>
</div>
<div>
  <div style="color:#8b92a5;font-size:0.78rem">Trạng thái</div>
  <div style="font-size:1.1rem;font-weight:700;color:{status_color}">{gap_text}</div>
</div>
</div>
</div>""", unsafe_allow_html=True)

        if missing_dates:
            st.markdown("**Các ngày cần tạo dữ liệu:**")
            cols = st.columns(min(len(missing_dates), 7))
            for i, d in enumerate(missing_dates[:7]):
                dow_vn = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"][d.weekday()]
                cols[i].markdown(
                    f"<div style='background:#252836;border-radius:6px;padding:6px 10px;"
                    f"text-align:center;font-size:0.85rem'>"
                    f"<b style='color:#e8c84a'>{d.strftime('%d/%m')}</b>"
                    f"<br><span style='color:#8b92a5;font-size:0.75rem'>{dow_vn}</span></div>",
                    unsafe_allow_html=True
                )

    with col_action:
        st.markdown("### 🤖 Tạo dữ liệu mới")

        if not openai_ok:
            st.warning("⚠️ Chưa có OpenAI API Key — sẽ dùng kịch bản ngẫu nhiên thay thế AI.")

        # Hiển thị trạng thái ca hôm nay
        now = datetime.now()
        shift_status = simulator.get_shift_status(now)
        shift_labels = {
            "morning": "Ca sáng (09–14h)",
            "afternoon": "Ca chiều (14–20h)",
            "evening": "Ca tối (20–22h)",
        }
        shift_status_vn = {"completed": "✅ Đã xong", "active": "🔄 Đang chạy", "upcoming": "⏳ Chưa bắt đầu"}
        shift_html_parts = []
        for s in simulator.SHIFTS:
            sname = s["name"]
            st_label = shift_status_vn.get(shift_status.get(sname, "upcoming"), "")
            shift_html_parts.append(
                f"<span style='margin-right:12px;font-size:0.82rem'>"
                f"<b style='color:#e2e8f0'>{shift_labels[sname]}</b>: "
                f"<span style='color:#8b92a5'>{st_label}</span>"
                f"</span>"
            )
        shift_html = "".join(shift_html_parts)
        st.markdown(
            f"<div style='background:#1e2130;border-radius:8px;padding:10px 14px;margin-bottom:10px'>"
            f"<div style='font-size:0.75rem;color:#8b92a5;margin-bottom:4px'>TRẠNG THÁI CA HÔM NAY</div>"
            f"{shift_html}</div>",
            unsafe_allow_html=True
        )

        # Feedback đang áp dụng
        adj = simulator.get_feedback_adjustments(store_id, for_date=today.isoformat())
        if adj.get("applied_actions"):
            acts_txt = ", ".join(adj["applied_actions"])
            st.info(f"Hành động đã áp dụng hôm nay sẽ ảnh hưởng ca tiếp theo: **{acts_txt}**")

        if not missing_dates:
            st.success("✅ Dữ liệu đã cập nhật đến hôm nay!")
            st.markdown("Nhấn **Cập nhật ca hiện tại** để regenerate dữ liệu đến giờ hiện tại.")
            regen_today = st.button("🔁 Cập nhật ca hiện tại", use_container_width=True, type="secondary")
            if regen_today:
                st.session_state["sim_target_dates"] = [today]
                st.session_state["run_sim"] = True
                st.rerun()
        else:
            n = len(missing_dates)
            label = f"🚀 Tạo dữ liệu {n} ngày với AI" if n > 1 else "🚀 Cập nhật dữ liệu hôm nay với AI"
            if st.button(label, use_container_width=True, type="primary"):
                st.session_state["sim_target_dates"] = missing_dates
                st.session_state["run_sim"] = True
                st.rerun()

        st.caption(
            "OpenAI tạo kịch bản theo giờ thực tế. Hôm nay chỉ generate đến "
            f"{now.hour:02d}:{now.minute:02d}. Feedback ca trước tự động điều chỉnh tham số."
        )

    st.markdown("---")

    # ─── Chạy simulation ──────────────────────────────────────────────────────
    if st.session_state.get("run_sim"):
        st.session_state["run_sim"] = False
        target_dates = st.session_state.get("sim_target_dates", missing_dates)

        progress_bar = st.progress(0, text="Đang khởi động...")
        log_box = st.empty()
        log_lines = []

        def progress_cb(msg: str):
            log_lines.append(f"• {msg}")
            log_box.markdown(
                "<div style='background:#1e2130;border-radius:8px;padding:12px;"
                "font-size:0.85rem;color:#8b92a5'>"
                + "<br>".join(log_lines[-8:])
                + "</div>",
                unsafe_allow_html=True
            )

        result = simulator.run_simulation(
            store_id,
            target_dates=target_dates,
            progress_cb=progress_cb
        )
        progress_bar.progress(100, text="Hoàn tất!")

        # Lưu kết quả vào session để hiển thị
        st.session_state["sim_result"] = result
        st.session_state["sim_store_id"] = store_id
        st.rerun()

    # ─── Hiển thị kết quả simulation ──────────────────────────────────────────
    result = st.session_state.get("sim_result")
    if result and st.session_state.get("sim_store_id") == store_id:
        if result.get("error"):
            st.error(result["error"])
            return

        scenarios = result.get("scenarios", [])
        if not scenarios:
            st.info(result.get("message", "Không có ngày nào cần tạo."))
            return

        st.markdown("### 📋 Kết quả Simulation")
        st.success(
            f"✅ Đã tạo dữ liệu **{result['dates_generated']} ngày** — "
            f"**{result['total_transactions']:,} giao dịch** mới cho {result['store_name']}"
        )

        for sc in scenarios:
            scen = sc["scenario"]
            weather_icon = _weather_icon(scen.get("weather", ""))
            target_pct = sc["target_pct"]
            pct_color = "#4ecca3" if target_pct >= 95 else "#e8c84a" if target_pct >= 75 else "#ff6b6b"
            event_txt = f"📌 {scen['event']}" if scen.get("event") else ""
            staff_txt = f"⚠️ {scen['staff_issue']}" if scen.get("staff_issue") else ""
            hot_txt = f"🔥 Hot: {scen['hot_category']} ×{scen['hot_category_mult']}" if scen.get("hot_category") else ""
            promo_txt = "🎁 Khuyến mãi đang chạy" if scen.get("promo_active") else ""
            partial_txt = (
                f"🕐 Đến {sc['max_hour']:02d}:{sc.get('current_minute', 0):02d} "
                "(đang diễn ra)"
                if sc.get("is_partial")
                else ""
            )
            feedback_acts = sc.get("feedback_applied", [])
            feedback_txt = f"💡 Áp dụng từ ca trước: {', '.join(feedback_acts)}" if feedback_acts else ""

            tags = " &nbsp;|&nbsp; ".join(
                t for t in [partial_txt, event_txt, staff_txt, hot_txt, promo_txt, feedback_txt] if t
            )

            # Shift breakdown cho ngày hôm nay
            shift_info_html = ""
            if sc.get("shift_info"):
                shift_status_colors = {"completed": "#4ecca3", "active": "#e8c84a", "upcoming": "#555e72"}
                shift_names_vn = {"morning": "Sáng", "afternoon": "Chiều", "evening": "Tối"}
                shift_rows = []
                for sname, sdata in sc["shift_info"].items():
                    color = shift_status_colors.get(sdata["status"], "#555e72")
                    rev_m = sdata["revenue"] / 1e6
                    status_label = {"completed": "Xong", "active": "Đang chạy", "upcoming": "Chưa bắt đầu"}.get(sdata["status"], "")
                    shift_rows.append(
                        f"<span style='margin-right:16px;font-size:0.80rem'>"
                        f"<b style='color:{color}'>{shift_names_vn.get(sname, sname)}</b>: "
                        f"{rev_m:.1f}M đ <span style='color:#8b92a5'>({status_label})</span></span>"
                    )
                shift_info_html = (
                    f"<div style='margin-top:8px;padding-top:8px;border-top:1px solid #2d3250'>"
                    + "".join(shift_rows)
                    + "</div>"
                )

            st.markdown(f"""
<div style="background:linear-gradient(135deg,#1e2130,#252836);border:1px solid #2d3250;
            border-radius:10px;padding:16px 20px;margin:8px 0">
<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px">
  <div style="flex:1">
    <div style="font-size:0.78rem;color:#8b92a5;text-transform:uppercase;letter-spacing:0.08em">
      {sc['date']}</div>
    <div style="font-size:1.1rem;font-weight:700;color:#e2e8f0;margin:4px 0">
      {weather_icon} {scen.get('weather','').capitalize()}</div>
    <div style="font-size:0.88rem;color:#b0b7c3;margin-top:4px">{scen.get('description','')}</div>
    {f'<div style="font-size:0.82rem;color:#8b92a5;margin-top:6px">{tags}</div>' if tags else ''}
    {shift_info_html}
  </div>
  <div style="text-align:right;min-width:160px">
    <div style="font-size:1.8rem;font-weight:800;color:{pct_color}">{target_pct}%</div>
    <div style="font-size:0.78rem;color:#8b92a5">so với target</div>
    <div style="font-size:0.85rem;color:#e2e8f0;margin-top:4px">
      {sc['revenue']/1e6:.1f}M đ &nbsp;·&nbsp; {sc['traffic']} lượt &nbsp;·&nbsp; CR {sc['cr']}%
    </div>
    <div style="font-size:0.78rem;color:#8b92a5">{sc['transactions']} giao dịch</div>
  </div>
</div>
</div>""", unsafe_allow_html=True)

        # ─── Xem rule engine trigger sau simulation ────────────────────────────
        st.markdown("---")
        st.markdown("### ⚡ Rules được kích hoạt sau simulation")

        latest_after = db.get_latest_data_date(store_id)
        if latest_after:
            signals = evaluate_rules_for_store(store_id, latest_after)
            if signals:
                for sig in signals:
                    urg = sig["urgency"]
                    urg_color = {"HIGH": "#ff6b6b", "MEDIUM": "#f7c948", "LOW": "#4ecca3"}[urg]
                    st.markdown(f"""
<div style="background:#1e2130;border-left:3px solid {urg_color};
            border-radius:6px;padding:10px 14px;margin:6px 0">
<div style="display:flex;justify-content:space-between;align-items:center">
  <div>
    <span style="background:{urg_color}22;color:{urg_color};border:1px solid {urg_color}44;
                 border-radius:4px;padding:1px 7px;font-size:0.75rem;font-weight:700">{urg}</span>
    <b style="color:#e2e8f0;margin-left:8px">{sig['rule_name']}</b>
    <span style="color:#8b92a5;font-size:0.82rem;margin-left:8px">
      (Confidence {sig['confidence']*100:.0f}%)</span>
  </div>
</div>
<div style="color:#8b92a5;font-size:0.83rem;margin-top:6px">{sig['details']}</div>
</div>""", unsafe_allow_html=True)
            else:
                st.success("Không có rule nào triggered — cửa hàng đang hoạt động tốt!")

        # ─── Nút xem dashboard ────────────────────────────────────────────────
        st.markdown("---")
        if st.button("📊 Xem Dashboard ngày mới nhất", type="primary", use_container_width=False):
            st.session_state["current_page"] = "dashboard"
            st.session_state.pop("sim_result", None)
            st.rerun()
