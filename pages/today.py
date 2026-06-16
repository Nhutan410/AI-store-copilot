"""
Trang Trong hôm nay: tổng kết đơn hàng đúng ngày thực tế hiện tại.
Không dùng ngày mới nhất trong dataset để thay thế khi hôm nay chưa có dữ liệu.
"""
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from engine import db


CATEGORY_NAMES = {
    "wedding_ring": "Nhẫn cưới",
    "engagement_ring": "Nhẫn đính hôn",
    "fashion_ring": "Nhẫn thời trang",
    "bracelet": "Lắc tay",
    "necklace": "Dây chuyền",
    "earring": "Bông tai",
    "watch": "Đồng hồ",
    "accessory": "Phụ kiện",
}

SHIFT_NAMES = {
    "morning": "Ca sáng",
    "afternoon": "Ca chiều",
    "evening": "Ca tối",
}


def _format_date(date_str: str) -> str:
    return date.fromisoformat(date_str).strftime("%d/%m/%Y")


def _summarize_today(snapshot: dict | None, transactions: list[dict]) -> dict:
    revenue = sum(t.get("actual_price", 0) for t in transactions)
    orders = len(transactions)

    if snapshot and not transactions:
        revenue = snapshot.get("revenue", revenue)
        orders = snapshot.get("num_transactions", orders)

    traffic = snapshot.get("traffic", 0) if snapshot else 0
    conversion_rate = snapshot.get("conversion_rate", 0) if snapshot else 0
    aov = revenue / orders if orders else 0

    return {
        "orders": orders,
        "revenue": revenue,
        "traffic": traffic,
        "conversion_rate": conversion_rate,
        "aov": aov,
    }


def _render_metric_card(label: str, value: str, detail: str = ""):
    st.markdown(
        f"""
<div class="metric-card">
  <div class="metric-label">{label}</div>
  <div class="metric-value">{value}</div>
  <div style="font-size:0.82rem;color:#8b92a5">{detail}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_hourly_chart(transactions: list[dict]):
    hourly = {}
    for txn in transactions:
        hour = txn.get("hour")
        if hour is None:
            timestamp = txn.get("timestamp", "")
            try:
                hour = int(timestamp[11:13])
            except (TypeError, ValueError):
                continue

        bucket = hourly.setdefault(hour, {"orders": 0, "revenue": 0})
        bucket["orders"] += 1
        bucket["revenue"] += txn.get("actual_price", 0)

    hours = list(range(9, 22))
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[f"{hour:02d}:00" for hour in hours],
            y=[hourly.get(hour, {}).get("orders", 0) for hour in hours],
            name="Số đơn",
            marker_color="#e8c84a",
            hovertemplate="%{x}<br>%{y} đơn<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[f"{hour:02d}:00" for hour in hours],
            y=[hourly.get(hour, {}).get("revenue", 0) / 1e6 for hour in hours],
            name="Doanh thu",
            mode="lines+markers",
            line={"color": "#4ecca3", "width": 3},
            marker={"size": 7},
            yaxis="y2",
            hovertemplate="%{x}<br>%{y:.2f}M đ<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor="#1e2130",
        plot_bgcolor="#1e2130",
        font_color="#e2e8f0",
        height=330,
        xaxis={"gridcolor": "#2d3250", "title": "Khung giờ"},
        yaxis={"gridcolor": "#2d3250", "title": "Số đơn", "rangemode": "tozero"},
        yaxis2={
            "title": "Doanh thu (triệu đồng)",
            "overlaying": "y",
            "side": "right",
            "rangemode": "tozero",
            "showgrid": False,
        },
        legend={"bgcolor": "#1e2130", "orientation": "h", "y": 1.12},
        margin=dict(l=10, r=10, t=45, b=10),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_category_chart(transactions: list[dict]):
    category_revenue = {}
    for txn in transactions:
        category = txn.get("category", "other")
        category_revenue[category] = (
            category_revenue.get(category, 0) + txn.get("actual_price", 0)
        )

    labels = [CATEGORY_NAMES.get(key, key) for key in category_revenue]
    values = list(category_revenue.values())
    colors = [
        "#e8c84a",
        "#f7a948",
        "#4ecca3",
        "#667eea",
        "#6bcb77",
        "#ff6b6b",
        "#c77dff",
        "#48cae4",
    ]
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker_colors=colors[:len(labels)],
            textinfo="percent",
            hovertemplate="%{label}<br>%{value:,.0f} đ<br>%{percent}<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor="#1e2130",
        font_color="#e2e8f0",
        height=330,
        legend={"bgcolor": "#1e2130", "font": {"size": 11}},
        margin=dict(l=0, r=0, t=15, b=15),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_order_table(transactions: list[dict], store_id: str):
    staff_map = {
        member["id"]: member.get("name", member["id"])
        for member in db.get_staff(store_id)
    }
    sku_map = {
        sku["id"]: sku.get("name", sku["id"])
        for sku in db.get_skus_with_inventory(store_id)
    }

    rows = []
    for txn in sorted(
        transactions,
        key=lambda item: item.get("timestamp", ""),
        reverse=True,
    ):
        rows.append(
            {
                "Mã đơn": txn.get("id", ""),
                "Thời gian": txn.get("timestamp", "")[11:19],
                "Sản phẩm": sku_map.get(txn.get("sku_id"), txn.get("sku_id", "")),
                "Danh mục": CATEGORY_NAMES.get(
                    txn.get("category"), txn.get("category", "")
                ),
                "Doanh thu": txn.get("actual_price", 0),
                "Nhân viên": staff_map.get(
                    txn.get("staff_id"), txn.get("staff_id", "")
                ),
                "Ca": SHIFT_NAMES.get(txn.get("shift"), txn.get("shift", "")),
            }
        )

    frame = pd.DataFrame(rows)
    st.dataframe(
        frame,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Doanh thu": st.column_config.NumberColumn(
                "Doanh thu",
                format="%d đ",
            ),
        },
    )


def render(store_id: str):
    today = date.today().isoformat()
    today_label = _format_date(today)
    store = db.get_store(store_id)

    st.markdown("## 📅 Trong hôm nay")
    st.caption(
        f"Tổng kết đơn hàng ngày {today_label}. "
        "Trang này chỉ đọc dữ liệu trùng chính xác với ngày hiện tại."
    )

    if not store:
        st.error("Không tìm thấy cửa hàng.")
        return

    snapshot = db.get_snapshot(store_id, today)
    transactions = db.get_transactions(store_id, date_str=today)
    has_today_data = snapshot is not None or bool(transactions)

    if not has_today_data:
        latest = db.get_latest_data_date(store_id)
        latest_note = (
            f" Ngày cuối trong dataset là {_format_date(latest)}, "
            "nhưng hệ thống không dùng ngày này để thay thế."
            if latest
            else ""
        )
        st.info(
            f"Chưa có dữ liệu đơn hàng của ngày hôm nay ({today_label}) "
            f"cho {store['name']}.{latest_note}"
        )
        return

    summary = _summarize_today(snapshot, transactions)
    target = store.get("daily_target", 0)
    target_pct = summary["revenue"] / target * 100 if target else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        _render_metric_card(
            "Tổng đơn hôm nay",
            f"{summary['orders']:,}",
            "Đơn hàng đúng ngày hiện tại",
        )
    with col2:
        _render_metric_card(
            "Doanh thu",
            f"{summary['revenue']/1e6:.2f}M đ",
            f"{target_pct:.1f}% target ngày",
        )
    with col3:
        _render_metric_card(
            "AOV",
            f"{summary['aov']/1e6:.2f}M đ",
            "Giá trị trung bình mỗi đơn",
        )
    with col4:
        _render_metric_card(
            "Traffic",
            f"{summary['traffic']:,}",
            "Lượt khách vào cửa hàng",
        )
    with col5:
        _render_metric_card(
            "Tỷ lệ chuyển đổi",
            f"{summary['conversion_rate']*100:.1f}%",
            "Số đơn / traffic",
        )

    st.markdown("---")

    if not transactions:
        st.info(
            f"Đã có bản ghi ngày {today_label}, nhưng hiện chưa phát sinh đơn hàng. "
            "Biểu đồ và bảng chi tiết sẽ xuất hiện khi có giao dịch."
        )
        return

    col_hourly, col_category = st.columns([3, 2])
    with col_hourly:
        st.markdown("### Đơn hàng và doanh thu theo giờ")
        _render_hourly_chart(transactions)
    with col_category:
        st.markdown("### Cơ cấu doanh thu")
        _render_category_chart(transactions)

    st.markdown("### Chi tiết đơn hàng hôm nay")
    _render_order_table(transactions, store_id)
