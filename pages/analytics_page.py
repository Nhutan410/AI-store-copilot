"""
Trang 5 — Analytics 30 ngày: charts xu hướng, so sánh, hiệu suất.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from engine import db, analytics

DATE = "2026-04-30"


def render(store_id: str):
    st.markdown("## 📊 Analytics 30 Ngày")
    store = db.get_store(store_id)
    if not store:
        st.error("Không tìm thấy cửa hàng.")
        return

    tab1, tab2, tab3 = st.tabs(["📈 Xu Hướng", "👥 Hiệu Suất NV", "🔄 So Sánh Chuỗi"])

    with tab1:
        _render_trends(store_id, store)
    with tab2:
        _render_staff_performance(store_id)
    with tab3:
        _render_cross_store(store_id, store, DATE)


def _render_trends(store_id: str, store: dict):
    # Chart 1: Revenue vs Target
    st.markdown("### 💰 Doanh Thu vs Target — 30 Ngày")
    revenue_data = analytics.get_revenue_trend(store_id, 30)
    if revenue_data:
        fig = go.Figure()
        colors = ["#4ecca3" if d["target_pct"] >= 95 else "#e8c84a" if d["target_pct"] >= 80 else "#ff6b6b"
                  for d in revenue_data]
        fig.add_trace(go.Bar(
            x=[d["date"] for d in revenue_data],
            y=[d["revenue"] / 1e6 for d in revenue_data],
            name="Doanh thu thực tế",
            marker_color=colors,
            hovertemplate="%{x}<br>Doanh thu: %{y:.1f}M đ<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=[d["date"] for d in revenue_data],
            y=[store["daily_target"] / 1e6] * len(revenue_data),
            name="Target",
            line={"color": "#e8c84a", "dash": "dash", "width": 2},
            mode="lines",
        ))
        fig.update_layout(
            paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
            font_color="#e2e8f0", height=300,
            xaxis={"gridcolor": "#2d3250", "tickangle": -45},
            yaxis={"gridcolor": "#2d3250", "title": "Triệu đồng"},
            legend={"bgcolor": "#1e2130"},
            margin=dict(l=10, r=10, t=10, b=60),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Summary stats
        total_rev = sum(d["revenue"] for d in revenue_data)
        avg_pct = sum(d["target_pct"] for d in revenue_data) / len(revenue_data)
        days_hit = sum(1 for d in revenue_data if d["target_pct"] >= 95)
        col1, col2, col3 = st.columns(3)
        col1.metric("Tổng DT 30 ngày", f"{total_rev/1e9:.2f}B đ")
        col2.metric("TB % Target", f"{avg_pct:.1f}%")
        col3.metric("Ngày đạt target (≥95%)", f"{days_hit}/{len(revenue_data)}")
    else:
        st.info("Chưa có dữ liệu.")

    st.markdown("---")

    # Chart 2 & 3: CR và Traffic side by side
    col_cr, col_tr = st.columns(2)

    with col_cr:
        st.markdown("### 📉 Tỷ Lệ Chuyển Đổi (CR)")
        cr_data = analytics.get_cr_trend(store_id, 30)
        if cr_data:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=[d["date"] for d in cr_data],
                y=[d["cr"] for d in cr_data],
                name="CR thực tế",
                line={"color": "#667eea", "width": 2},
                fill="tozeroy", fillcolor="rgba(102,126,234,0.13)",
                hovertemplate="%{x}<br>CR: %{y:.1f}%<extra></extra>",
            ))
            fig2.add_trace(go.Scatter(
                x=[d["date"] for d in cr_data],
                y=[d["baseline"] for d in cr_data],
                name="Baseline",
                line={"color": "#e8c84a", "dash": "dot", "width": 1.5},
                mode="lines",
            ))
            fig2.update_layout(
                paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
                font_color="#e2e8f0", height=250,
                xaxis={"gridcolor": "#2d3250", "tickangle": -45, "title": ""},
                yaxis={"gridcolor": "#2d3250", "title": "CR (%)"},
                legend={"bgcolor": "#1e2130"},
                margin=dict(l=10, r=10, t=10, b=50),
            )
            st.plotly_chart(fig2, use_container_width=True)

    with col_tr:
        st.markdown("### 🚶 Traffic & Baseline")
        tr_data = analytics.get_traffic_trend(store_id, 30)
        if tr_data:
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                x=[d["date"] for d in tr_data],
                y=[d["traffic"] for d in tr_data],
                name="Traffic thực tế",
                marker_color="#4ecca3",
                opacity=0.8,
            ))
            fig3.add_trace(go.Scatter(
                x=[d["date"] for d in tr_data],
                y=[d["baseline"] for d in tr_data],
                name="Baseline 14 ngày",
                line={"color": "#e8c84a", "dash": "dash", "width": 2},
                mode="lines",
            ))
            fig3.update_layout(
                paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
                font_color="#e2e8f0", height=250,
                xaxis={"gridcolor": "#2d3250", "tickangle": -45, "title": ""},
                yaxis={"gridcolor": "#2d3250", "title": "Lượt khách"},
                legend={"bgcolor": "#1e2130"},
                margin=dict(l=10, r=10, t=10, b=50),
            )
            st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # Chart 4: Category mix stacked bar
    st.markdown("### 🏷️ Cơ Cấu Doanh Thu Theo Danh Mục — 30 Ngày")
    cat_data = analytics.get_category_mix_trend(store_id, 30)
    if cat_data:
        categories = {
            "wedding_ring": ("Nhẫn cưới", "#e8c84a"),
            "engagement_ring": ("Nhẫn đính hôn", "#f7a948"),
            "fashion_ring": ("Nhẫn thời trang", "#4ecca3"),
            "bracelet": ("Lắc tay", "#667eea"),
            "necklace": ("Dây chuyền", "#6bcb77"),
            "earring": ("Bông tai", "#ff6b6b"),
            "watch": ("Đồng hồ", "#c77dff"),
            "accessory": ("Phụ kiện", "#48cae4"),
        }
        fig4 = go.Figure()
        for cat_id, (cat_name, color) in categories.items():
            values = [d.get(cat_id, 0) for d in cat_data]
            if any(v > 0 for v in values):
                fig4.add_trace(go.Bar(
                    x=[d["date"] for d in cat_data],
                    y=values,
                    name=cat_name,
                    marker_color=color,
                ))
        fig4.update_layout(
            barmode="stack",
            paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
            font_color="#e2e8f0", height=320,
            xaxis={"gridcolor": "#2d3250", "tickangle": -45},
            yaxis={"gridcolor": "#2d3250", "title": "% Doanh thu"},
            legend={"bgcolor": "#1e2130", "font": {"size": 10}},
            margin=dict(l=10, r=10, t=10, b=60),
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")

    # Heatmap: Revenue by day and hour (Store Health Timeline)
    st.markdown("### 🗓️ Store Health Timeline — Doanh Thu Theo Ngày")
    snaps_30 = db.get_snapshots(store_id, 30)
    if snaps_30:
        df_heat = pd.DataFrame([{
            "Ngày": s["date"],
            "% Target": round(s.get("target_pct", 0) * 100, 1),
            "Traffic": s.get("traffic", 0),
            "CR (%)": round(s.get("conversion_rate", 0) * 100, 1),
            "Thứ": s.get("day_of_week_vn", ""),
        } for s in snaps_30])
        df_heat = df_heat.sort_values("Ngày")

        fig_heat = px.imshow(
            df_heat[["% Target"]].T,
            x=df_heat["Ngày"],
            y=["% Target"],
            color_continuous_scale=[[0, "#ff6b6b"], [0.8, "#e8c84a"], [1, "#4ecca3"]],
            zmin=50, zmax=120,
            aspect="auto",
        )
        fig_heat.update_layout(
            paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
            font_color="#e2e8f0", height=120,
            xaxis={"tickangle": -45},
            coloraxis_colorbar={"title": "%"},
            margin=dict(l=80, r=10, t=10, b=50),
        )
        st.plotly_chart(fig_heat, use_container_width=True)


def _render_staff_performance(store_id: str):
    st.markdown("### 👥 Hiệu Suất Nhân Viên — 30 Ngày")
    perf_data = analytics.get_staff_performance_summary(store_id, 30)

    if not perf_data:
        st.info("Chưa có dữ liệu.")
        return

    # Staff Efficiency Matrix (scatter)
    st.markdown("**Ma Trận Hiệu Suất — Doanh Thu vs Số Đơn**")
    fig_scatter = go.Figure()

    level_colors = {"senior": "#4ecca3", "mid": "#e8c84a", "junior": "#f7a948"}
    for item in perf_data:
        color = level_colors.get(item.get("level", ""), "#8b92a5")
        fig_scatter.add_trace(go.Scatter(
            x=[item["avg_orders"]],
            y=[item["avg_daily_revenue"] / 1e6],
            mode="markers+text",
            marker={"color": color, "size": max(12, item["revenue"] / 5e6), "opacity": 0.8},
            text=[item["name"].split()[-1]],  # Họ cuối
            textposition="top center",
            name=item["name"],
            hovertemplate=(
                f"<b>{item['name']}</b><br>"
                f"DT TB: {item['avg_daily_revenue']/1e6:.1f}M đ<br>"
                f"Đơn TB: {item['avg_orders']:.1f}<br>"
                f"Level: {item.get('level','')}"
                "<extra></extra>"
            )
        ))

    fig_scatter.update_layout(
        paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
        font_color="#e2e8f0", height=350,
        showlegend=False,
        xaxis={"gridcolor": "#2d3250", "title": "Số đơn trung bình/ngày"},
        yaxis={"gridcolor": "#2d3250", "title": "DT TB/ngày (Triệu đ)"},
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Bar chart hiệu suất
    st.markdown("**Tổng Doanh Thu 30 Ngày — Theo Nhân Viên**")
    df = pd.DataFrame(perf_data)
    df = df.sort_values("revenue", ascending=False)

    fig_bar = go.Figure(go.Bar(
        x=df["name"],
        y=df["revenue"] / 1e6,
        marker_color=[level_colors.get(l, "#8b92a5") for l in df["level"]],
        text=[f"{v:.0f}M" for v in df["revenue"] / 1e6],
        textposition="outside",
        hovertemplate="%{x}<br>%{y:.1f}M đ<extra></extra>",
    ))
    fig_bar.update_layout(
        paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
        font_color="#e2e8f0", height=300,
        xaxis={"gridcolor": "#2d3250", "tickangle": -30},
        yaxis={"gridcolor": "#2d3250", "title": "Triệu đồng"},
        margin=dict(l=10, r=10, t=20, b=70),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Bảng chi tiết
    st.markdown("**Bảng Chi Tiết:**")
    level_vn = {"senior": "Senior", "mid": "Mid", "junior": "Junior"}
    table_data = [{
        "Tên": row["name"],
        "Level": level_vn.get(row["level"], row["level"]),
        "Tổng DT (M đ)": f"{row['revenue']/1e6:.1f}",
        "DT TB/ngày (M đ)": f"{row['avg_daily_revenue']/1e6:.1f}",
        "Tổng đơn": row["orders"],
        "Đơn TB/ngày": f"{row['avg_orders']:.1f}",
        "CR TB": f"{row['avg_cr']*100:.0f}%",
    } for _, row in df.iterrows()]
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

    # SKU Opportunity
    st.markdown("---")
    st.markdown("### 💎 SKU Opportunity Score — Cơ Hội Đang Bỏ Lỡ")
    sku_scores = analytics.get_sku_opportunity_scores(store_id, DATE)
    missed = [s for s in sku_scores if s["is_missed_opportunity"]][:8]

    if missed:
        st.warning(f"⚠️ Có **{len(missed)} SKU** tồn kho tốt, CVR cao nhưng chưa bán trong 7 ngày qua:")
        for sku in missed:
            score_color = "#4ecca3" if sku["opportunity_score"] > 0.2 else "#e8c84a"
            cat_vn = {
                "wedding_ring": "Nhẫn cưới", "engagement_ring": "Nhẫn đính hôn",
                "fashion_ring": "Nhẫn thời trang", "bracelet": "Lắc tay",
                "necklace": "Dây chuyền", "earring": "Bông tai",
                "watch": "Đồng hồ", "accessory": "Phụ kiện",
            }.get(sku["category"], sku["category"])
            st.markdown(f"""
<div style="background:#1e2130;border-radius:8px;padding:10px 14px;margin:4px 0;
            display:flex;justify-content:space-between;align-items:center">
<div>
<span style="color:#e2e8f0;font-weight:600">{sku['id']} — {sku['name']}</span>
<span style="color:#8b92a5;font-size:0.8rem;margin-left:8px">{cat_vn}</span><br>
<span style="color:#6b7280;font-size:0.78rem">
CVR: {sku['cvr_history']*100:.0f}% &nbsp;|&nbsp;
Margin: {sku['margin_pct']*100:.0f}% &nbsp;|&nbsp;
Tồn: {sku['stock']} {sku['unit']}
</span>
</div>
<div style="text-align:right">
<div style="color:{score_color};font-size:1.1rem;font-weight:700">
{sku['opportunity_score']:.3f}
</div>
<div style="color:#8b92a5;font-size:0.72rem">Opportunity</div>
</div>
</div>""", unsafe_allow_html=True)
    else:
        st.success("✅ Tất cả SKU đang được bán tốt trong 7 ngày qua!")


def _render_cross_store(store_id: str, store: dict, date_str: str):
    st.markdown("### 🔄 So Sánh Cùng Phân Khúc")
    segment = store["segment"]
    all_stores = db.get_stores()
    same_segment = [s for s in all_stores if s["segment"] == segment]

    benchmark = analytics.get_segment_benchmark(segment, date_str)
    snap_current = db.get_snapshot(store_id, date_str)

    st.markdown(f"**Phân khúc {segment} — {len(same_segment)} cửa hàng**")

    if snap_current and benchmark:
        metrics = [
            ("% Target", snap_current.get("target_pct", 0) * 100,
             benchmark.get("target_pct", 0) * 100, "%"),
            ("CR", snap_current.get("conversion_rate", 0) * 100,
             benchmark.get("conversion_rate", 0) * 100, "%"),
            ("Traffic", snap_current.get("traffic", 0),
             benchmark.get("traffic", 0), " lượt"),
            ("AOV", snap_current.get("aov", 0) / 1e6,
             benchmark.get("aov", 0) / 1e6, "M đ"),
        ]
        cols = st.columns(4)
        for i, (name, my_val, avg_val, unit) in enumerate(metrics):
            delta = my_val - avg_val
            delta_color = "#4ecca3" if delta >= 0 else "#ff6b6b"
            delta_sign = "+" if delta >= 0 else ""
            with cols[i]:
                st.markdown(f"""
<div class="metric-card">
<div class="metric-label">{name}</div>
<div class="metric-value" style="font-size:1.4rem">{my_val:.1f}{unit}</div>
<div style="font-size:0.78rem;color:#8b92a5">TB phân khúc: {avg_val:.1f}{unit}</div>
<div style="font-size:0.82rem;color:{delta_color}">{delta_sign}{delta:.1f}{unit} vs TB</div>
</div>""", unsafe_allow_html=True)

    # Bảng so sánh tất cả stores cùng phân khúc
    st.markdown("---")
    st.markdown("**Chi Tiết Từng Cửa Hàng Phân Khúc:**")
    rows = []
    for s in same_segment:
        snap = db.get_snapshot(s["id"], date_str)
        if snap:
            rows.append({
                "Cửa hàng": s["name"],
                "Thành phố": s["city"],
                "DT (M đ)": f"{snap['revenue']/1e6:.1f}",
                "% Target": f"{snap.get('target_pct',0)*100:.1f}%",
                "CR": f"{snap.get('conversion_rate',0)*100:.1f}%",
                "Traffic": snap.get("traffic", 0),
                "AOV (M đ)": f"{snap.get('aov',0)/1e6:.2f}",
                "Store hiện tại": "✅" if s["id"] == store_id else "",
            })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Revenue comparison chart
    if rows:
        st.markdown("**So Sánh Doanh Thu:**")
        store_names = [r["Cửa hàng"].split()[-2] + " " + r["Cửa hàng"].split()[-1] for r in rows]
        revenues = [float(r["DT (M đ)"]) for r in rows]
        colors = ["#e8c84a" if r["Store hiện tại"] else "#667eea" for r in rows]

        fig_cmp = go.Figure(go.Bar(
            x=store_names,
            y=revenues,
            marker_color=colors,
            text=[f"{v:.0f}M" for v in revenues],
            textposition="outside",
        ))
        fig_cmp.update_layout(
            paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
            font_color="#e2e8f0", height=280,
            xaxis={"gridcolor": "#2d3250", "tickangle": -20},
            yaxis={"gridcolor": "#2d3250", "title": "Triệu đồng"},
            margin=dict(l=10, r=10, t=20, b=60),
        )
        st.plotly_chart(fig_cmp, use_container_width=True)
        st.caption("🟡 Vàng = cửa hàng đang xem | 🟣 Tím = cửa hàng cùng phân khúc")
