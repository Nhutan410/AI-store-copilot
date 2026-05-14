"""
Tính toán baselines, comparisons, trends và health score.
"""
from collections import defaultdict
from datetime import date, timedelta
from engine import db


def _today() -> date:
    return date.today()


# ─── Baseline ────────────────────────────────────────────────────────────────

def get_baseline(store_id: str, metric: str = "traffic",
                 days: int = 14) -> float:
    snaps = db.get_snapshots(store_id, days)
    if not snaps:
        return 0.0
    values = [s.get(metric, 0) for s in snaps]
    return sum(values) / len(values) if values else 0.0


def get_dow_baseline(store_id: str, day_of_week: str,
                     metric: str = "conversion_rate", weeks: int = 4) -> float:
    """Baseline cùng thứ trong N tuần gần nhất."""
    snaps = db.get_snapshots(store_id, weeks * 7 + 1)
    matched = [s for s in snaps if s.get("day_of_week") == day_of_week]
    if not matched:
        return 0.0
    vals = [s.get(metric, 0) for s in matched]
    return sum(vals) / len(vals)


# ─── Daily Comparison ────────────────────────────────────────────────────────

def compare_to_baseline(store_id: str, date_str: str) -> dict:
    snap = db.get_snapshot(store_id, date_str)
    if not snap:
        return {}
    baseline_traffic = get_baseline(store_id, "traffic", 14)
    baseline_cr = get_baseline(store_id, "conversion_rate", 14)
    baseline_aov = get_baseline(store_id, "aov", 14)
    baseline_rev = get_baseline(store_id, "revenue", 14)

    dow = snap.get("day_of_week", "")
    dow_cr = get_dow_baseline(store_id, dow, "conversion_rate")
    dow_rev = get_dow_baseline(store_id, dow, "revenue")

    return {
        "traffic_ratio": snap["traffic"] / baseline_traffic if baseline_traffic else 1,
        "cr_ratio": snap["conversion_rate"] / baseline_cr if baseline_cr else 1,
        "aov_ratio": snap["aov"] / baseline_aov if baseline_aov else 1,
        "rev_ratio": snap["revenue"] / baseline_rev if baseline_rev else 1,
        "cr_vs_dow": snap["conversion_rate"] / dow_cr if dow_cr else 1,
        "rev_vs_dow": snap["revenue"] / dow_rev if dow_rev else 1,
        "baseline_traffic": baseline_traffic,
        "baseline_cr": baseline_cr,
        "baseline_aov": baseline_aov,
        "baseline_rev": baseline_rev,
    }


# ─── Health Score ─────────────────────────────────────────────────────────────

def calc_health_score(store_id: str, date_str: str) -> dict:
    snap = db.get_snapshot(store_id, date_str)
    if not snap:
        return {"score": 50, "grade": "C", "components": {}}

    store = db.get_store(store_id)
    target = store["daily_target"] if store else 92_000_000
    cmp = compare_to_baseline(store_id, date_str)

    # Revenue vs target (40 pts)
    rev_pct = snap.get("target_pct", 0)
    rev_score = min(40, rev_pct * 40)

    # CR vs baseline (25 pts)
    cr_ratio = cmp.get("cr_ratio", 1)
    cr_score = min(25, cr_ratio * 25)

    # Traffic vs baseline (15 pts)
    tr_ratio = cmp.get("traffic_ratio", 1)
    tr_score = min(15, tr_ratio * 15)

    # Category mix — wedding/engagement (10 pts)
    cat_rev = snap.get("category_revenue", {})
    total_rev = snap.get("revenue", 1) or 1
    wedding_pct = (cat_rev.get("wedding_ring", 0) + cat_rev.get("engagement_ring", 0)) / total_rev
    mix_score = min(10, (wedding_pct / 0.40) * 10)

    # Staff efficiency (10 pts) — proxy: avg CR from staff perf
    perf = snap.get("staff_performance", {})
    if perf:
        traffic = max(snap.get("traffic", 1), 1)
        total_orders = sum(v["orders"] for v in perf.values())
        implicit_cr = total_orders / traffic
        eff_score = min(10, (implicit_cr / 0.35) * 10)
    else:
        eff_score = 5

    total = rev_score + cr_score + tr_score + mix_score + eff_score

    if total >= 85:
        grade = "A"
    elif total >= 70:
        grade = "B"
    elif total >= 55:
        grade = "C"
    else:
        grade = "D"

    return {
        "score": round(total),
        "grade": grade,
        "components": {
            "Doanh thu vs Target": round(rev_score, 1),
            "Tỷ lệ chuyển đổi": round(cr_score, 1),
            "Lưu lượng khách": round(tr_score, 1),
            "Cơ cấu sản phẩm": round(mix_score, 1),
            "Hiệu suất nhân viên": round(eff_score, 1),
        },
        "details": {
            "revenue_pct": round(rev_pct * 100, 1),
            "cr_ratio": round(cr_ratio * 100, 1),
            "traffic_ratio": round(tr_ratio * 100, 1),
            "wedding_pct": round(wedding_pct * 100, 1),
        }
    }


# ─── Trends 30 ngày ─────────────────────────────────────────────────────────

def get_revenue_trend(store_id: str, days: int = 30) -> list:
    snaps = db.get_snapshots(store_id, days)
    store = db.get_store(store_id)
    target = store["daily_target"] if store else 92_000_000
    return [{
        "date": s["date"],
        "revenue": s["revenue"],
        "target": target,
        "target_pct": s.get("target_pct", 0) * 100,
        "day_of_week_vn": s.get("day_of_week_vn", ""),
    } for s in snaps]


def get_cr_trend(store_id: str, days: int = 30) -> list:
    snaps = db.get_snapshots(store_id, days)
    baseline = get_baseline(store_id, "conversion_rate", days)
    return [{
        "date": s["date"],
        "cr": round(s.get("conversion_rate", 0) * 100, 2),
        "baseline": round(baseline * 100, 2),
        "day_of_week_vn": s.get("day_of_week_vn", ""),
    } for s in snaps]


def get_traffic_trend(store_id: str, days: int = 30) -> list:
    snaps = db.get_snapshots(store_id, days)
    baseline = get_baseline(store_id, "traffic", 14)
    return [{
        "date": s["date"],
        "traffic": s.get("traffic", 0),
        "baseline": round(baseline),
        "day_of_week_vn": s.get("day_of_week_vn", ""),
    } for s in snaps]


def get_category_mix_trend(store_id: str, days: int = 30) -> list:
    snaps = db.get_snapshots(store_id, days)
    result = []
    for s in snaps:
        cat = s.get("category_revenue", {})
        total = s.get("revenue", 1) or 1
        result.append({
            "date": s["date"],
            "wedding_ring": round(cat.get("wedding_ring", 0) / total * 100, 1),
            "engagement_ring": round(cat.get("engagement_ring", 0) / total * 100, 1),
            "fashion_ring": round(cat.get("fashion_ring", 0) / total * 100, 1),
            "bracelet": round(cat.get("bracelet", 0) / total * 100, 1),
            "necklace": round(cat.get("necklace", 0) / total * 100, 1),
            "earring": round(cat.get("earring", 0) / total * 100, 1),
            "watch": round(cat.get("watch", 0) / total * 100, 1),
            "accessory": round(cat.get("accessory", 0) / total * 100, 1),
        })
    return result


def get_staff_performance_summary(store_id: str, days: int = 30) -> list:
    snaps = db.get_snapshots(store_id, days)
    staff_map = {nv["id"]: nv for nv in db.get_staff(store_id)}
    agg: dict = {}
    for s in snaps:
        for sid, perf in s.get("staff_performance", {}).items():
            if sid not in agg:
                nv = staff_map.get(sid, {})
                agg[sid] = {
                    "staff_id": sid,
                    "name": nv.get("name", sid),
                    "level": nv.get("level", ""),
                    "revenue": 0,
                    "orders": 0,
                    "days": 0,
                }
            agg[sid]["revenue"] += perf.get("revenue", 0)
            agg[sid]["orders"] += perf.get("orders", 0)
            agg[sid]["days"] += 1

    result = []
    for sid, v in agg.items():
        nv = staff_map.get(sid, {})
        v["avg_daily_revenue"] = v["revenue"] / v["days"] if v["days"] else 0
        v["avg_orders"] = v["orders"] / v["days"] if v["days"] else 0
        v["avg_cr"] = nv.get("avg_cr", 0)
        result.append(v)
    return sorted(result, key=lambda x: x["revenue"], reverse=True)


# ─── Cross-store Benchmark ────────────────────────────────────────────────────

def get_segment_benchmark(segment: str, date_str: str) -> dict:
    stores = [s for s in db.get_stores() if s["segment"] == segment]
    metrics = defaultdict(list)
    for store in stores:
        snap = db.get_snapshot(store["id"], date_str)
        if snap:
            metrics["target_pct"].append(snap.get("target_pct", 0))
            metrics["conversion_rate"].append(snap.get("conversion_rate", 0))
            metrics["traffic"].append(snap.get("traffic", 0))
            metrics["aov"].append(snap.get("aov", 0))
    return {
        k: round(sum(v) / len(v), 4) if v else 0
        for k, v in metrics.items()
    }


# ─── Predictive Revenue ───────────────────────────────────────────────────────

def predict_eod_revenue(store_id: str, current_revenue: float,
                        current_hour: int) -> float:
    """Linear projection từ pace hiện tại × hệ số giờ cao điểm."""
    # Tỷ lệ doanh thu tích lũy theo giờ (lịch sử)
    hour_weights = {
        9: 0.06, 10: 0.14, 11: 0.23, 12: 0.30,
        13: 0.36, 14: 0.44, 15: 0.53, 16: 0.62,
        17: 0.74, 18: 0.87, 19: 0.97, 20: 0.99, 21: 1.00
    }
    pace_pct = hour_weights.get(current_hour, 0.5)
    if pace_pct <= 0:
        return current_revenue
    return current_revenue / pace_pct


# ─── SKU Opportunity Score ────────────────────────────────────────────────────

def get_sku_opportunity_scores(store_id: str, date_str: str) -> list:
    """
    Tính điểm cơ hội cho từng SKU dựa trên CVR local, margin và tồn kho thực của store.
    Dùng per-store inventory thay vì catalog toàn cầu.
    """
    skus = db.get_skus_with_inventory(store_id)
    txns = db.get_transactions(store_id, days=7)
    sold_skus = {t["sku_id"] for t in txns}

    result = []
    for sku in skus:
        cvr = sku.get("cvr_local", sku.get("cvr_history", 0.4))
        stock = sku.get("stock", 0)
        # Score = CVR local × Margin × stock_factor
        # stock_factor: nếu tồn < 2 → ưu tiên nhập hàng hơn push, giảm score
        stock_factor = min(1.0, stock / 10) if stock < 10 else 1.0
        score = cvr * sku["margin_pct"] * stock_factor

        days_since_sold = None
        last_sold = sku.get("last_sold_date")
        if last_sold:
            try:
                delta = (_today() - date.fromisoformat(last_sold)).days
                days_since_sold = delta
            except (ValueError, TypeError):
                pass

        is_missed = (sku["id"] not in sold_skus and stock > 0)
        is_slow_moving = (stock >= 10 and (days_since_sold or 0) >= 7)

        result.append({
            **sku,
            "opportunity_score": round(score, 4),
            "is_missed_opportunity": is_missed,
            "is_slow_moving": is_slow_moving,
            "sold_7days": sku["id"] in sold_skus,
            "days_since_sold": days_since_sold,
        })
    return sorted(result, key=lambda x: x["opportunity_score"], reverse=True)
