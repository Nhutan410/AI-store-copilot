# Giải thích chi tiết 12 Rules — AI Store Copilot Rule Engine

> **Mục tiêu tài liệu:** Giúp bất kỳ ai trong team hiểu rõ từng rule hoạt động như thế nào, tại sao nó tồn tại, và khi nào nó được kích hoạt — không cần đọc code.

---

## Tổng quan kiến trúc Rule Engine

### Rule Engine là gì?

Rule Engine là lớp phân tích **chạy trước AI (LLM)**. Nó đọc dữ liệu thực tế của cửa hàng trong ngày, so sánh với các ngưỡng nghiệp vụ, rồi quyết định vấn đề nào đang xảy ra. AI (Qwen2.5) sau đó chỉ việc diễn đạt những phát hiện này thành ngôn ngữ tự nhiên tiếng Việt.

```
Dữ liệu thực tế
      ↓
Rule Engine (nhanh, deterministic, không tốn token)
      ↓ danh sách vấn đề đã phát hiện
LLM (diễn đạt, giải thích, đề xuất bằng tiếng Việt)
      ↓
CHT nhận báo cáo / gợi ý hành động
```

### Cấu trúc của mỗi Rule

Mỗi rule gồm 4 phần:

| Phần | Ý nghĩa |
|---|---|
| **WHEN** | Điều kiện kích hoạt — so sánh metric thực tế với ngưỡng nghiệp vụ |
| **THEN** | Danh sách action cụ thể được gợi ý cho CHT |
| **WHY** | Lý do nghiệp vụ — giải thích tại sao rule này quan trọng |
| **confidence** | Mức độ tin cậy của rule (xem phần cuối tài liệu) |

### Thứ tự ưu tiên hiển thị

Sau khi chạy tất cả 12 rules, hệ thống sắp xếp kết quả theo:
1. **Urgency** trước: HIGH → MEDIUM → LOW
2. Trong cùng mức urgency: rule có **confidence cao hơn** hiển thị trước

---

## 12 Rules chi tiết

---

### RULE-01 — Nhẫn cưới yếu trong cao điểm

**Confidence: 0.95** | **Urgency: HIGH**

#### Khi nào rule này kích hoạt?

Rule kích hoạt khi **cả 3 điều kiện xảy ra đồng thời** trong ca chiều (14h–20h):

| Điều kiện | Ngưỡng | Ý nghĩa thực tế |
|---|---|---|
| Doanh thu nhẫn cưới / tổng doanh thu < 32% | `wedding_revenue_pct < 0.32` | Nhẫn cưới đang bán quá ít so với tiềm năng |
| Số NV có kỹ năng mạnh về nhẫn cưới đang làm ca chiều < 2 người | `strong_wedding_staff_in_peak < 2` | Không đủ người tốt để tư vấn nhẫn cưới |
| Đang trong ca chiều (14h–20h) | `is_afternoon_shift` | Đây là ca cao điểm, cần hành động ngay |

**Tại sao phải cả 3 điều kiện cùng lúc?**

Rule dùng logic AND chặt — nếu chỉ 1 hoặc 2 điều kiện đúng thì chưa cần lo:
- Nhẫn cưới thấp **nhưng** đang là ca sáng → bình thường, ca chiều mới là lúc bán nhiều
- Ca chiều thiếu NV wedding **nhưng** nhẫn cưới đang chiếm >32% → đội hình hiện tại vẫn đang làm được
- Chỉ khi cả hai vấn đề xảy ra **đúng trong giờ vàng** → cần hành động ngay lập tức

**Hành động được gợi ý:**

- `focus_wedding_sku` — Nhắc nhở toàn bộ TVV ưu tiên dẫn khách về phía khu trưng bày nhẫn cưới, chủ động gợi ý các mẫu NC-156, NC-218 có CVR cao
- `add_strong_staff_to_peak` — Nếu có NV giỏi nhẫn cưới đang làm việc khác hoặc nghỉ giữa ca → điều vào quầy ngay

**Cảnh báo sớm (trước khi sự việc xảy ra):**

Rule này còn có 2 chế độ cảnh báo trước:
- **Đầu ca chiều (14h–17h):** Nếu ca chiều vừa bắt đầu mà đã thiếu NV wedding → cảnh báo "CHUẨN BỊ CAO ĐIỂM", cần bổ sung trước 17h
- **Đang ca sáng:** Nếu lịch ca chiều sắp tới chỉ có < 2 NV wedding mạnh → cảnh báo "CHUẨN BỊ CA CHIỀU", điều chuyển trước 14h

**Bối cảnh PNJ — tại sao rule này quan trọng nhất?**

Nhẫn cưới là nhóm sản phẩm có giá trị đơn hàng cao nhất: 5–26 triệu đồng/đôi. Trong một ngày lý tưởng, nhẫn cưới nên chiếm 40–50% tổng doanh thu. Chỉ cần thêm 2–3 đơn nhẫn cưới là thay đổi hoàn toàn bức tranh doanh thu cả ngày. Đây là lý do rule này có confidence cao nhất hệ thống (0.95).

**Ví dụ từ demo data (ngày hôm qua tại STR-002):**

Bảo Ngọc (senior, wedding mạnh nhất store) làm ca sáng. Ca chiều chỉ có Võ Thanh Tùng là NV có kỹ năng wedding — thiếu 1 người so với ngưỡng 2. Kết quả: 28 lượt khách couple vào nhưng chỉ bán được 4 đôi nhẫn cưới, wedding ratio chỉ đạt 23.2% thay vì 40% kỳ vọng.

---

### RULE-02 — Traffic tốt, CR thấp = vấn đề tư vấn

**Confidence: 0.80** | **Urgency: MEDIUM**

#### Khi nào rule này kích hoạt?

Rule kích hoạt khi **cả 2 điều kiện xảy ra đồng thời**:

| Điều kiện | Ngưỡng | Ý nghĩa thực tế |
|---|---|---|
| Traffic hôm nay ≥ 90% trung bình 14 ngày qua | `traffic_ratio >= 0.90` | Khách đang vào đủ, không phải thiếu người |
| Conversion Rate hôm nay < 85% trung bình 14 ngày qua | `cr_ratio < 0.85` | Tỷ lệ chốt đơn thấp hơn bình thường >15% |

**Logic nghiệp vụ cốt lõi — phân biệt 2 vấn đề hoàn toàn khác nhau:**

| Tình huống | Biểu hiện | Nguyên nhân | Giải pháp |
|---|---|---|---|
| **Thiếu traffic** | Traffic thấp + CR thấp | Ít khách vào | Marketing, traffic activation |
| **Tư vấn kém** | Traffic đủ + CR thấp | Khách vào nhưng không chốt được | Đổi cách tiếp cận, training |

Rule-02 chỉ xử lý tình huống thứ 2. Khi traffic đạt ≥90% baseline nhưng CR lại thấp hơn thường lệ hơn 15%, điều đó có nghĩa là **khách vào đủ nhưng NV không chốt được đơn** — vấn đề nằm ở chất lượng tư vấn, không phải thiếu khách.

**Hành động được gợi ý:**

- `change_sales_pitch` — Điều chỉnh cách tiếp cận khách. Có thể nhóm khách hôm nay khác profile so với ngày thường (ví dụ nhiều nam solo hơn → cần pitch khác với nữ solo), NV cần nhận diện và điều chỉnh
- `simplify_choice_set` — Giảm số mẫu tư vấn xuống còn ≤ 3 options mỗi lần. Khi NV đưa ra quá nhiều lựa chọn, khách dễ bị "analysis paralysis" (tê liệt vì quá nhiều lựa chọn) và không mua

**Tại sao ngưỡng 85% cho CR?**

CR dao động tự nhiên theo ngày (thứ 2 thấp hơn thứ 7, đầu tháng cao hơn cuối tháng). Nếu chỉ thấp hơn 10% thì có thể do yếu tố bên ngoài bình thường. Nhưng khi CR thấp hơn 15% so với baseline trong khi traffic vẫn đủ — đó là tín hiệu rõ ràng có vấn đề về chất lượng tư vấn.

---

### RULE-03 — Pace revenue chậm sau giữa ngày

**Confidence: 0.88** | **Urgency: HIGH**

#### Khi nào rule này kích hoạt?

Rule kích hoạt khi **cả 2 điều kiện xảy ra đồng thời**:

| Điều kiện | Ngưỡng | Ý nghĩa thực tế |
|---|---|---|
| Doanh thu tích lũy ước tính đến 12h trưa < 38% target ngày | `revenue_at_noon_pct < 0.38` | Ca sáng đang rất chậm, không đủ tiến độ |
| Đang trong khung giờ 11h–13h | `is_midday` | Còn kịp can thiệp trước khi ca chiều bắt đầu |

**Tại sao ngưỡng 38% vào lúc 12h?**

Phân bổ doanh thu lý tưởng theo giờ tại PNJ:

```
09h–14h (Ca sáng)   : ~28–35% doanh thu ngày
14h–20h (Ca chiều)  : ~55–65% doanh thu ngày  ← cao điểm
20h–22h (Ca tối)    : ~8–12% doanh thu ngày
```

Vào lúc 12h (giữa ca sáng), nếu tích lũy chỉ đạt < 38% target thì ca sáng đang yếu hơn kỳ vọng. Dù ca chiều có tốt đến đâu, nếu ca sáng quá thấp thì tổng ngày vẫn khó đạt target — vì ca chiều chỉ còn ~6 tiếng (14h–20h) để gánh phần còn lại.

**Hành động được gợi ý:**

- `alert_manager` — Gửi cảnh báo ngay cho CHT, không đợi đến cuối ngày mới biết
- `suggest_mini_activation` — Kích hoạt hoạt động nhỏ tại chỗ: cải thiện trưng bày, NV chủ động hơn, tạo lý do để khách dừng lại lâu hơn
- `review_staff_allocation` — Kiểm tra lại xem NV mạnh nhất đang đứng ở đâu: có đang ở vị trí tiếp xúc khách tốt nhất không, hay đang làm việc khác không tạo ra doanh thu

---

### RULE-04 — Không có senior trong giờ vàng

**Confidence: 0.90** | **Urgency: HIGH**

#### Khi nào rule này kích hoạt?

Rule kích hoạt khi **1 trong các tình huống sau xảy ra**:

| Tình huống | Điều kiện | Khi nào |
|---|---|---|
| **Đang trong giờ vàng** mà không có NV senior nào | Ca 17h–20h hiện không có NV nào ở cấp senior | Đang trong khung 17h–20h |
| **Đầu ca chiều** (14h–17h) nhưng cả ca chiều không có senior | Ca chiều (14h–20h) không có NV senior, dù chưa đến 17h | Đang trong 14h–17h |
| **Ca sáng cảnh báo trước** — ca chiều sắp tới không có senior | Lịch ca chiều hôm nay không xếp NV senior nào | Đang trong ca sáng 9h–14h |

**Tại sao senior quan trọng đặc biệt trong giờ 17h–20h?**

Dữ liệu thực tế từ store STR-002 cho thấy:

| Cấp độ | CR cá nhân trung bình | Doanh thu trung bình/ngày |
|---|---|---|
| Senior (Bảo Ngọc, Minh Đức) | 48–52% | 17–18 triệu/người |
| Mid-level (Phương Thảo, Thanh Tùng) | 38–44% | 11–13 triệu/người |
| Junior (Ngọc Hân, Văn Quang) | 26–29% | 6–7 triệu/người |

Chênh lệch CR giữa senior và junior là khoảng **20 điểm phần trăm**. Trong giờ 17h–20h khi traffic tập trung cao nhất (35–40% doanh thu ngày), vắng mặt toàn bộ senior có thể làm mất 10–15% doanh thu cả ngày.

**Hành động được gợi ý:**

- `reassign_senior_to_peak` — Điều chuyển ngay NV senior vào ca 17h–20h, dù có thể cần thay đổi lịch
- `alert_manager` — Thông báo CHT để CHT ra quyết định phân bổ lại nhân sự

---

### RULE-05 — Cơ cấu SKU lệch sang margin thấp

**Confidence: 0.95** | **Urgency: MEDIUM**

#### Khi nào rule này kích hoạt?

| Điều kiện | Ngưỡng | Ý nghĩa thực tế |
|---|---|---|
| Tổng doanh thu từ các nhóm sản phẩm có margin thấp > 55% tổng doanh thu ngày | `low_margin_revenue_pct > 0.55` | Quá nhiều tiền đến từ sản phẩm sinh lời thấp |

**Nhóm sản phẩm được tính là "margin thấp" trong hệ thống:**

Bao gồm: nhẫn thời trang (18–25% margin), lắc tay (16–29% margin), dây chuyền (17–33% margin), bông tai (15–35% margin), và phụ kiện (45–90% — tuy margin % cao nhưng giá trị tuyệt đối rất nhỏ).

Không bao gồm: nhẫn cưới (29–42% margin) và nhẫn đính hôn (28–40% margin).

**Tại sao ngưỡng 55%?**

Đây là bài toán lợi nhuận ẩn. Một ngày bán được 80 triệu có thể tốt hơn hoặc tệ hơn một ngày bán 70 triệu, tùy vào cơ cấu sản phẩm:
- 80 triệu từ bông tai bạc + lắc bạc (margin ~15%) → lợi nhuận thực ~12 triệu
- 70 triệu từ nhẫn cưới + đính hôn (margin ~35%) → lợi nhuận thực ~24.5 triệu

Khi nhóm margin thấp vượt 55% doanh thu, dù doanh thu trông ổn nhưng lợi nhuận thực sự đang bị bào mòn.

**Hành động được gợi ý:**

- `focus_high_margin_sku` — Nhắc NV ưu tiên tư vấn và trưng bày nổi bật các SKU có margin cao: nhẫn cưới, nhẫn đính hôn, dây chuyền vàng 18k
- `coach_upsell_technique` — Hướng dẫn NV kỹ năng upsell: khi khách muốn mua lắc bạc, gợi ý thêm "Anh/chị có muốn xem lắc vàng 18k không? Bền hơn và giữ giá trị tốt hơn nhiều"

---

### RULE-06 — Nhóm khách couple cao, nhẫn cưới bán thấp

**Confidence: 0.82** | **Urgency: MEDIUM**

#### Khi nào rule này kích hoạt?

Rule kích hoạt khi **cả 2 điều kiện xảy ra đồng thời**:

| Điều kiện | Ngưỡng | Ý nghĩa thực tế |
|---|---|---|
| Tỷ lệ khách couple (cặp đôi) ≥ 35% tổng lượt khách vào store | `couple_traffic_pct >= 0.35` | Có đủ nhiều cặp đôi để tạo doanh thu nhẫn cưới lớn |
| Doanh thu nhẫn cưới + nhẫn đính hôn < 40% tổng doanh thu | `wedding_engagement_revenue_pct < 0.40` | Các cặp đôi đó đang mua thứ khác hoặc ra về mà không mua |

**Tại sao rule này khác với RULE-01?**

RULE-01 nhìn vào **nhân sự** (thiếu NV wedding mạnh).
RULE-06 nhìn vào **hành vi khách hàng** (nhiều cặp đôi vào nhưng không mua nhẫn).

Hai rule có thể trigger cùng lúc — thường thì nguyên nhân của RULE-06 chính là vì thiếu NV tốt (RULE-01), nhưng cũng có thể do cách tư vấn chưa đúng dù NV đã có mặt.

**Hành động được gợi ý:**

- `focus_wedding_sku` — Ưu tiên dẫn dắt các cặp đôi vào khu nhẫn cưới ngay từ đầu
- `focus_emotional_selling` — Không chỉ giới thiệu sản phẩm, mà khai thác câu chuyện cảm xúc: "Hai anh chị đang chuẩn bị cho đám cưới chưa, hay đang tìm nhẫn kỷ niệm?" — mở ra cuộc trò chuyện đúng hướng
- `pair_junior_with_senior` — Để senior dẫn dắt tư vấn với couple, junior hỗ trợ — vì nhẫn cưới là sản phẩm cần kinh nghiệm để chốt

**Bối cảnh PNJ:** Khách couple có AOV cao nhất: 15–25 triệu/đơn. Mỗi cặp đôi ra về mà không mua là bỏ lỡ cơ hội doanh thu lớn nhất trong ngày.

---

### RULE-07 — Junior nhiều, senior ít → cần ghép cặp

**Confidence: 0.70** | **Urgency: MEDIUM**

#### Khi nào rule này kích hoạt?

**Trong ca hiện tại** — rule trigger khi:

| Điều kiện | Ngưỡng | Ý nghĩa thực tế |
|---|---|---|
| Số NV junior đang làm việc > số NV senior × 2 | `junior_count > senior_count * 2` | Tỷ lệ junior:senior vượt 2:1 |
| Traffic hôm nay cao hơn baseline 14 ngày | `traffic > baseline_traffic` | Đang đông khách, áp lực tư vấn cao |

**Cảnh báo trước cho ca chiều** (khi đang là ca sáng) — trigger khi lịch ca chiều có tỷ lệ junior:senior > 2:1 và traffic dự báo ≥ 80% baseline.

**Tại sao tỷ lệ 2:1 là ngưỡng nguy hiểm?**

Khi có 1 senior và 1–2 junior: senior có thể kèm cặp, trả lời câu hỏi, hỗ trợ chốt đơn cho junior — hoạt động bình thường.

Khi có 1 senior và 3+ junior trong giờ đông: senior bị phân tán, không thể hỗ trợ hết, junior phải tự xử lý những tình huống phức tạp mà họ chưa đủ kinh nghiệm (khách hỏi giá, xin discount, cần tư vấn kỹ về kỹ thuật kim cương...) → CR toàn ca giảm.

**Hành động được gợi ý:**

- `pair_junior_with_senior` — Phân cặp rõ ràng ngay đầu ca: mỗi junior theo sát 1 senior cụ thể
- `buddy_system_coaching` — Kích hoạt chế độ mentor-mentee trong ca: junior quan sát cách senior tư vấn, học real-time

**Lưu ý:** Rule này có confidence thấp hơn các rule khác (0.70) vì hiệu quả phụ thuộc nhiều vào cá nhân — một junior giỏi vẫn có thể tự xử lý tốt, và không phải lúc nào ghép cặp cũng tạo kết quả ngay.

---

### RULE-08 — Hàng tồn cao nhưng bán chậm

**Confidence: 0.73** | **Urgency: LOW**

#### Khi nào rule này kích hoạt?

Rule kích hoạt khi tìm thấy **ít nhất 1 SKU** thỏa mãn **cả 3 điều kiện**:

| Điều kiện | Ngưỡng | Ý nghĩa thực tế |
|---|---|---|
| Tồn kho ≥ 10 đơn vị | `stock >= 10` | Sản phẩm đang tồn kho nhiều |
| Không có giao dịch nào trong 7 ngày qua | `no_sale_7days` | Sản phẩm đang không được bán |
| CVR lịch sử ≥ 40% | `cvr_history >= 0.40` | Sản phẩm từng bán tốt khi được tư vấn |

**Logic phát hiện "cơ hội bị bỏ lỡ":**

Sự kết hợp của 3 điều kiện trên tạo ra một nghịch lý: SKU này **có thể bán được** (CVR lịch sử tốt), **có hàng để bán** (tồn kho cao), nhưng lại **không được bán** (0 giao dịch 7 ngày). Nguyên nhân thường gặp:
- SKU không được trưng bày đúng vị trí (bị che khuất, đặt ở góc tối)
- NV không biết hoặc không nhớ đến sản phẩm này
- Không được include trong danh sách "sản phẩm cần đẩy" của ngày

**Hành động được gợi ý:**

- `feature_slow_moving_sku` — Đưa SKU này ra vị trí trưng bày nổi bật, thêm vào danh sách sản phẩm NV cần recommend
- `suggest_display_change` — Cân nhắc đổi vị trí trưng bày SKU này trong tủ kính

**Ví dụ từ demo data:** NC-218 (Nhẫn cưới vàng 18k Classic) và NC-305 (Nhẫn cưới kim cương 0.3ct) có CVR lịch sử 45% và 38% nhưng bán 0 đơn trong ngày hôm qua tại STR-002 — đây là ứng viên điển hình cho RULE-08.

---

### RULE-09 — Dự báo miss target cuối ngày

**Confidence: 0.87** | **Urgency: HIGH**

#### Khi nào rule này kích hoạt?

| Điều kiện | Ngưỡng | Ý nghĩa thực tế |
|---|---|---|
| Doanh thu tích lũy ước tính đến 16h < 55% target ngày | `revenue_at_16h_pct < 0.55` | Pace hiện tại không đủ để đạt target dù ca chiều có bình thường |

**Tại sao 16h và ngưỡng 55%?**

Lúc 16h, store đã trải qua 7/13 giờ mở cửa (9h–22h). Theo phân bổ lịch sử, đến 16h nên tích lũy được ~62% doanh thu ngày (bao gồm ca sáng đầy đủ và 2 tiếng đầu ca chiều). Nếu chỉ đạt < 55% — tức là chậm hơn kỳ vọng ~7 điểm — thì để đạt target, ca còn lại (16h–22h) phải tạo ra > 45% doanh thu trong 6 tiếng. Điều này chỉ khả thi nếu push rất mạnh.

**Cảnh báo sớm từ ca sáng:**

Nếu đang là ca sáng (trước 14h) và pace hiện tại dự báo đến 16h sẽ < 55% target → hệ thống gắn nhãn "[DỰ BÁO]" và cảnh báo CHT cần chuẩn bị push mạnh hơn cho ca chiều.

**Hành động được gợi ý:**

- `urgent_alert` — Cảnh báo khẩn cấp, ưu tiên hiển thị cao nhất trên dashboard
- `activate_closing_push` — Kích hoạt chiến lược push cuối ngày: NV chủ động hơn, ưu tiên khách có dấu hiệu quan tâm cao
- `reassign_best_staff` — Đảm bảo NV có CR cao nhất đang đứng ở vị trí tiếp khách trong 4 giờ còn lại

---

### RULE-10 — Thứ Hai traffic thấp = cần kích hoạt

**Confidence: 0.68** | **Urgency: MEDIUM**

#### Khi nào rule này kích hoạt?

Rule kích hoạt khi **cả 2 điều kiện xảy ra**:

| Điều kiện | Ngưỡng | Ý nghĩa thực tế |
|---|---|---|
| Hôm nay là thứ Hai | `is_monday` | Ngày traffic thấp nhất trong tuần theo lịch sử |
| Traffic buổi sáng (9h–14h) < 60% baseline thứ Hai | `morning_traffic_ratio < 0.60` | Thấp hơn cả mức thấp thông thường của thứ Hai |

**Tại sao phân biệt "baseline thứ Hai" riêng?**

Thứ Hai vốn đã thấp hơn ngày thường 20–25%. Nếu so sánh với baseline tổng thể, thứ Hai sẽ luôn "thấp" — không hữu ích. Rule này so sánh traffic thứ Hai hôm nay với **trung bình các thứ Hai khác trong 14 ngày qua** — nếu thậm chí còn thấp hơn cả mức thấp của thứ Hai bình thường, thì cần can thiệp.

**Hành động được gợi ý:**

- `suggest_proactive_greeting` — NV chủ động chào hỏi từ lối vào, tạo không khí thân thiện ngay từ đầu, không đợi khách bước vào mới để ý
- `activate_social_sharing_incentive` — Khuyến khích khách check-in tại store, share lên mạng xã hội để tạo thêm lý do ghé qua (mini viral effect)

**Lưu ý:** Rule này có confidence thấp nhất hệ thống (0.68) vì traffic thấp thứ Hai thường do yếu tố bên ngoài khó kiểm soát (thời tiết, sự kiện địa phương, tâm lý đầu tuần). Các action được gợi ý giúp nhưng không phải lúc nào cũng thay đổi được đáng kể.

---

### RULE-11 — Cuối tháng + AOV thấp → gợi ý trả góp

**Confidence: 0.72** | **Urgency: MEDIUM**

#### Khi nào rule này kích hoạt?

Rule kích hoạt khi **cả 2 điều kiện xảy ra**:

| Điều kiện | Ngưỡng | Ý nghĩa thực tế |
|---|---|---|
| Ngày trong tháng ≥ 25 | `day_of_month >= 25` | Đang trong tuần cuối tháng, tài chính cá nhân eo hẹp |
| Giá trị đơn hàng trung bình (AOV) < 4,000,000đ | `aov < 4_000_000` | Khách đang mua rẻ hơn mức trung bình |

**Insight hành vi tiêu dùng:**

Lịch sử cho thấy pattern rõ ràng:
- **Đầu tháng (1–5):** Lương vừa về, mua sắm nhiều hơn 15–20%, AOV cao hơn
- **Cuối tháng (25–31):** Tài chính cá nhân eo hẹp, khách vẫn **muốn mua** nhưng **e ngại số tiền lớn**

Nhưng khoảng cách giữa "muốn mua" và "có tiền mua" có thể được lấp đầy bằng **trả góp 0%** — khách trả một khoản nhỏ ngay, phần còn lại trả dần. Đây là cơ hội doanh thu đang bị bỏ lỡ nếu NV không chủ động đề xuất.

**Hành động được gợi ý:**

- `suggest_installment_option` — NV chủ động hỏi: "Anh/chị có muốn dùng dịch vụ trả góp 0% không? Với sản phẩm này anh/chị chỉ cần trả X triệu trước, phần còn lại chia đều các tháng sau"
- `focus_mid_price_sku` — Tập trung vào sản phẩm tầm 3–8 triệu đồng: vừa đủ hấp dẫn về giá trị, vừa không quá lớn để khách e ngại

---

### RULE-12 — Khách nữ độc thân cao, nhẫn thời trang thấp

**Confidence: 0.76** | **Urgency: MEDIUM**

#### Khi nào rule này kích hoạt?

Rule kích hoạt khi **cả 2 điều kiện xảy ra**:

| Điều kiện | Ngưỡng | Ý nghĩa thực tế |
|---|---|---|
| Tỷ lệ khách nữ đến một mình ≥ 40% tổng lượt khách | `female_solo_pct >= 0.40` | Nhóm khách chủ yếu là nữ solo |
| Doanh thu nhẫn thời trang + lắc tay < 25% tổng doanh thu | `fashion_ring_bracelet_pct < 0.25` | Đang không tận dụng được nhóm khách này |

**Insight về nhóm khách nữ độc thân:**

Nhóm nữ solo là nhóm **dễ bỏ lỡ nhất** tại PNJ vì hầu hết NV mặc định pitch theo kiểu "quà tặng cho người thân" hoặc "nhẫn cưới". Nhưng nữ solo thường đến để **tự thưởng cho bản thân** — đây là hoàn toàn khác về tâm lý mua.

Hai pitch hoàn toàn khác nhau:
- ❌ "Chị mua làm quà cho ai không? Hay chị đang tìm nhẫn đính hôn?"
- ✅ "Cái này hợp với chị lắm, đeo vào vừa sang vừa tự tin — chị có muốn thử không?"

Theo dữ liệu lịch sử, đổi pitch sang "tự thưởng" tăng CR với nhóm nữ solo 15–20%.

**Hành động được gợi ý:**

- `change_sales_pitch_self_reward` — Toàn bộ NV chuyển pitch: không hỏi "mua cho ai" mà tập trung vào cảm giác khi đeo, phong cách cá nhân, sự tự tin
- `feature_trending_fashion_sku` — Trưng bày nổi bật và giới thiệu các SKU đang trend: NT-301 (nhẫn sapphire), NT-267 (nhẫn hoa cúc), LC-201 (lắc vàng classic)

**Cảnh báo trước cho ca chiều:** Nếu đang là ca sáng và pattern này đã rõ từ dữ liệu buổi sáng → hệ thống gắn nhãn "[CHUẨN BỊ CA CHIỀU]" để CHT chuẩn bị cho team trước khi bắt đầu ca cao điểm.

---

## Bảng tổng hợp 12 Rules

| Rule | Tên | Confidence | Urgency | Điều kiện chính | Actions chính |
|---|---|---|---|---|---|
| RULE-01 | Nhẫn cưới yếu trong cao điểm | **0.95** | HIGH | Wedding < 32% + < 2 NV wedding mạnh ở ca chiều | focus_wedding_sku, add_strong_staff |
| RULE-02 | Traffic tốt, CR thấp | 0.80 | MEDIUM | Traffic ≥ 90% baseline nhưng CR < 85% baseline | change_sales_pitch, simplify_choice |
| RULE-03 | Pace chậm giữa ngày | 0.88 | HIGH | Đến 12h chưa đạt 38% target | alert_manager, mini_activation |
| RULE-04 | Không có senior giờ vàng | 0.90 | HIGH | Ca 17h–20h không có NV senior | reassign_senior, alert_manager |
| RULE-05 | SKU cơ cấu margin thấp | **0.95** | MEDIUM | Sản phẩm margin thấp > 55% doanh thu | focus_high_margin, coach_upsell |
| RULE-06 | Couple nhiều, nhẫn cưới thấp | 0.82 | MEDIUM | Couple ≥ 35% traffic + wedding < 40% revenue | focus_wedding, emotional_selling |
| RULE-07 | Junior nhiều, senior ít | 0.70 | MEDIUM | Junior > Senior × 2 khi traffic cao | pair_junior_senior, buddy_coaching |
| RULE-08 | Hàng tồn cao, bán chậm | 0.73 | LOW | Tồn ≥ 10 + 0 giao dịch 7 ngày + CVR ≥ 40% | feature_slow_sku, display_change |
| RULE-09 | Dự báo miss target | 0.87 | HIGH | Đến 16h chưa đạt 55% target | urgent_alert, closing_push |
| RULE-10 | Thứ Hai traffic thấp | **0.68** | MEDIUM | Thứ Hai + traffic sáng < 60% baseline thứ 2 | proactive_greeting, social_sharing |
| RULE-11 | Cuối tháng + AOV thấp | 0.72 | MEDIUM | Ngày ≥ 25 + AOV < 4 triệu | suggest_installment, mid_price_sku |
| RULE-12 | Nữ solo nhiều, fashion thấp | 0.76 | MEDIUM | Female solo ≥ 40% + fashion+bracelet < 25% | pitch_self_reward, feature_fashion |

---

## Cách đánh giá Confidence Score

### Confidence Score là gì?

Confidence Score (điểm tin cậy) là một số từ 0.0 đến 1.0 thể hiện **mức độ tin tưởng của hệ thống vào hiệu quả thực tế của rule đó**. Con số càng cao, rule càng đã được kiểm chứng là đáng tin và hữu ích.

### Công thức tính hiện tại

Hiện tại, hệ thống dùng điểm confidence khởi đầu được đặt thủ công dựa trên kiến thức nghiệp vụ PNJ. Đây là thiết kế có chủ đích: khi chưa có đủ dữ liệu feedback thực tế, dùng expert knowledge làm baseline.

```
Confidence khởi đầu = được đặt thủ công bởi team nghiệp vụ
                      dựa trên: mức độ phổ biến của pattern,
                                độ rõ ràng của mối quan hệ nhân quả,
                                kinh nghiệm thực tế từ các store PNJ
```

### Các yếu tố quyết định Confidence cao hay thấp

**1. Mối quan hệ nhân quả rõ ràng (Causality)**

Rule có mối quan hệ nhân quả trực tiếp, rõ ràng thì confidence cao hơn:
- RULE-01 (0.95): "Thiếu NV giỏi → bán ít nhẫn cưới" — quan hệ trực tiếp, không có biến số ẩn
- RULE-10 (0.68): "Thứ Hai traffic thấp → cần kích hoạt" — traffic thấp còn phụ thuộc thời tiết, sự kiện, tâm lý... nhiều yếu tố ngoài tầm kiểm soát

**2. Phổ biến của pattern (Frequency)**

Pattern xảy ra thường xuyên và nhất quán → confidence cao:
- RULE-04 (0.90): Vắng senior trong giờ cao điểm luôn kéo CR xuống — pattern nhất quán
- RULE-07 (0.70): Tỷ lệ junior/senior ảnh hưởng đến CR, nhưng mức độ còn phụ thuộc vào kỹ năng cá nhân từng NV

**3. Hành động có thể thực hiện ngay (Actionability)**

Rule có hành động cụ thể, CHT có thể làm ngay → confidence cao hơn rule chỉ mô tả vấn đề:
- RULE-09 (0.87): "Đến 16h chưa đạt 55% → push mạnh 4 giờ còn lại" — hành động rõ ràng, tức thì
- RULE-08 (0.73): "Hàng tồn cao, đổi vị trí trưng bày" — cần điều tra thêm nguyên nhân thực sự trước khi hành động

**4. Phạm vi kiểm soát (Controllability)**

Điều kiện nằm trong tầm kiểm soát của CHT → confidence cao:
- RULE-01, 04: Phân bổ nhân sự — CHT có thể điều chỉnh
- RULE-10: Traffic thứ Hai — phần lớn do yếu tố bên ngoài, CHT khó tác động nhiều

### Cơ chế Learning Loop (sẽ cập nhật confidence tự động)

Hệ thống được thiết kế để **tự cập nhật confidence theo feedback thực tế**. Dưới đây là luồng hoạt động:

```
CHT accept action từ Rule X
        ↓
Hệ thống ghi nhận: rule_id, action, timestamp, metrics tại thời điểm đó
        ↓
2 giờ sau: so sánh metric tương ứng trước và sau
        ↓
Nếu metric tốt lên → positive_outcome += 1
Nếu metric không thay đổi hoặc giảm → outcome_count += 1 (không tăng positive)
        ↓
Confidence mới = (positive_outcomes / outcome_count) × 0.6
                 + initial_confidence × 0.4
        ↓
Rule có feedback tốt nhiều lần → confidence tăng → hiển thị ưu tiên hơn
Rule thường xuyên không hiệu quả → confidence giảm → cảnh báo team nghiệp vụ
```

Hiện tại trong JSON (`feedback_count`, `positive_feedback`, `outcome_count`, `positive_outcomes`) đã có cấu trúc để lưu dữ liệu này. Khi có đủ dữ liệu thực tế từ các store, hệ thống sẽ dùng công thức trên để cập nhật confidence tự động thay vì dùng giá trị cố định.

### Đọc Confidence Score như thế nào?

| Khoảng giá trị | Ý nghĩa | Cách xử lý |
|---|---|---|
| **0.90 – 1.00** | Rất tin cậy — pattern đã được kiểm chứng rõ ràng | Nên áp dụng ngay khi trigger |
| **0.80 – 0.89** | Tin cậy cao — hầu hết trường hợp đều đúng | Nên áp dụng, kiểm tra thêm nếu có gì bất thường |
| **0.70 – 0.79** | Tin cậy trung bình — đúng trong nhiều trường hợp | Cân nhắc kỹ hoàn cảnh cụ thể trước khi áp dụng |
| **0.60 – 0.69** | Cần cẩn thận — còn nhiều biến số | CHT nên xem xét toàn cảnh trước khi quyết định |
| **< 0.60** | Thử nghiệm — chưa đủ cơ sở | Chỉ áp dụng nếu CHT thấy phù hợp với bối cảnh thực tế |

---

*Tài liệu này mô tả trạng thái rule engine tính đến ngày 12/05/2026. Khi có cập nhật rules mới hoặc thay đổi ngưỡng, tài liệu cần được cập nhật tương ứng.*
