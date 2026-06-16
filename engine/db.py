"""
CRUD operations cho JSON-based database.
"""
import json
import os
from datetime import date, datetime
from typing import Any

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _path(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)


def _load(filename: str, default=None) -> Any:
    p = _path(filename)
    if not os.path.exists(p):
        return default if default is not None else []
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(filename: str, data: Any):
    p = _path(filename)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─── Reads ───────────────────────────────────────────────────────────────────

def get_stores() -> list:
    return _load("stores.json", [])


def get_store(store_id: str) -> dict | None:
    return next((s for s in get_stores() if s["id"] == store_id), None)


def get_staff(store_id: str | None = None) -> list:
    staff = _load("staff.json", [])
    if store_id:
        return [s for s in staff if s["store_id"] == store_id]
    return staff


def get_staff_member(staff_id: str) -> dict | None:
    return next((s for s in _load("staff.json", []) if s["id"] == staff_id), None)


def get_skus(segment: str | None = None) -> list:
    skus = _load("skus.json", [])
    if segment:
        return [s for s in skus if segment in s.get("segments", [])]
    return skus


# ─── Store Inventory (per-store per-SKU) ─────────────────────────────────────

def get_store_inventory(store_id: str) -> dict:
    """Trả về {sku_id: record} cho store. Đã bao gồm stock, display_position, cvr_local."""
    inv = _load("store_inventory.json", [])
    return {r["sku_id"]: r for r in inv if r["store_id"] == store_id}


def get_skus_with_inventory(store_id: str) -> list:
    """Merge catalog SKU + per-store inventory. Kết quả có stock và cvr_local thực tế."""
    store = get_store(store_id)
    segment = store["segment"] if store else "A"
    catalog = [s for s in _load("skus.json", []) if segment in s.get("segments", [])]
    inventory = get_store_inventory(store_id)
    result = []
    for sku in catalog:
        inv = inventory.get(sku["id"], {})
        result.append({
            **sku,
            "stock": inv.get("stock", 0),
            "display_position": inv.get("display_position", "standard"),
            "cvr_local": inv.get("cvr_local", sku["cvr_history"]),
            "last_sold_date": inv.get("last_sold_date"),
        })
    return result


def update_sku_stock(store_id: str, sku_id: str, delta: int,
                     sold_date: str | None = None):
    """Điều chỉnh stock. delta âm = bán ra, dương = nhập hàng."""
    from datetime import date as _date
    inv = _load("store_inventory.json", [])
    for rec in inv:
        if rec["store_id"] == store_id and rec["sku_id"] == sku_id:
            if rec["stock"] != 9999:  # PK-002 dịch vụ không giới hạn
                rec["stock"] = max(0, rec["stock"] + delta)
            if delta < 0:
                rec["last_sold_date"] = sold_date or _date.today().isoformat()
            break
    _save("store_inventory.json", inv)


def bulk_update_inventory_after_sales(store_id: str, txns: list):
    """Trừ tồn kho hàng loạt sau khi simulate xong một ngày."""
    from collections import Counter
    sold_counts = Counter(t["sku_id"] for t in txns)
    inv = _load("store_inventory.json", [])
    sold_date = txns[0]["date"] if txns else None
    for rec in inv:
        if rec["store_id"] != store_id:
            continue
        count = sold_counts.get(rec["sku_id"], 0)
        if count > 0 and rec["stock"] != 9999:
            rec["stock"] = max(0, rec["stock"] - count)
            rec["last_sold_date"] = sold_date
    _save("store_inventory.json", inv)


def restore_inventory_before_regeneration(store_id: str, txns: list):
    """Hoàn lại tồn của các giao dịch sắp bị xóa khi regenerate cùng ngày."""
    from collections import Counter

    sold_counts = Counter(
        t["sku_id"] for t in txns
        if t.get("store_id") == store_id
    )
    if not sold_counts:
        return

    inv = _load("store_inventory.json", [])
    for rec in inv:
        if rec["store_id"] != store_id or rec["stock"] == 9999:
            continue
        count = sold_counts.get(rec["sku_id"], 0)
        if count > 0:
            rec["stock"] += count
    _save("store_inventory.json", inv)


def replenish_inventory_for_simulation(store_id: str,
                                       minimum_available_ratio: float = 0.6) -> int:
    """
    Nhập bù khi kho mô phỏng đã cạn quá mức.

    Chỉ kích hoạt khi số SKU hữu hạn còn hàng thấp hơn tỷ lệ tối thiểu. Mức nhập
    bù nhỏ hơn tồn kho seed ban đầu để giữ ý nghĩa của cảnh báo tồn kho.
    """
    store = get_store(store_id)
    if not store:
        return 0

    segment = store.get("segment", "A")
    catalog = {
        sku["id"]: sku
        for sku in _load("skus.json", [])
        if segment in sku.get("segments", [])
    }
    inv = _load("store_inventory.json", [])
    store_rows = [
        rec for rec in inv
        if rec["store_id"] == store_id
        and rec["sku_id"] in catalog
        and rec["stock"] != 9999
    ]
    if not store_rows:
        return 0

    available_count = sum(rec.get("stock", 0) > 0 for rec in store_rows)
    if available_count / len(store_rows) >= minimum_available_ratio:
        return 0

    replenished = 0
    for rec in store_rows:
        if rec.get("stock", 0) > 0:
            continue

        price = catalog[rec["sku_id"]].get("price", 0)
        if price >= 10_000_000:
            restock_level = 2
        elif price >= 5_000_000:
            restock_level = 3
        elif price >= 2_000_000:
            restock_level = 5
        else:
            restock_level = 8

        rec["stock"] = restock_level
        replenished += 1

    if replenished:
        _save("store_inventory.json", inv)
    return replenished


def get_rules() -> list:
    return _load("rules.json", [])


def get_action_registry() -> list:
    return _load("action_registry.json", [])


def get_transactions(store_id: str, date_str: str | None = None,
                     days: int = 30) -> list:
    txns = _load("transactions.json", [])
    result = [t for t in txns if t["store_id"] == store_id]
    if date_str:
        result = [t for t in result if t["date"] == date_str]
    elif days:
        cutoff = _cutoff_date(days)
        result = [t for t in result if t["date"] >= cutoff]
    return result


def append_transactions(new_txns: list):
    """Thêm giao dịch mới vào transactions.json mà không xóa lịch sử."""
    txns = _load("transactions.json", [])
    txns.extend(new_txns)
    _save("transactions.json", txns)


def append_snapshot(snapshot: dict):
    """Thêm hoặc cập nhật snapshot cho ngày/store."""
    snaps = _load("snapshots.json", [])
    key = (snapshot["store_id"], snapshot["date"])
    snaps = [s for s in snaps if (s["store_id"], s["date"]) != key]
    snaps.append(snapshot)
    _save("snapshots.json", snaps)


def append_roster(roster: dict):
    """Thêm hoặc cập nhật roster cho ngày/store."""
    roster_data = _load("roster.json", [])
    key = (roster["store_id"], roster["date"])
    roster_data = [r for r in roster_data if (r["store_id"], r["date"]) != key]
    roster_data.append(roster)
    _save("roster.json", roster_data)


def get_latest_data_date(store_id: str) -> str | None:
    """Trả về ngày mới nhất có snapshot trong DB. None nếu chưa có data."""
    snaps = _load("snapshots.json", [])
    store_snaps = [s["date"] for s in snaps if s["store_id"] == store_id]
    return max(store_snaps) if store_snaps else None


def count_transactions_total() -> int:
    txns = _load("transactions.json", [])
    return len(txns)


def get_snapshot(store_id: str, date_str: str) -> dict | None:
    snaps = _load("snapshots.json", [])
    return next((s for s in snaps
                 if s["store_id"] == store_id and s["date"] == date_str), None)


def get_snapshots(store_id: str, days: int = 30) -> list:
    snaps = _load("snapshots.json", [])
    cutoff = _cutoff_date(days)
    result = [s for s in snaps
              if s["store_id"] == store_id and s["date"] >= cutoff]
    return sorted(result, key=lambda x: x["date"])


def get_roster(store_id: str, date_str: str) -> dict | None:
    roster = _load("roster.json", [])
    return next((r for r in roster
                 if r["store_id"] == store_id and r["date"] == date_str), None)


def get_roster_range(store_id: str, days: int = 30) -> list:
    roster = _load("roster.json", [])
    cutoff = _cutoff_date(days)
    return [r for r in roster
            if r["store_id"] == store_id and r["date"] >= cutoff]


# ─── Chat History ────────────────────────────────────────────────────────────

def get_chat_history(store_id: str) -> list:
    hist = _load("chat_history.json", {})
    return hist.get(store_id, [])


def append_chat(store_id: str, role: str, content: str):
    hist = _load("chat_history.json", {})
    if store_id not in hist:
        hist[store_id] = []
    hist[store_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    _save("chat_history.json", hist)


def clear_chat(store_id: str):
    hist = _load("chat_history.json", {})
    hist[store_id] = []
    _save("chat_history.json", hist)


# ─── Notifications ───────────────────────────────────────────────────────────

def get_notifications(store_id: str | None = None) -> list:
    notifs = _load("notifications.json", [])
    if store_id:
        notifs = [n for n in notifs if n.get("store_id") == store_id]
    return sorted(notifs, key=lambda x: x.get("created_at", ""), reverse=True)


def add_notification(store_id: str, title: str, body: str,
                     notif_type: str = "tip", urgency: str = "MEDIUM"):
    notifs = _load("notifications.json", [])
    notifs.append({
        "id": f"NOTIF-{len(notifs)+1:04d}",
        "store_id": store_id,
        "title": title,
        "body": body,
        "type": notif_type,
        "urgency": urgency,
        "read": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    _save("notifications.json", notifs)


def mark_notification_read(notif_id: str):
    notifs = _load("notifications.json", [])
    for n in notifs:
        if n["id"] == notif_id:
            n["read"] = True
    _save("notifications.json", notifs)


# ─── Action Feedback ─────────────────────────────────────────────────────────

# Metric cần theo dõi sau khi CHT áp dụng mỗi rule
_RULE_OUTCOME_METRICS = {
    "RULE-01": "wedding_pct",
    "RULE-02": "conversion_rate",
    "RULE-03": "target_pct",
    "RULE-04": "target_pct",
    "RULE-05": "target_pct",
    "RULE-06": "wedding_pct",
    "RULE-07": "conversion_rate",
    "RULE-08": "target_pct",
    "RULE-09": "target_pct",
    "RULE-10": "traffic",
    "RULE-11": "aov",
    "RULE-12": "conversion_rate",
}


def _extract_outcome_metric(rule_id: str, snap: dict) -> float | None:
    key = _RULE_OUTCOME_METRICS.get(rule_id)
    if not key or not snap:
        return None
    if key == "wedding_pct":
        revenue = snap.get("revenue", 0)
        if not revenue:
            return None
        cat = snap.get("category_revenue", {})
        wedding = cat.get("wedding_ring", 0) + cat.get("engagement_ring", 0)
        return wedding / revenue
    return snap.get(key)


def get_action_feedback(store_id: str | None = None) -> list:
    fb = _load("action_feedback.json", [])
    if store_id:
        fb = [f for f in fb if f.get("store_id") == store_id]
    return fb


def save_action_feedback(store_id: str, rule_id: str, action_id: str,
                          decision: str, snapshot_before: dict | None = None):
    fb = _load("action_feedback.json", [])
    fb.append({
        "id": f"FB-{len(fb)+1:04d}",
        "store_id": store_id,
        "rule_id": rule_id,
        "action_id": action_id,
        "decision": decision,  # "accept" | "skip"
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "snapshot_before": snapshot_before,
        "outcome": None,  # Điền sau khi có snapshot ngày hôm sau
    })
    _save("action_feedback.json", fb)
    # Skip không thay đổi confidence — không có dữ liệu thì không phán xét.
    # Accept cũng chưa thay đổi ngay — chờ evaluate_pending_outcomes() kiểm tra kết quả.


def evaluate_pending_outcomes(store_id: str):
    """Kiểm tra outcome của các action đã Accept nhưng chưa có kết quả.

    So sánh metric liên quan của ngày hôm sau với ngày trước khi áp dụng.
    Nếu metric tốt hơn → positive → confidence tăng.
    Nếu không → negative → confidence giảm.
    Skip không được tính vào đây.
    """
    from datetime import date as _date, timedelta
    fb_list = _load("action_feedback.json", [])
    snapshots = _load("snapshots.json", [])
    snap_map = {(s["store_id"], s["date"]): s for s in snapshots}

    changed = False
    for fb in fb_list:
        if fb.get("store_id") != store_id:
            continue
        if fb.get("decision") != "accept":
            continue
        if fb.get("outcome") is not None:
            continue

        ts = fb.get("timestamp", "")
        if not ts:
            continue
        fb_date = ts[:10]
        try:
            next_date = (_date.fromisoformat(fb_date) + timedelta(days=1)).isoformat()
        except ValueError:
            continue

        snap_after = snap_map.get((store_id, next_date))
        if snap_after is None:
            continue  # Snapshot ngày hôm sau chưa có, chờ tiếp

        metric_before = _extract_outcome_metric(fb["rule_id"], fb.get("snapshot_before") or {})
        metric_after = _extract_outcome_metric(fb["rule_id"], snap_after)

        if metric_before is None or metric_after is None:
            continue

        fb["outcome"] = "positive" if metric_after > metric_before else "negative"
        changed = True
        _update_rule_confidence(fb["rule_id"], fb["outcome"])

    if changed:
        _save("action_feedback.json", fb_list)


def _update_rule_confidence(rule_id: str, outcome: str):
    """Cập nhật confidence dựa trên kết quả thực tế (positive/negative).

    Chỉ được gọi sau khi có outcome — không gọi từ save_action_feedback.
    confidence = 0.70 + (positive_outcomes / total_outcomes) * 0.25
    """
    rules = _load("rules.json", [])
    for r in rules:
        if r["id"] == rule_id:
            r["outcome_count"] = r.get("outcome_count", 0) + 1
            if outcome == "positive":
                r["positive_outcomes"] = r.get("positive_outcomes", 0) + 1
            else:
                r["negative_outcomes"] = r.get("negative_outcomes", 0) + 1
            total = r["outcome_count"]
            pos = r.get("positive_outcomes", 0)
            r["confidence"] = round(min(0.95, 0.70 + (pos / total) * 0.25), 3) if total > 0 else 0.70
    _save("rules.json", rules)


# ─── Utils ───────────────────────────────────────────────────────────────────

def _cutoff_date(days: int) -> str:
    from datetime import date, timedelta
    return (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")


def today_str() -> str:
    from datetime import date
    return date.today().isoformat()


def yesterday_str() -> str:
    from datetime import date, timedelta
    return (date.today() - timedelta(days=1)).isoformat()


def get_store_id_from_ctx() -> str | None:
    """Placeholder — được patch bởi rule_engine khi evaluate."""
    return None
