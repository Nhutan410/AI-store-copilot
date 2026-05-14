"""
Script sinh toàn bộ dữ liệu mẫu cho AI Store Copilot POC.
Chạy: python data/seed_data.py
"""
import json
import random
import os
from datetime import datetime, timedelta, date

random.seed(42)
DATA_DIR = os.path.dirname(os.path.abspath(__file__))


# ─── Stores ──────────────────────────────────────────────────────────────────

STORES = [
    {
        "id": "STR-001", "name": "PNJ Vincom Center Bà Triệu", "city": "Hà Nội",
        "segment": "A", "daily_target": 85_000_000,
        "location": "Tầng 1, gần lối vào chính", "area_sqm": 85, "num_counters": 6,
        "customer_profile": "Cặp đôi trẻ, khách văn phòng cao cấp",
        "opened": "2018-03-15"
    },
    {
        "id": "STR-002", "name": "PNJ Parkson Cantavil", "city": "TP.HCM",
        "segment": "A", "daily_target": 92_000_000,
        "location": "Tầng 2, trung tâm khu mua sắm", "area_sqm": 95, "num_counters": 7,
        "customer_profile": "Cặp đôi, nữ độc thân trẻ, gia đình",
        "opened": "2017-09-20"
    },
    {
        "id": "STR-003", "name": "PNJ Lotte Mart Gò Vấp", "city": "TP.HCM",
        "segment": "B", "daily_target": 58_000_000,
        "location": "Tầng G, gần siêu thị", "area_sqm": 65, "num_counters": 4,
        "customer_profile": "Gia đình, nữ độc thân, người mua quà",
        "opened": "2019-05-10"
    },
    {
        "id": "STR-004", "name": "PNJ Aeon Mall Tân Phú", "city": "TP.HCM",
        "segment": "B", "daily_target": 63_000_000,
        "location": "Tầng 1, khu thời trang", "area_sqm": 70, "num_counters": 5,
        "customer_profile": "Gia đình trẻ, cặp đôi, học sinh sinh viên",
        "opened": "2020-01-08"
    },
    {
        "id": "STR-005", "name": "PNJ Vincom Plaza Nha Trang", "city": "Nha Trang",
        "segment": "B", "daily_target": 51_000_000,
        "location": "Tầng 1, cạnh cửa hàng thời trang", "area_sqm": 58, "num_counters": 4,
        "customer_profile": "Du khách, cặp đôi, khách địa phương",
        "opened": "2020-08-12"
    },
    {
        "id": "STR-006", "name": "PNJ Coopmart Đà Nẵng", "city": "Đà Nẵng",
        "segment": "C", "daily_target": 38_000_000,
        "location": "Tầng G, khu trang sức", "area_sqm": 45, "num_counters": 3,
        "customer_profile": "Gia đình, người mua quà, khách phổ thông",
        "opened": "2021-03-22"
    },
    {
        "id": "STR-007", "name": "PNJ BigC Hải Phòng", "city": "Hải Phòng",
        "segment": "C", "daily_target": 34_000_000,
        "location": "Tầng 1, lối vào siêu thị", "area_sqm": 40, "num_counters": 3,
        "customer_profile": "Khách phổ thông, gia đình, người mua quà",
        "opened": "2021-11-05"
    },
    {
        "id": "STR-008", "name": "PNJ Trung tâm Cần Thơ", "city": "Cần Thơ",
        "segment": "C", "daily_target": 41_000_000,
        "location": "Tầng 1, khu trung tâm", "area_sqm": 50, "num_counters": 3,
        "customer_profile": "Gia đình, cặp đôi trẻ, người mua quà",
        "opened": "2022-06-18"
    },
]

# ─── Staff ───────────────────────────────────────────────────────────────────

STAFF = [
    # STR-002 — store chính demo
    {"id": "NV001", "store_id": "STR-002", "name": "Trần Thị Bảo Ngọc", "level": "senior",
     "strong_categories": ["wedding_ring", "engagement_ring"], "experience_years": 5,
     "avg_cr": 0.52, "avg_daily_revenue": 18_500_000, "phone": "0901234001"},
    {"id": "NV002", "store_id": "STR-002", "name": "Lê Hoàng Minh Khôi", "level": "senior",
     "strong_categories": ["watch", "fashion_ring"], "experience_years": 4,
     "avg_cr": 0.48, "avg_daily_revenue": 16_200_000, "phone": "0901234002"},
    {"id": "NV003", "store_id": "STR-002", "name": "Nguyễn Phương Thảo", "level": "mid",
     "strong_categories": ["bracelet", "necklace"], "experience_years": 2,
     "avg_cr": 0.41, "avg_daily_revenue": 11_800_000, "phone": "0901234003"},
    {"id": "NV004", "store_id": "STR-002", "name": "Võ Thanh Tùng", "level": "mid",
     "strong_categories": ["wedding_ring", "earring"], "experience_years": 2.5,
     "avg_cr": 0.39, "avg_daily_revenue": 12_100_000, "phone": "0901234004"},
    {"id": "NV005", "store_id": "STR-002", "name": "Phạm Ngọc Hân", "level": "junior",
     "strong_categories": ["earring", "bracelet"], "experience_years": 0.67,
     "avg_cr": 0.29, "avg_daily_revenue": 7_300_000, "phone": "0901234005"},
    {"id": "NV006", "store_id": "STR-002", "name": "Đỗ Văn Quang", "level": "junior",
     "strong_categories": ["necklace"], "experience_years": 0.42,
     "avg_cr": 0.26, "avg_daily_revenue": 6_800_000, "phone": "0901234006"},
    {"id": "NV007", "store_id": "STR-002", "name": "Huỳnh Thị Thu Hương", "level": "mid",
     "strong_categories": ["wedding_ring", "engagement_ring"], "experience_years": 3,
     "avg_cr": 0.44, "avg_daily_revenue": 13_500_000, "phone": "0901234007"},
    {"id": "NV008", "store_id": "STR-002", "name": "Bùi Minh Đức", "level": "senior",
     "strong_categories": ["watch", "fashion_ring"], "experience_years": 6,
     "avg_cr": 0.50, "avg_daily_revenue": 17_100_000, "phone": "0901234008"},

    # STR-001
    {"id": "NV009", "store_id": "STR-001", "name": "Phan Thị Lan Anh", "level": "senior",
     "strong_categories": ["wedding_ring", "engagement_ring"], "experience_years": 7,
     "avg_cr": 0.55, "avg_daily_revenue": 22_000_000, "phone": "0901234009"},
    {"id": "NV010", "store_id": "STR-001", "name": "Hoàng Đức Việt", "level": "senior",
     "strong_categories": ["watch", "bracelet"], "experience_years": 5,
     "avg_cr": 0.49, "avg_daily_revenue": 17_800_000, "phone": "0901234010"},
    {"id": "NV011", "store_id": "STR-001", "name": "Trịnh Thị Mai Linh", "level": "mid",
     "strong_categories": ["necklace", "earring"], "experience_years": 3,
     "avg_cr": 0.43, "avg_daily_revenue": 13_200_000, "phone": "0901234011"},
    {"id": "NV012", "store_id": "STR-001", "name": "Ngô Văn Hải", "level": "mid",
     "strong_categories": ["fashion_ring"], "experience_years": 2,
     "avg_cr": 0.37, "avg_daily_revenue": 10_900_000, "phone": "0901234012"},
    {"id": "NV013", "store_id": "STR-001", "name": "Đinh Thị Quỳnh Như", "level": "junior",
     "strong_categories": ["earring"], "experience_years": 0.5,
     "avg_cr": 0.27, "avg_daily_revenue": 6_500_000, "phone": "0901234013"},
    {"id": "NV014", "store_id": "STR-001", "name": "Lý Thành Đạt", "level": "mid",
     "strong_categories": ["wedding_ring", "bracelet"], "experience_years": 2,
     "avg_cr": 0.40, "avg_daily_revenue": 11_600_000, "phone": "0901234014"},

    # STR-003
    {"id": "NV015", "store_id": "STR-003", "name": "Cao Thị Mỹ Dung", "level": "senior",
     "strong_categories": ["wedding_ring"], "experience_years": 4,
     "avg_cr": 0.47, "avg_daily_revenue": 14_200_000, "phone": "0901234015"},
    {"id": "NV016", "store_id": "STR-003", "name": "Đặng Văn Phú", "level": "mid",
     "strong_categories": ["necklace", "earring"], "experience_years": 2,
     "avg_cr": 0.38, "avg_daily_revenue": 10_100_000, "phone": "0901234016"},
    {"id": "NV017", "store_id": "STR-003", "name": "Trương Thị Kiều Oanh", "level": "junior",
     "strong_categories": ["bracelet"], "experience_years": 0.58,
     "avg_cr": 0.28, "avg_daily_revenue": 6_200_000, "phone": "0901234017"},
    {"id": "NV018", "store_id": "STR-003", "name": "Võ Anh Khoa", "level": "mid",
     "strong_categories": ["fashion_ring"], "experience_years": 1.5,
     "avg_cr": 0.35, "avg_daily_revenue": 9_800_000, "phone": "0901234018"},

    # STR-004
    {"id": "NV019", "store_id": "STR-004", "name": "Lê Thị Hồng Nhung", "level": "senior",
     "strong_categories": ["wedding_ring", "engagement_ring"], "experience_years": 5,
     "avg_cr": 0.46, "avg_daily_revenue": 15_500_000, "phone": "0901234019"},
    {"id": "NV020", "store_id": "STR-004", "name": "Nguyễn Văn Thắng", "level": "mid",
     "strong_categories": ["bracelet", "necklace"], "experience_years": 2.5,
     "avg_cr": 0.40, "avg_daily_revenue": 11_200_000, "phone": "0901234020"},
    {"id": "NV021", "store_id": "STR-004", "name": "Trần Thị Cẩm Ly", "level": "junior",
     "strong_categories": ["earring"], "experience_years": 0.75,
     "avg_cr": 0.30, "avg_daily_revenue": 7_100_000, "phone": "0901234021"},
    {"id": "NV022", "store_id": "STR-004", "name": "Phạm Tuấn Anh", "level": "mid",
     "strong_categories": ["fashion_ring", "watch"], "experience_years": 2,
     "avg_cr": 0.36, "avg_daily_revenue": 10_300_000, "phone": "0901234022"},

    # STR-005
    {"id": "NV023", "store_id": "STR-005", "name": "Dương Thị Mộng Trinh", "level": "senior",
     "strong_categories": ["wedding_ring", "necklace"], "experience_years": 4.5,
     "avg_cr": 0.45, "avg_daily_revenue": 13_800_000, "phone": "0901234023"},
    {"id": "NV024", "store_id": "STR-005", "name": "Lâm Quốc Huy", "level": "mid",
     "strong_categories": ["bracelet", "earring"], "experience_years": 2,
     "avg_cr": 0.38, "avg_daily_revenue": 9_600_000, "phone": "0901234024"},
    {"id": "NV025", "store_id": "STR-005", "name": "Nguyễn Thị Bích Trâm", "level": "junior",
     "strong_categories": ["fashion_ring"], "experience_years": 0.83,
     "avg_cr": 0.29, "avg_daily_revenue": 6_800_000, "phone": "0901234025"},
    {"id": "NV026", "store_id": "STR-005", "name": "Huỳnh Thanh Bình", "level": "mid",
     "strong_categories": ["necklace", "earring"], "experience_years": 1.5,
     "avg_cr": 0.36, "avg_daily_revenue": 8_900_000, "phone": "0901234026"},

    # STR-006
    {"id": "NV027", "store_id": "STR-006", "name": "Trần Thị Yến Nhi", "level": "senior",
     "strong_categories": ["wedding_ring", "engagement_ring"], "experience_years": 4,
     "avg_cr": 0.44, "avg_daily_revenue": 11_200_000, "phone": "0901234027"},
    {"id": "NV028", "store_id": "STR-006", "name": "Võ Minh Phúc", "level": "mid",
     "strong_categories": ["bracelet", "fashion_ring"], "experience_years": 2,
     "avg_cr": 0.37, "avg_daily_revenue": 8_600_000, "phone": "0901234028"},
    {"id": "NV029", "store_id": "STR-006", "name": "Lê Thị Thanh Hà", "level": "junior",
     "strong_categories": ["earring"], "experience_years": 0.5,
     "avg_cr": 0.26, "avg_daily_revenue": 5_200_000, "phone": "0901234029"},

    # STR-007
    {"id": "NV030", "store_id": "STR-007", "name": "Nguyễn Thị Lan Phương", "level": "senior",
     "strong_categories": ["wedding_ring", "bracelet"], "experience_years": 3.5,
     "avg_cr": 0.43, "avg_daily_revenue": 10_100_000, "phone": "0901234030"},
    {"id": "NV031", "store_id": "STR-007", "name": "Đoàn Văn Long", "level": "mid",
     "strong_categories": ["necklace", "fashion_ring"], "experience_years": 2,
     "avg_cr": 0.35, "avg_daily_revenue": 7_800_000, "phone": "0901234031"},
    {"id": "NV032", "store_id": "STR-007", "name": "Phạm Thị Thu Nga", "level": "junior",
     "strong_categories": ["earring", "bracelet"], "experience_years": 0.67,
     "avg_cr": 0.27, "avg_daily_revenue": 5_600_000, "phone": "0901234032"},

    # STR-008
    {"id": "NV033", "store_id": "STR-008", "name": "Bùi Thị Diễm Châu", "level": "senior",
     "strong_categories": ["wedding_ring", "engagement_ring"], "experience_years": 5,
     "avg_cr": 0.46, "avg_daily_revenue": 12_500_000, "phone": "0901234033"},
    {"id": "NV034", "store_id": "STR-008", "name": "Trần Minh Tuấn", "level": "mid",
     "strong_categories": ["fashion_ring", "bracelet"], "experience_years": 2.5,
     "avg_cr": 0.38, "avg_daily_revenue": 9_200_000, "phone": "0901234034"},
    {"id": "NV035", "store_id": "STR-008", "name": "Lý Thị Mỹ Hạnh", "level": "junior",
     "strong_categories": ["earring", "necklace"], "experience_years": 0.5,
     "avg_cr": 0.28, "avg_daily_revenue": 5_800_000, "phone": "0901234035"},
    {"id": "NV036", "store_id": "STR-008", "name": "Nguyễn Hữu Khang", "level": "mid",
     "strong_categories": ["necklace", "fashion_ring"], "experience_years": 1.5,
     "avg_cr": 0.35, "avg_daily_revenue": 8_100_000, "phone": "0901234036"},
]

# ─── SKUs ────────────────────────────────────────────────────────────────────

SKUS = [
    # NHẪN CƯỚI
    {"id": "NC-218", "name": "Nhẫn cưới vàng 18k đôi Classic", "category": "wedding_ring",
     "price": 8_500_000, "margin_pct": 0.32, "cvr_history": 0.45, "unit": "đôi",
     "segments": ["A", "B", "C"]},
    {"id": "NC-305", "name": "Nhẫn cưới kim cương 0.3ct đôi", "category": "wedding_ring",
     "price": 18_200_000, "margin_pct": 0.38, "cvr_history": 0.38, "unit": "đôi",
     "segments": ["A", "B", "C"]},
    {"id": "NC-401", "name": "Nhẫn cưới bạch kim đôi Premium", "category": "wedding_ring",
     "price": 26_500_000, "margin_pct": 0.42, "cvr_history": 0.28, "unit": "đôi",
     "segments": ["A"]},
    {"id": "NC-156", "name": "Nhẫn cưới vàng 14k đôi Everyday", "category": "wedding_ring",
     "price": 5_800_000, "margin_pct": 0.29, "cvr_history": 0.52, "unit": "đôi",
     "segments": ["A", "B", "C"]},
    {"id": "NC-520", "name": "Nhẫn cưới vàng hồng 18k Rose", "category": "wedding_ring",
     "price": 11_400_000, "margin_pct": 0.35, "cvr_history": 0.41, "unit": "đôi",
     "segments": ["A", "B"]},

    # NHẪN ĐÍNH HÔN
    {"id": "ND-112", "name": "Nhẫn đính hôn kim cương 0.5ct", "category": "engagement_ring",
     "price": 23_800_000, "margin_pct": 0.40, "cvr_history": 0.32, "unit": "chiếc",
     "segments": ["A"]},
    {"id": "ND-089", "name": "Nhẫn đính hôn kim cương 0.3ct Solitaire", "category": "engagement_ring",
     "price": 15_600_000, "margin_pct": 0.36, "cvr_history": 0.39, "unit": "chiếc",
     "segments": ["A", "B"]},
    {"id": "ND-200", "name": "Nhẫn đính hôn vàng trắng đá CZ", "category": "engagement_ring",
     "price": 7_200_000, "margin_pct": 0.28, "cvr_history": 0.48, "unit": "chiếc",
     "segments": ["A", "B", "C"]},

    # NHẪN THỜI TRANG
    {"id": "NT-301", "name": "Nhẫn vàng 14k đính đá sapphire", "category": "fashion_ring",
     "price": 4_800_000, "margin_pct": 0.25, "cvr_history": 0.55, "unit": "chiếc",
     "segments": ["A", "B", "C"]},
    {"id": "NT-145", "name": "Nhẫn bạc sterling đính đá", "category": "fashion_ring",
     "price": 1_200_000, "margin_pct": 0.18, "cvr_history": 0.68, "unit": "chiếc",
     "segments": ["A", "B", "C"]},
    {"id": "NT-267", "name": "Nhẫn vàng 18k hoa cúc", "category": "fashion_ring",
     "price": 3_500_000, "margin_pct": 0.24, "cvr_history": 0.58, "unit": "chiếc",
     "segments": ["A", "B", "C"]},

    # LẮC TAY
    {"id": "LC-201", "name": "Lắc vàng 18k trơn Classic", "category": "bracelet",
     "price": 4_200_000, "margin_pct": 0.27, "cvr_history": 0.58, "unit": "chiếc",
     "segments": ["A", "B", "C"]},
    {"id": "LC-388", "name": "Lắc vàng 14k đính đá nhiều màu", "category": "bracelet",
     "price": 6_100_000, "margin_pct": 0.29, "cvr_history": 0.50, "unit": "chiếc",
     "segments": ["A", "B"]},
    {"id": "LC-102", "name": "Lắc bạc sterling charm", "category": "bracelet",
     "price": 980_000, "margin_pct": 0.16, "cvr_history": 0.72, "unit": "chiếc",
     "segments": ["A", "B", "C"]},
    {"id": "LC-450", "name": "Lắc vàng hồng 18k dạng xích", "category": "bracelet",
     "price": 5_500_000, "margin_pct": 0.28, "cvr_history": 0.49, "unit": "chiếc",
     "segments": ["A", "B"]},

    # DÂY CHUYỀN
    {"id": "DC-105", "name": "Dây chuyền vàng trắng 18k mặt kim cương", "category": "necklace",
     "price": 9_800_000, "margin_pct": 0.33, "cvr_history": 0.43, "unit": "chiếc",
     "segments": ["A"]},
    {"id": "DC-218", "name": "Dây chuyền vàng 14k mặt tròn", "category": "necklace",
     "price": 3_600_000, "margin_pct": 0.24, "cvr_history": 0.62, "unit": "chiếc",
     "segments": ["A", "B", "C"]},
    {"id": "DC-076", "name": "Dây chuyền bạc sterling đính đá", "category": "necklace",
     "price": 1_450_000, "margin_pct": 0.17, "cvr_history": 0.70, "unit": "chiếc",
     "segments": ["A", "B", "C"]},
    {"id": "DC-330", "name": "Dây chuyền vàng 18k herringbone", "category": "necklace",
     "price": 7_200_000, "margin_pct": 0.30, "cvr_history": 0.48, "unit": "chiếc",
     "segments": ["A", "B"]},

    # BÔNG TAI
    {"id": "BT-088", "name": "Bông tai kim cương 0.2ct stud", "category": "earring",
     "price": 8_900_000, "margin_pct": 0.35, "cvr_history": 0.47, "unit": "đôi",
     "segments": ["A", "B"]},
    {"id": "BT-201", "name": "Bông tai vàng 18k drop", "category": "earring",
     "price": 4_100_000, "margin_pct": 0.26, "cvr_history": 0.60, "unit": "đôi",
     "segments": ["A", "B", "C"]},
    {"id": "BT-055", "name": "Bông tai bạc sterling hoa", "category": "earring",
     "price": 680_000, "margin_pct": 0.15, "cvr_history": 0.75, "unit": "đôi",
     "segments": ["A", "B", "C"]},
    {"id": "BT-312", "name": "Bông tai vàng 14k ngọc trai", "category": "earring",
     "price": 3_200_000, "margin_pct": 0.27, "cvr_history": 0.58, "unit": "đôi",
     "segments": ["A", "B", "C"]},

    # ĐỒNG HỒ
    {"id": "DH-Longines-L45", "name": "Longines L4.5 nam", "category": "watch",
     "price": 18_500_000, "margin_pct": 0.20, "cvr_history": 0.28, "unit": "chiếc",
     "segments": ["A"]},
    {"id": "DH-Tissot-T01", "name": "Tissot T-Classic nữ", "category": "watch",
     "price": 12_200_000, "margin_pct": 0.18, "cvr_history": 0.32, "unit": "chiếc",
     "segments": ["A"]},
    {"id": "DH-Citizen-BM", "name": "Citizen BM8180 nam", "category": "watch",
     "price": 5_800_000, "margin_pct": 0.15, "cvr_history": 0.41, "unit": "chiếc",
     "segments": ["A"]},

    # PHỤ KIỆN
    {"id": "PK-001", "name": "Hộp đựng trang sức cao cấp", "category": "accessory",
     "price": 380_000, "margin_pct": 0.45, "cvr_history": 0.82, "unit": "cái",
     "segments": ["A", "B", "C"]},
    {"id": "PK-002", "name": "Dịch vụ đánh bóng vệ sinh trang sức", "category": "accessory",
     "price": 150_000, "margin_pct": 0.90, "cvr_history": 0.40, "unit": "lần",
     "segments": ["A", "B", "C"]},
]

# ─── Store Inventory Profiles ─────────────────────────────────────────────────
# Đặc thù từng cửa hàng ảnh hưởng đến tồn kho và CVR local

STORE_INV_PROFILES = {
    "STR-001": {  # Vincom Hà Nội — cặp đôi trẻ, văn phòng cao cấp, khẩu vị thận trọng
        "stock_mult": 1.0,
        "cvr_adj": {"wedding_ring": +0.05, "engagement_ring": +0.04, "watch": +0.03,
                    "fashion_ring": -0.07, "bracelet": -0.03, "necklace": +0.01},
        "front_cats": ["wedding_ring", "engagement_ring", "watch"],
        "vault_skus": ["DH-Longines-L45", "NC-401"],
        # LC-388 và DC-330 để tồn cao nhưng ít bán → test RULE-08
        "slow_skus": ["LC-388", "DC-330"],
    },
    "STR-002": {  # Parkson Cantavil HCM — trendy, cặp đôi + nữ trẻ (store demo chính)
        "stock_mult": 1.2,
        "cvr_adj": {"fashion_ring": +0.07, "bracelet": +0.06, "wedding_ring": +0.03,
                    "necklace": +0.04, "engagement_ring": +0.02, "earring": +0.03},
        "front_cats": ["wedding_ring", "fashion_ring", "bracelet"],
        "vault_skus": ["DH-Longines-L45", "NC-401", "ND-112"],
        # LC-450 và DC-105 slow để test rule engine
        "slow_skus": ["LC-450", "DC-105"],
    },
    "STR-003": {  # Lotte Gò Vấp HCM — gia đình, nữ độc thân, quà tặng
        "stock_mult": 0.8,
        "cvr_adj": {"earring": +0.08, "accessory": +0.09, "fashion_ring": +0.05,
                    "bracelet": +0.04, "wedding_ring": -0.07, "engagement_ring": -0.05},
        "front_cats": ["earring", "bracelet", "fashion_ring", "accessory"],
        "vault_skus": [],
        "slow_skus": ["NC-305", "ND-089"],  # high-end ít bán ở Seg B
    },
    "STR-004": {  # Aeon Tân Phú HCM — gia đình trẻ, học sinh sinh viên
        "stock_mult": 0.9,
        "cvr_adj": {"fashion_ring": +0.09, "bracelet": +0.06, "earring": +0.05,
                    "accessory": +0.07, "wedding_ring": -0.05, "necklace": +0.02},
        "front_cats": ["fashion_ring", "bracelet", "earring"],
        "vault_skus": [],
        "slow_skus": ["ND-089", "LC-450"],
    },
    "STR-005": {  # Vincom Nha Trang — du khách, cặp đôi, địa phương
        "stock_mult": 0.85,
        "cvr_adj": {"accessory": +0.11, "necklace": +0.07, "bracelet": +0.05,
                    "earring": +0.06, "fashion_ring": +0.03, "wedding_ring": +0.00},
        "front_cats": ["necklace", "bracelet", "accessory", "earring"],
        "vault_skus": ["DH-Longines-L45"],
        "slow_skus": ["NC-305", "DC-330"],  # ít phù hợp tourist
    },
    "STR-006": {  # CoopMart Đà Nẵng — gia đình, quà tặng, phổ thông
        "stock_mult": 0.70,
        "cvr_adj": {"accessory": +0.13, "earring": +0.09, "fashion_ring": +0.06,
                    "bracelet": +0.05, "necklace": +0.04, "wedding_ring": -0.06},
        "front_cats": ["earring", "accessory", "fashion_ring", "bracelet"],
        "vault_skus": [],
        "slow_skus": ["NC-305", "ND-089", "LC-388"],
    },
    "STR-007": {  # BigC Hải Phòng — phổ thông, gia đình, quà tặng
        "stock_mult": 0.65,
        "cvr_adj": {"accessory": +0.11, "earring": +0.08, "fashion_ring": +0.05,
                    "bracelet": +0.04, "necklace": +0.03, "wedding_ring": -0.05},
        "front_cats": ["earring", "accessory", "bracelet"],
        "vault_skus": [],
        "slow_skus": ["NC-305", "DC-105", "LC-388"],
    },
    "STR-008": {  # CT Cần Thơ — gia đình, cặp đôi trẻ, quà tặng
        "stock_mult": 0.75,
        "cvr_adj": {"accessory": +0.10, "earring": +0.07, "bracelet": +0.05,
                    "necklace": +0.04, "wedding_ring": +0.01, "fashion_ring": +0.03},
        "front_cats": ["earring", "bracelet", "necklace", "accessory"],
        "vault_skus": [],
        "slow_skus": ["NC-305", "ND-089", "DC-330"],
    },
}

# Base stock cho từng SKU (tham chiếu khi generate inventory)
SKU_BASE_STOCK = {
    "NC-218": 12, "NC-305": 8, "NC-401": 5, "NC-156": 18, "NC-520": 9,
    "ND-112": 6,  "ND-089": 10, "ND-200": 14,
    "NT-301": 20, "NT-145": 35, "NT-267": 22,
    "LC-201": 15, "LC-388": 11, "LC-102": 40, "LC-450": 13,
    "DC-105": 8,  "DC-218": 18, "DC-076": 30, "DC-330": 9,
    "BT-088": 10, "BT-201": 16, "BT-055": 50, "BT-312": 21,
    "DH-Longines-L45": 4, "DH-Tissot-T01": 6, "DH-Citizen-BM": 8,
    "PK-001": 60, "PK-002": 9999,
}

# ─── Rules ───────────────────────────────────────────────────────────────────

RULES = [
    {
        "id": "RULE-01", "name": "Nhẫn cưới yếu trong cao điểm",
        "when": "wedding_revenue_pct < 0.32 AND strong_wedding_staff_in_peak < 2 AND is_afternoon_shift",
        "then": ["focus_wedding_sku", "add_strong_staff_to_peak"],
        "why": "Nhẫn cưới chiếm 40–50% doanh thu lý tưởng. Thiếu người + thiếu focus SKU đồng thời là nguyên nhân số 1 miss target.",
        "confidence": 0.85, "feedback_count": 0, "positive_feedback": 0
    },
    {
        "id": "RULE-02", "name": "Traffic tốt, CR thấp = vấn đề tư vấn",
        "when": "traffic_ratio >= 0.90 AND cr_ratio < 0.85",
        "then": ["change_sales_pitch", "simplify_choice_set"],
        "why": "Khách vào đủ nhưng không chốt được → không phải thiếu traffic, mà cách tư vấn chưa phù hợp với nhóm khách hiện tại.",
        "confidence": 0.80, "feedback_count": 0, "positive_feedback": 0
    },
    {
        "id": "RULE-03", "name": "Pace revenue chậm sau giữa ngày",
        "when": "revenue_at_noon_pct < 0.38 AND is_midday",
        "then": ["alert_manager", "suggest_mini_activation", "review_staff_allocation"],
        "why": "Nếu đến giữa ngày chỉ đạt < 38% target thì ca chiều phải chịu áp lực rất lớn. Cần can thiệp sớm.",
        "confidence": 0.88, "feedback_count": 0, "positive_feedback": 0
    },
    {
        "id": "RULE-04", "name": "Không có senior giờ vàng",
        "when": "senior_count_in_peak == 0 AND is_peak_hour",
        "then": ["reassign_senior_to_peak", "alert_manager"],
        "why": "Senior tạo ra 40–45% doanh thu trong giờ cao điểm. Vắng mặt toàn bộ = rủi ro mất 10–15% doanh thu ngày.",
        "confidence": 0.90, "feedback_count": 0, "positive_feedback": 0
    },
    {
        "id": "RULE-05", "name": "Cơ cấu SKU lệch sang margin thấp",
        "when": "low_margin_revenue_pct > 0.55",
        "then": ["focus_high_margin_sku", "coach_upsell_technique"],
        "why": "Doanh thu nhìn đẹp nhưng lợi nhuận thực tế thấp. Cần dịch chuyển mix sang sản phẩm sinh lời tốt hơn.",
        "confidence": 0.75, "feedback_count": 0, "positive_feedback": 0
    },
    {
        "id": "RULE-06", "name": "Nhóm khách couple cao, nhẫn cưới bán thấp",
        "when": "couple_traffic_pct >= 0.35 AND wedding_engagement_revenue_pct < 0.40",
        "then": ["focus_wedding_sku", "focus_emotional_selling", "pair_junior_with_senior"],
        "why": "Khách couple vào mà không mua nhẫn là đang bỏ cơ hội lớn. Cần senior dẫn dắt tư vấn.",
        "confidence": 0.82, "feedback_count": 0, "positive_feedback": 0
    },
    {
        "id": "RULE-07", "name": "Junior nhiều, Senior ít → cần ghép cặp",
        "when": "junior_count > senior_count * 2 AND traffic > baseline_traffic",
        "then": ["pair_junior_with_senior", "buddy_system_coaching"],
        "why": "Junior nhiều hơn senior 2:1 trong giờ đông sẽ làm giảm chất lượng tư vấn.",
        "confidence": 0.70, "feedback_count": 0, "positive_feedback": 0
    },
    {
        "id": "RULE-08", "name": "Hàng tồn cao nhưng bán chậm",
        "when": "slow_sku_stock >= 10 AND slow_sku_no_sale_7days AND slow_sku_cvr >= 0.40",
        "then": ["feature_slow_moving_sku", "suggest_display_change"],
        "why": "Hàng tồn cao + CVR tốt nhưng không bán → vấn đề có thể là không được trưng bày đúng chỗ.",
        "confidence": 0.73, "feedback_count": 0, "positive_feedback": 0
    },
    {
        "id": "RULE-09", "name": "Dự báo miss target cuối ngày",
        "when": "revenue_at_16h_pct < 0.55",
        "then": ["urgent_alert", "activate_closing_push", "reassign_best_staff"],
        "why": "Với pace này, khó đạt target ngay cả khi ca chiều tốt. Cần push mạnh nhất trong 4 giờ còn lại.",
        "confidence": 0.87, "feedback_count": 0, "positive_feedback": 0
    },
    {
        "id": "RULE-10", "name": "Thứ 2 traffic thấp = cần kích hoạt",
        "when": "is_monday AND morning_traffic_ratio < 0.60",
        "then": ["suggest_proactive_greeting", "activate_social_sharing_incentive"],
        "why": "Thứ 2 traffic vốn thấp. Nếu thấp hơn bình thường thứ 2 → cần tạo lý do cho khách ghé thêm.",
        "confidence": 0.68, "feedback_count": 0, "positive_feedback": 0
    },
    {
        "id": "RULE-11", "name": "Cuối tháng + AOV thấp → gợi ý trả góp",
        "when": "day_of_month >= 25 AND aov < 4_000_000",
        "then": ["suggest_installment_option", "focus_mid_price_sku"],
        "why": "Cuối tháng eo tiền, khách vẫn muốn mua nhưng e ngại giá. Gợi ý trả góp 0% tăng chuyển đổi đáng kể.",
        "confidence": 0.72, "feedback_count": 0, "positive_feedback": 0
    },
    {
        "id": "RULE-12", "name": "Khách nữ độc thân cao, nhẫn thời trang thấp",
        "when": "female_solo_pct >= 0.40 AND fashion_ring_bracelet_pct < 0.25",
        "then": ["change_sales_pitch_self_reward", "feature_trending_fashion_sku"],
        "why": "Nhóm nữ độc thân đang là cơ hội bỏ lỡ. Chuyển pitch sang 'tự thưởng cho bản thân' tăng CR 15–20%.",
        "confidence": 0.76, "feedback_count": 0, "positive_feedback": 0
    },
]

# ─── Action Registry ─────────────────────────────────────────────────────────

ACTION_REGISTRY = [
    {"id": "focus_wedding_sku", "name": "Tập trung tư vấn SKU nhẫn cưới CVR cao", "type": "product", "urgency": "HIGH"},
    {"id": "focus_high_margin_sku", "name": "Ưu tiên đẩy SKU biên lợi nhuận cao", "type": "product", "urgency": "MEDIUM"},
    {"id": "focus_mid_price_sku", "name": "Focus sản phẩm tầm trung 3–8 triệu", "type": "product", "urgency": "MEDIUM"},
    {"id": "feature_slow_moving_sku", "name": "Trưng bày nổi bật SKU tồn chậm", "type": "product", "urgency": "LOW"},
    {"id": "feature_trending_fashion_sku", "name": "Nổi bật SKU nhẫn thời trang trending", "type": "product", "urgency": "MEDIUM"},
    {"id": "suggest_display_change", "name": "Đề xuất đổi vị trí trưng bày", "type": "product", "urgency": "LOW"},

    {"id": "add_strong_staff_to_peak", "name": "Bổ sung NV mạnh vào ca cao điểm", "type": "staff", "urgency": "HIGH"},
    {"id": "reassign_senior_to_peak", "name": "Điều chuyển senior vào giờ 17h–20h", "type": "staff", "urgency": "HIGH"},
    {"id": "reassign_best_staff", "name": "Điều chuyển NV tốt nhất vào ca chốt", "type": "staff", "urgency": "HIGH"},
    {"id": "reassign_staff_strong_category", "name": "Phân NV mạnh đúng nhóm khách", "type": "staff", "urgency": "HIGH"},
    {"id": "pair_junior_with_senior", "name": "Ghép NV mới với NV giỏi", "type": "staff", "urgency": "MEDIUM"},
    {"id": "buddy_system_coaching", "name": "Kích hoạt mentor–mentee trong ca", "type": "staff", "urgency": "LOW"},

    {"id": "suggest_mini_activation", "name": "Kích hoạt mini campaign tại chỗ", "type": "ops", "urgency": "HIGH"},
    {"id": "activate_closing_push", "name": "Push mạnh trong 2–3h cuối ngày", "type": "ops", "urgency": "HIGH"},
    {"id": "urgent_alert", "name": "Cảnh báo khẩn cho CHT", "type": "ops", "urgency": "HIGH"},
    {"id": "activate_social_sharing_incentive", "name": "Khuyến khích khách check-in/share", "type": "ops", "urgency": "MEDIUM"},
    {"id": "suggest_installment_option", "name": "Gợi ý trả góp 0% cho khách", "type": "ops", "urgency": "MEDIUM"},
    {"id": "alert_manager", "name": "Gửi alert ngay cho CHT", "type": "ops", "urgency": "HIGH"},
    {"id": "review_staff_allocation", "name": "Xem xét lại phân bổ nhân sự", "type": "ops", "urgency": "MEDIUM"},

    {"id": "change_sales_pitch", "name": "Điều chỉnh cách tiếp cận khách", "type": "selling", "urgency": "MEDIUM"},
    {"id": "change_sales_pitch_self_reward", "name": "Dùng pitch 'tự thưởng cho bản thân'", "type": "selling", "urgency": "MEDIUM"},
    {"id": "simplify_choice_set", "name": "Giảm số lựa chọn khi tư vấn (≤3 mẫu)", "type": "selling", "urgency": "MEDIUM"},
    {"id": "focus_emotional_selling", "name": "Khai thác cảm xúc/câu chuyện khi bán", "type": "selling", "urgency": "LOW"},
    {"id": "coach_upsell_technique", "name": "Coach NV kỹ năng upsell", "type": "selling", "urgency": "LOW"},
    {"id": "suggest_proactive_greeting", "name": "Chủ động chào hỏi từ lối vào", "type": "selling", "urgency": "LOW"},
]

# ─── Helpers ─────────────────────────────────────────────────────────────────

CUSTOMER_TYPES = ["couple", "female_solo", "male_solo", "gift_buyer", "family"]

# Mỗi loại khách có danh sách category ưu tiên — dùng để chọn SKU
CATEGORY_CUSTOMER_MAP = {
    "couple": ["wedding_ring", "engagement_ring", "necklace", "bracelet"],
    "female_solo": ["fashion_ring", "bracelet", "necklace", "earring"],
    "male_solo": ["fashion_ring", "accessory", "necklace", "bracelet"],   # bỏ watch/wedding (hiếm)
    "gift_buyer": ["earring", "bracelet", "accessory", "fashion_ring"],
    "family": ["necklace", "bracelet", "earring", "fashion_ring", "accessory"],
}

# Xác suất mua item đắt (>=5M) theo loại khách — để kiểm soát AOV thực tế
# Xác suất couple mua nhẫn cưới/đính hôn thay vì đồ phụ
COUPLE_WEDDING_PROB = 0.26   # ~26% cặp đôi mua nhẫn cưới hoặc đính hôn

# Giá ngưỡng "rẻ" — khi khách không mua wedding ring
CHEAP_PRICE_THRESHOLD = 4_000_000

# CR calibration — để revenue khớp với target thực tế
CR_CALIBRATION = 0.68

SPECIAL_DAYS = {}  # date_str -> multiplier


def _build_special_days(today: date):
    """Đánh dấu các ngày đặc biệt trong 30 ngày lịch sử."""
    for i in range(31):
        d = today - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        # 20/10
        if d.month == 10 and d.day == 20:
            SPECIAL_DAYS[ds] = 1.9
        # Valentine
        elif d.month == 2 and d.day == 14:
            SPECIAL_DAYS[ds] = 2.0
        # 8/3
        elif d.month == 3 and d.day == 8:
            SPECIAL_DAYS[ds] = 1.7
        # Đầu tháng
        elif 1 <= d.day <= 5:
            SPECIAL_DAYS[ds] = 1.15
        # Cuối tháng
        elif d.day >= 25:
            SPECIAL_DAYS[ds] = 0.88


def _traffic_for_day(d: date, store: dict) -> int:
    """Tính traffic baseline của 1 ngày."""
    base = {"A": 130, "B": 95, "C": 70}[store["segment"]]
    dow = d.weekday()  # 0=Mon
    if dow == 0:
        mult = 0.75
    elif dow in (5, 6):
        mult = 1.35
    else:
        mult = 1.0
    ds = d.strftime("%Y-%m-%d")
    special = SPECIAL_DAYS.get(ds, 1.0)
    raw = base * mult * special
    noise = random.uniform(0.9, 1.1)
    return max(10, int(raw * noise))


def _hourly_distribution(total: int) -> dict:
    """Phân phối traffic theo giờ trong ngày."""
    weights = {
        9: 0.06, 10: 0.08, 11: 0.09, 12: 0.07,
        13: 0.06, 14: 0.08, 15: 0.09, 16: 0.09,
        17: 0.12, 18: 0.13, 19: 0.10, 20: 0.02, 21: 0.01
    }
    dist = {}
    remaining = total
    hours = sorted(weights.keys())
    for h in hours[:-1]:
        v = max(0, int(total * weights[h] * random.uniform(0.85, 1.15)))
        dist[h] = min(v, remaining)
        remaining -= dist[h]
    dist[hours[-1]] = max(0, remaining)
    return dist


def _pick_sku(store: dict, customer_type: str, d: date) -> dict | None:
    """
    Chọn SKU dựa trên loại khách và segment store.
    - Couple: 30% mua nhẫn cưới/đính hôn, 70% mua dây chuyền/lắc rẻ hơn
    - Khách khác: chủ yếu mua item dưới CHEAP_PRICE_THRESHOLD
    """
    segment = store["segment"]

    # Couple có xác suất mua nhẫn cưới cao hơn
    if customer_type == "couple" and random.random() < COUPLE_WEDDING_PROB:
        wedding_skus = [s for s in SKUS if segment in s["segments"]
                        and s["category"] in ["wedding_ring", "engagement_ring"]]
        if wedding_skus:
            weights = [s["cvr_history"] for s in wedding_skus]
            return random.choices(wedding_skus, weights=weights, k=1)[0]

    preferred_cats = CATEGORY_CUSTOMER_MAP.get(customer_type, ["fashion_ring"])
    eligible = [s for s in SKUS if segment in s["segments"]
                and s["category"] in preferred_cats]
    if not eligible:
        eligible = [s for s in SKUS if segment in s["segments"]]
    if not eligible:
        return None

    # Ưu tiên item rẻ (<4.5M) để AOV thực tế ~2M
    cheap = [s for s in eligible if s["price"] < CHEAP_PRICE_THRESHOLD]
    if cheap:
        eligible = cheap

    weights = [s["cvr_history"] for s in eligible]
    return random.choices(eligible, weights=weights, k=1)[0]


def _staff_for_shift(store_id: str, shift: str, roster_day: dict) -> list[str]:
    shift_key = {"morning": "morning_staff", "afternoon": "afternoon_staff", "evening": "evening_staff"}[shift]
    return roster_day.get(shift_key, [])


def _cr_for_staff(staff_id: str, staff_map: dict, customer_type: str) -> float:
    nv = staff_map.get(staff_id, {})
    base_cr = nv.get("avg_cr", 0.33)
    # Adjust by customer–category match
    preferred_cats = CATEGORY_CUSTOMER_MAP.get(customer_type, [])
    strong = nv.get("strong_categories", [])
    if any(c in strong for c in preferred_cats):
        return min(0.90, base_cr * 1.15)
    return base_cr


# ─── Generate Roster ─────────────────────────────────────────────────────────

def gen_roster(today: date) -> list:
    roster = []
    store_staff = {}
    for nv in STAFF:
        store_staff.setdefault(nv["store_id"], []).append(nv["id"])

    for store in STORES:
        sid = store["id"]
        nvs = store_staff.get(sid, [])
        # Tách theo level để roster hợp lý
        seniors = [n for n in nvs if next((x for x in STAFF if x["id"] == n), {}).get("level") == "senior"]
        others = [n for n in nvs if n not in seniors]

        for i in range(31):
            d = today - timedelta(days=i)
            ds = d.strftime("%Y-%m-%d")
            dow = d.weekday()
            is_weekend = dow in (5, 6)
            all_nv = list(nvs)
            random.shuffle(all_nv)

            # STR-002 đặc biệt: 5–7 ngày ca chiều thiếu senior wedding
            bao_ngoc = "NV001"
            thu_huong = "NV007"
            wedding_seniors = [bao_ngoc, thu_huong]

            morning_size = 3 if is_weekend else 2
            afternoon_size = 4 if is_weekend else 3
            evening_size = 2

            if sid == "STR-002":
                # Tạo tình huống thiếu senior wedding ở ca chiều cho 7/31 ngày
                bad_day = (i % 4 == 1)  # khoảng 7–8 ngày
                if bad_day:
                    # Bảo Ngọc ca sáng, Thu Hương ca tối
                    morning_pool = [bao_ngoc] + [n for n in others if n != thu_huong]
                    afternoon_pool = [n for n in nvs if n not in wedding_seniors]
                    evening_pool = [thu_huong] + [n for n in others if n not in morning_pool[:morning_size]]
                else:
                    morning_pool = [n for n in nvs if n not in [bao_ngoc, thu_huong]]
                    afternoon_pool = [bao_ngoc, thu_huong] + [n for n in others]
                    evening_pool = [n for n in nvs if n not in morning_pool[:morning_size]
                                    and n not in afternoon_pool[:afternoon_size]]

                morning_staff = morning_pool[:morning_size]
                afternoon_staff = afternoon_pool[:afternoon_size]
                evening_staff = evening_pool[:evening_size]
            else:
                # Đảm bảo có ít nhất 1 senior ở ca chiều
                senior_morning = seniors[:1] if seniors else []
                senior_afternoon = seniors[1:2] if len(seniors) > 1 else seniors[:1]
                other_morning = [n for n in others if n not in senior_morning][:morning_size - len(senior_morning)]
                other_afternoon = [n for n in others if n not in senior_afternoon and n not in other_morning][:afternoon_size - len(senior_afternoon)]

                morning_staff = (senior_morning + other_morning)[:morning_size]
                afternoon_staff = (senior_afternoon + other_afternoon)[:afternoon_size]
                evening_staff = [n for n in nvs if n not in morning_staff and n not in afternoon_staff][:evening_size]

            roster.append({
                "date": ds,
                "store_id": sid,
                "morning_staff": morning_staff,
                "morning_start": "09:00",
                "morning_end": "14:00",
                "afternoon_staff": afternoon_staff,
                "afternoon_start": "14:00",
                "afternoon_end": "20:00",
                "evening_staff": evening_staff,
                "evening_start": "20:00",
                "evening_end": "22:00",
            })
    return roster


# ─── Generate Transactions ───────────────────────────────────────────────────

def gen_transactions(today: date, roster: list) -> list:
    txns = []
    staff_map = {nv["id"]: nv for nv in STAFF}

    # Roster lookup
    roster_lookup = {}
    for r in roster:
        roster_lookup[(r["store_id"], r["date"])] = r

    txn_id = 1
    for store in STORES:
        sid = store["id"]
        for i in range(31):
            d = today - timedelta(days=i)
            ds = d.strftime("%Y-%m-%d")
            traffic = _traffic_for_day(d, store)
            hourly = _hourly_distribution(traffic)
            rl = roster_lookup.get((sid, ds), {})

            # Xác định tỷ lệ khách theo ngày
            is_special = ds in SPECIAL_DAYS and SPECIAL_DAYS[ds] > 1.4
            if is_special:
                ct_weights = [0.40, 0.28, 0.12, 0.12, 0.08]  # couple cao trong ngày đặc biệt
            else:
                ct_weights = [0.22, 0.35, 0.18, 0.15, 0.10]

            for hour, count in hourly.items():
                if count == 0:
                    continue
                # Xác định ca
                if 9 <= hour < 14:
                    shift = "morning"
                    staff_ids = rl.get("morning_staff", [])
                elif 14 <= hour < 20:
                    shift = "afternoon"
                    staff_ids = rl.get("afternoon_staff", [])
                else:
                    shift = "evening"
                    staff_ids = rl.get("evening_staff", [])

                if not staff_ids:
                    staff_ids = [nv["id"] for nv in STAFF if nv["store_id"] == sid][:2]

                for _ in range(count):
                    ctype = random.choices(CUSTOMER_TYPES, weights=ct_weights)[0]
                    # Xác định CR dựa trên staff ca này
                    staff_id = random.choice(staff_ids)
                    cr = _cr_for_staff(staff_id, staff_map, ctype) * CR_CALIBRATION

                    if random.random() > cr:
                        continue  # Khách không mua

                    sku = _pick_sku(store, ctype, d)
                    if not sku:
                        continue

                    # Giá thực tế (có thể discount nhỏ)
                    has_promo = random.random() < 0.12
                    actual_price = sku["price"] * (0.93 if has_promo else 1.0)
                    actual_price = round(actual_price / 1000) * 1000

                    minute = random.randint(0, 59)
                    second = random.randint(0, 59)
                    ts = f"{ds} {hour:02d}:{minute:02d}:{second:02d}"

                    txns.append({
                        "id": f"TXN-{txn_id:06d}",
                        "store_id": sid,
                        "date": ds,
                        "timestamp": ts,
                        "hour": hour,
                        "shift": shift,
                        "sku_id": sku["id"],
                        "category": sku["category"],
                        "quantity": 1,
                        "unit_price": sku["price"],
                        "actual_price": actual_price,
                        "staff_id": staff_id,
                        "customer_type": ctype,
                        "has_promotion": has_promo,
                    })
                    txn_id += 1

    return txns


# ─── Generate Daily Snapshots ────────────────────────────────────────────────

def gen_snapshots(today: date, transactions: list, roster: list) -> list:
    staff_map = {nv["id"]: nv for nv in STAFF}
    store_map = {s["id"]: s for s in STORES}

    # Group transactions
    day_store_txns: dict = {}
    for t in transactions:
        k = (t["store_id"], t["date"])
        day_store_txns.setdefault(k, []).append(t)

    # Group roster
    roster_lookup = {(r["store_id"], r["date"]): r for r in roster}

    snapshots = []
    for i in range(31):
        d = today - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        for store in STORES:
            sid = store["id"]
            target = store["daily_target"]
            txns = day_store_txns.get((sid, ds), [])
            traffic = _traffic_for_day(d, store)
            rl = roster_lookup.get((sid, ds), {})

            total_rev = sum(t["actual_price"] for t in txns)
            num_txns = len(txns)
            cr = num_txns / traffic if traffic > 0 else 0
            aov = total_rev / num_txns if num_txns > 0 else 0

            # Category breakdown
            cat_rev: dict = {}
            for t in txns:
                cat_rev[t["category"]] = cat_rev.get(t["category"], 0) + t["actual_price"]

            # Customer type breakdown
            ct_count: dict = {}
            for t in txns:
                ct_count[t["customer_type"]] = ct_count.get(t["customer_type"], 0) + 1

            # Staff performance
            staff_perf: dict = {}
            for t in txns:
                nv = t["staff_id"]
                if nv not in staff_perf:
                    staff_perf[nv] = {"revenue": 0, "orders": 0, "name": staff_map.get(nv, {}).get("name", nv)}
                staff_perf[nv]["revenue"] += t["actual_price"]
                staff_perf[nv]["orders"] += 1

            # Shift revenue
            shift_rev = {"morning": 0, "afternoon": 0, "evening": 0}
            for t in txns:
                shift_rev[t["shift"]] = shift_rev.get(t["shift"], 0) + t["actual_price"]

            # Count CR per staff
            shift_traffic = {"morning": 0, "afternoon": 0, "evening": 0}
            for h, cnt in _hourly_distribution(traffic).items():
                if 9 <= h < 14:
                    shift_traffic["morning"] += cnt
                elif 14 <= h < 20:
                    shift_traffic["afternoon"] += cnt
                else:
                    shift_traffic["evening"] += cnt

            snapshots.append({
                "date": ds,
                "store_id": sid,
                "target": target,
                "revenue": total_rev,
                "target_pct": total_rev / target if target > 0 else 0,
                "traffic": traffic,
                "num_transactions": num_txns,
                "conversion_rate": cr,
                "aov": aov,
                "category_revenue": cat_rev,
                "customer_type_count": ct_count,
                "shift_revenue": shift_rev,
                "shift_traffic": shift_traffic,
                "staff_performance": staff_perf,
                "morning_staff": rl.get("morning_staff", []),
                "afternoon_staff": rl.get("afternoon_staff", []),
                "evening_staff": rl.get("evening_staff", []),
                "day_of_week": d.strftime("%A"),
                "day_of_week_vn": ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm",
                                    "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"][d.weekday()],
                "is_special_day": ds in SPECIAL_DAYS and SPECIAL_DAYS[ds] > 1.4,
                "special_day_multiplier": SPECIAL_DAYS.get(ds, 1.0),
            })

    return snapshots


def gen_store_inventory(today: date) -> list:
    """
    Sinh tồn kho per-store per-SKU với đặc thù riêng từng cửa hàng.
    - stock: tồn kho thực tế, khác nhau theo store và SKU
    - cvr_local: tỷ lệ chuyển đổi lịch sử riêng của store (khác với cvr_history toàn hệ thống)
    - display_position: front / standard / vault (ảnh hưởng trực tiếp đến khả năng bán)
    - last_sold_date: ngày bán gần nhất (để phát hiện slow-moving)
    """
    records = []
    for store in STORES:
        sid = store["id"]
        seg = store["segment"]
        profile = STORE_INV_PROFILES.get(sid, {})
        stock_mult = profile.get("stock_mult", 1.0)
        cvr_adj_map = profile.get("cvr_adj", {})
        front_cats = profile.get("front_cats", [])
        vault_skus = profile.get("vault_skus", [])
        slow_skus = profile.get("slow_skus", [])

        eligible = [s for s in SKUS if seg in s.get("segments", [])]

        for sku in eligible:
            sku_id = sku["id"]
            cat = sku["category"]
            base_stock = SKU_BASE_STOCK.get(sku_id, 10)

            # ── Display position ──
            if sku_id in vault_skus:
                display_pos = "vault"
            elif cat in front_cats:
                display_pos = "front"
            else:
                display_pos = "standard"

            # ── Stock calculation ──
            if sku_id == "PK-002":  # Dịch vụ không giới hạn tồn
                stock = 9999
            elif sku_id in slow_skus:
                # Tồn cao chủ đích để test RULE-08
                stock = int(base_stock * stock_mult * random.uniform(1.0, 1.4))
                stock = max(stock, 12)
            elif display_pos == "vault":
                # Hàng cao cấp trong kho: ít hơn
                stock = max(1, int(base_stock * stock_mult * random.uniform(0.3, 0.6)))
            elif display_pos == "front":
                # Hàng trưng bày trước: bán tốt, tồn vừa phải
                stock = max(2, int(base_stock * stock_mult * random.uniform(0.5, 0.95)))
            else:
                stock = max(1, int(base_stock * stock_mult * random.uniform(0.6, 1.1)))

            # ── CVR local ──
            adj = cvr_adj_map.get(cat, 0.0)
            cvr_local = round(
                max(0.10, min(0.90, sku["cvr_history"] + adj + random.uniform(-0.03, 0.03))),
                3
            )

            # ── Last sold date ──
            if sku_id == "PK-002":
                last_sold = (today - timedelta(days=random.randint(0, 1))).isoformat()
            elif sku_id in slow_skus:
                # Chủ đích để lâu không bán (8–18 ngày) → trigger RULE-08
                last_sold = (today - timedelta(days=random.randint(8, 18))).isoformat()
            elif display_pos == "front" and cvr_local > 0.5:
                last_sold = (today - timedelta(days=random.randint(0, 3))).isoformat()
            elif display_pos == "vault":
                last_sold = (today - timedelta(days=random.randint(3, 12))).isoformat()
            else:
                last_sold = (today - timedelta(days=random.randint(1, 7))).isoformat()

            records.append({
                "store_id": sid,
                "sku_id": sku_id,
                "stock": stock,
                "display_position": display_pos,
                "cvr_local": cvr_local,
                "last_sold_date": last_sold,
            })

    return records


def _save(filename: str, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ {filename} ({len(data) if isinstance(data, list) else 'dict'})")


def main():
    print("=== Sinh dữ liệu mẫu AI Store Copilot ===")
    today = date(2026, 5, 5)  # ngày cố định per CLAUDE.md context

    _build_special_days(today)

    print("\n[1/7] Lưu stores, staff, SKUs, rules, actions...")
    _save("stores.json", STORES)
    _save("staff.json", STAFF)
    _save("skus.json", SKUS)
    _save("rules.json", RULES)
    _save("action_registry.json", ACTION_REGISTRY)

    print("\n[2/7] Sinh lịch làm việc (roster) 31 ngày × 8 stores...")
    roster = gen_roster(today)
    _save("roster.json", roster)

    print("\n[3/7] Sinh giao dịch (transactions) 31 ngày × 8 stores...")
    transactions = gen_transactions(today, roster)
    _save("transactions.json", transactions)
    print(f"       Tổng số giao dịch: {len(transactions):,}")

    print("\n[4/7] Tính daily snapshots...")
    snapshots = gen_snapshots(today, transactions, roster)
    _save("snapshots.json", snapshots)

    print("\n[5/7] Sinh tồn kho per-store (store_inventory.json)...")
    inventory = gen_store_inventory(today)
    _save("store_inventory.json", inventory)
    print(f"       Tổng records: {len(inventory)} ({len(STORES)} stores × ~{len(SKUS)} SKUs)")

    print("\n[6/7] Khởi tạo chat history, notifications, action feedback...")
    _save("chat_history.json", {})
    _save("notifications.json", [])
    _save("action_feedback.json", [])

    print("\n=== Hoàn tất! Dữ liệu đã sẵn sàng. ===")


if __name__ == "__main__":
    main()
