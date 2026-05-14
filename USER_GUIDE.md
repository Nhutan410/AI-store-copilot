# Hướng Dẫn Sử Dụng — AI Store Copilot PNJ

> **Dành cho:** Cửa hàng trưởng (CHT) và người dùng không có nền tảng kỹ thuật
> **Mục đích:** Giúp bạn hiểu app làm gì, dùng như thế nào, và khai thác tối đa các tính năng

---

## AI Store Copilot là gì?

AI Store Copilot là một **trợ lý AI chạy trực tiếp trên máy tính nội bộ**, không cần internet, không gửi dữ liệu ra ngoài. Nó đọc toàn bộ dữ liệu bán hàng của cửa hàng bạn (doanh thu, traffic, nhân viên, SKU...) và:

- **Tự động phát hiện vấn đề** mà bạn có thể bỏ sót khi nhìn vào bảng số
- **Giải thích nguyên nhân** bằng tiếng Việt thông thường, không cần bạn biết phân tích data
- **Đề xuất hành động cụ thể** với lý do rõ ràng, bạn quyết định có làm theo hay không
- **Trả lời câu hỏi** bất kỳ về tình hình cửa hàng ngay lập tức

---

## Màn hình chính — Bố cục chung

Khi mở app, bạn thấy 2 phần:

```
┌─────────────────────┬─────────────────────────────────────────────┐
│   SIDEBAR (trái)    │           NỘI DUNG CHÍNH (phải)             │
│                     │                                             │
│ 💎 AI Store Copilot │   [Nội dung của trang đang xem]            │
│                     │                                             │
│ Chọn cửa hàng ▼     │                                             │
│ STR-002 · PNJ...    │                                             │
│                     │                                             │
│ 📍 TP.HCM | Phân    │                                             │
│    khúc A           │                                             │
│ 🎯 Target: 92M đ    │                                             │
│                     │                                             │
│ ─── Điều hướng ─── │                                             │
│ 🏠 Dashboard        │                                             │
│ 💬 Chat Copilot     │                                             │
│ ☀️ Họp Ca Sáng      │                                             │
│ ⚡ Actions & Rules  │                                             │
│ 📊 Analytics 30 Ngày│                                             │
│ 🔔 Thông Báo        │                                             │
│                     │                                             │
│ 🟢 Ollama kết nối   │                                             │
└─────────────────────┴─────────────────────────────────────────────┘
```

**Sidebar luôn hiển thị:**
- **Chọn cửa hàng** → Khi bạn chọn store khác, toàn bộ dữ liệu trong app thay đổi theo
- **6 nút điều hướng** → Chuyển qua lại giữa các trang
- **Trạng thái Ollama** → 🟢 = AI đang hoạt động | 🔴 = AI offline (dữ liệu vẫn xem được)

---

## Trang 1 — 🏠 Dashboard (Tổng quan)

**Dùng khi nào:** Mỗi buổi sáng khi mở app lần đầu, hoặc bất cứ lúc nào muốn xem nhanh tình hình.

### Phần 1: 5 chỉ số KPI (hàng đầu tiên)

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Điểm Sức     │ │ % Target     │ │ Tỷ lệ Chuyển │ │ Traffic      │ │ AOV Trung    │
│ Khỏe         │ │ Hôm Qua      │ │ đổi           │ │ Khách        │ │ bình         │
│              │ │              │ │               │ │              │ │              │
│  75/100      │ │  79.2%       │ │  19.3%        │ │  114         │ │  3.31M đ     │
│  Hạng B      │ │  72.8M/92M đ │ │  -11.6pp vs   │ │  -18.5% vs   │ │  38 giao dịch│
│              │ │              │ │  baseline     │ │  baseline    │ │              │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

**Đọc số liệu này như thế nào:**

| Chỉ số | Ý nghĩa | Tốt khi nào |
|---|---|---|
| **Điểm Sức Khỏe** | Tổng điểm 5 tiêu chí: doanh thu, CR, traffic, sản phẩm, nhân viên | A ≥85 | B ≥70 | C ≥55 | D <55 |
| **% Target** | Doanh thu hôm qua đạt bao nhiêu % mục tiêu ngày | ≥ 95% = tốt |
| **Tỷ lệ Chuyển đổi (CR)** | Cứ 100 khách vào, bao nhiêu người mua | Cao hơn baseline = tốt |
| **Traffic** | Số lượt khách vào cửa hàng hôm qua | So sánh với baseline 14 ngày |
| **AOV** | Giá trị trung bình mỗi đơn hàng | Cao = tốt, đặc biệt nếu CR cao |

### Phần 2: Health Score Gauge + Cảnh báo

**Vòng đo sức khỏe** (bên trái): Hiển thị điểm tổng và breakdown 5 thành phần. Mỗi thành phần cho thấy bạn đang mạnh/yếu ở đâu.

**Cảnh báo đang kích hoạt** (bên phải): Đây là phần quan trọng nhất.

```
⚡ Cảnh Báo Đang Kích Hoạt (6)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 KHẨN  Pace revenue chậm sau giữa ngày
         Pace đến trưa ước tính 28% target (ngưỡng 38%)
         Tin cậy: 88% | Actions: alert_manager, mini_activation...

🔴 KHẨN  Dự báo miss target cuối ngày
         Ước tính pace 16h chỉ đạt 49% target
         ...
```

Mỗi cảnh báo có:
- **Màu đỏ/vàng/xanh** → Mức độ khẩn cấp
- **Mô tả ngắn** → Vấn đề là gì, số liệu cụ thể
- **Độ tin cậy** → AI tự tin bao nhiêu % về cảnh báo này

### Phần 3: Biểu đồ doanh thu 7 ngày + Cơ cấu sản phẩm

- **Cột xanh** → Ngày đạt ≥95% target
- **Cột vàng** → Ngày đạt 80–95% target
- **Cột đỏ** → Ngày dưới 80% target
- **Đường vàng đứt** → Target ngày

**Biểu đồ tròn** bên phải cho thấy hôm qua bán được gì nhiều nhất. Nhẫn cưới (vàng) nên chiếm nhiều nhất vì margin cao nhất.

### Phần 4: AI phân tích (2 nút bên dưới)

**📝 Tạo Báo Cáo AI:**
- AI đọc toàn bộ dữ liệu hôm qua và viết báo cáo bằng tiếng Việt
- Gồm: kết quả ngày, điểm mạnh, điểm yếu, 3 gợi ý hành động
- Thời gian: 15–60 giây (tùy model)
- Kết quả được **lưu cache** → không cần tạo lại khi đóng/mở

**🔎 Tạo Phân tích Nguyên nhân:**
- AI giải thích CÁC LÝ DO cụ thể tại sao hôm qua đạt/miss target
- Phân tích mối quan hệ nhân quả (VD: Bảo Ngọc ở ca sáng → thiếu NV wedding ca chiều → nhẫn cưới thấp → miss target)

> ⚠️ Nếu nút bị mờ (disabled): Ollama đang offline. Kiểm tra `ollama serve` trong terminal.

### Phần 5: Dự báo + Đội hình

**Dự báo doanh thu:** Ước tính con số cuối ngày dựa trên pace hiện tại. Màu xanh = đang đi đúng hướng, màu đỏ = cần can thiệp.

**Đội hình hôm nay:** Xem ai đang làm ca gì. Senior hiển thị màu xanh, Mid vàng, Junior cam.

---

## Trang 2 — 💬 Chat Copilot

**Dùng khi nào:** Bất cứ lúc nào bạn có câu hỏi cụ thể về cửa hàng.

### Cách dùng

**Cách 1 — Click câu hỏi gợi ý:**

```
💡 Câu hỏi gợi ý
──────────────────────────────────────────────────────
│ Vì sao hôm qua nhẫn cưới bán chậm?          │
│ Ca chiều hôm qua ổn không?                   │
│ Nhân viên nào hiệu quả nhất hôm qua?         │
│ So với baseline, tỷ lệ chuyển đổi thế nào?   │
│ Hôm nay nên focus vào SKU nào?               │
│ Nếu giữ đội hình này đến 20h có đạt target?  │
│ Nhóm khách nữ độc thân đang chiếm bao nhiêu? │
│ Bảo Ngọc hôm qua làm ca nào và kết quả?      │
```

**Cách 2 — Tự nhập câu hỏi:**
Gõ bất kỳ câu hỏi nào vào ô phía dưới và bấm "Gửi ➤"

### Ví dụ hội thoại thực tế

```
CHT: Vì sao hôm qua nhẫn cưới bán chậm?

AI:  Hôm qua nhẫn cưới chỉ đạt 11.7% doanh thu, thấp hơn đáng kể 
     so với ngưỡng lý tưởng 32-40%. Có 2 nguyên nhân chính:

     1. ĐỘI HÌNH CA CHIỀU: Ca chiều (14h-20h) chỉ có 1 NV có 
     strong category nhẫn cưới. Trong khi đó, Bảo Ngọc (senior 
     wedding, CR 52%) và Thu Hương (mid wedding, CR 44%) đều ở 
     ca khác.

     2. MẤT CƠ HỘI VỚI KHÁCH COUPLE: Có 18% lượt traffic là cặp 
     đôi (20 lượt) nhưng nhẫn cưới chỉ bán 2 đơn. Tỷ lệ chuyển 
     đổi từ couple sang nhẫn cưới quá thấp.

     Gợi ý: Hôm nay ca chiều đã có Bảo Ngọc và Thu Hương — hãy 
     ưu tiên để 2 NV này tiếp cặp đôi ngay từ lúc 14h.
```

### Lưu ý về Chat

- Lịch sử chat **lưu lại theo store** — đóng app rồi mở lại vẫn còn
- Bấm **🗑️ Xóa lịch sử chat** để bắt đầu cuộc hội thoại mới
- AI luôn **dựa trên số liệu thực tế** — không bịa số. Nếu không có dữ liệu, AI sẽ nói rõ

---

## Trang 3 — ☀️ Họp Ca Sáng

**Dùng khi nào:** Mỗi sáng trước khi mở cửa, hoặc khi họp với team.

### Bố cục trang

**Cột trái (3/5 màn hình):**

1. **Kết quả hôm qua** — 4 số liệu lớn: doanh thu, traffic, CR, health score. Đọc nhanh trong 10 giây.

2. **3 Ưu tiên hôm nay** — AI (hoặc rule engine) xác định 3 việc quan trọng nhất phải làm hôm nay, sắp xếp theo mức độ khẩn cấp.

3. **Top SKU cần đẩy hôm nay** — 3 sản phẩm được chọn dựa trên: tồn kho sẵn có + CVR lịch sử cao + margin tốt. Đây là sản phẩm team nên chủ động recommend cho khách.

**Cột phải (2/5 màn hình):**

4. **Đội hình hôm nay** — Ai làm ca gì. 🔥 đánh dấu ca cao điểm 14h-20h.

5. **Cần lưu ý** — 1-2 cảnh báo quan trọng nhất từ rule engine, hiển thị ngắn gọn.

### AI Soạn Brief — đọc cho team nghe

Bấm **✍️ AI Soạn Brief** → AI viết đoạn văn 2-3 phút cho CHT đọc thành tiếng trong cuộc họp ca sáng. Format tự nhiên, như đang nói chuyện thật.

Sau khi có brief:
- **⬇️ Tải Brief** → Download file `.txt` để lưu hoặc gửi lên Zalo team
- **🔄 Tạo lại Brief** → Nếu muốn AI viết lại với cách diễn đạt khác

**Mẫu brief AI viết:**

```
Chào cả team! Hôm qua mình đạt 72.8 triệu, chỉ bằng 79% target —
cần nỗ lực hơn hôm nay. Điểm sáng là Nguyễn Phương Thảo và 
Võ Thanh Tùng đã rất cố gắng, nhưng ca chiều nhẫn cưới thấp 
là vấn đề chính cần khắc phục.

Hôm nay target vẫn là 92 triệu. 3 ưu tiên:
1. Ca chiều: Bảo Ngọc và Thu Hương tập trung tiếp khách cặp đôi 
   ngay từ 14h, đừng để họ đứng quầy khác.
2. Chủ động recommend NC-156 và NC-218 cho couple —
   tồn kho đang nhiều, CVR tốt.
3. Cuối tháng rồi: gợi ý trả góp 0% ngay khi khách do dự về giá.

Nào, cùng làm tốt hôm nay nhé! 💪
```

---

## Trang 4 — ⚡ Actions & Rules

**Dùng khi nào:** Khi muốn quyết định có thực hiện theo gợi ý AI không, và xem lịch sử feedback.

### Tab 1: Actions Hôm Nay

Đây là danh sách **hành động cụ thể** được đề xuất dựa trên vấn đề phát hiện hôm nay.

```
🔴 KHẨN — Nhẫn cưới yếu trong cao điểm (tin cậy 85%)
├── Nguyên nhân phát hiện:
│   Nhẫn cưới đạt 11.7% doanh thu (ngưỡng 32%), 1 NV mạnh 
│   wedding ở ca chiều.
│
├── Lý do (WHY):
│   Nhẫn cưới chiếm 40–50% doanh thu lý tưởng. Thiếu người + 
│   thiếu focus SKU đồng thời là nguyên nhân số 1 miss target.
│
└── Hành động đề xuất:
    🏷️ Tập trung tư vấn SKU nhẫn cưới CVR cao
    👥 Bổ sung NV mạnh vào ca cao điểm
    
    [ ✅ Chấp nhận ]  [ ⏭️ Bỏ qua ]
```

**Khi bạn bấm ✅ Chấp nhận:**
- Hệ thống ghi lại quyết định của bạn
- Thêm 1 thông báo vào trang Notifications
- Rule đó tăng confidence score (AI học rằng bạn tin nó)

**Khi bạn bấm ⏭️ Bỏ qua:**
- Hệ thống cũng ghi lại (không phải bỏ qua mà không có lý do)
- Confidence score không tăng

> **Mẹo:** Càng feedback nhiều, AI càng hiểu store của bạn và đề xuất chính xác hơn.

### Tab 2: Toàn Bộ Rules

Xem 12 rules của hệ thống: rule nào đang kích hoạt, confidence hiện tại, và lịch sử feedback.

- **🔴 Đang kích hoạt** = Rule này đang thấy vấn đề hôm nay
- **🟢 Không kích hoạt** = Điều kiện của rule này chưa xảy ra hôm nay

### Tab 3: Lịch Sử Feedback

Xem bạn đã accept hay skip bao nhiêu actions, rule nào được dùng nhiều nhất, confidence score đang tăng hay giảm.

Biểu đồ confidence giúp bạn thấy: rule nào đang được tin tưởng nhất sau thực tiễn.

---

## Trang 5 — 📊 Analytics 30 Ngày

**Dùng khi nào:** Phân tích xu hướng, so sánh hiệu suất, tìm pattern theo tuần/tháng.

### Tab 1: Xu Hướng

**Biểu đồ 1 — Doanh thu vs Target 30 ngày:**

```
M đ
120┤                           ▐█
100┤   ██       ██    ██       ██      ██
 92┤···▐█·······▐█····▐█·······▐█······▐█·· Target
 80┤ ███ ██   ███       ██   ███       ██
 60┤
   └────────────────────────────────────► ngày
    01  05  10  15  20  25  30
    
 Xanh = đạt ≥95% | Vàng = 80-95% | Đỏ = dưới 80%
```

→ Nhìn pattern: Cuối tuần (Thứ 7/CN) cột thường cao hơn. Thứ 2 thường thấp. Đầu tháng cao hơn cuối tháng.

**Biểu đồ 2 — Tỷ lệ CR + Biểu đồ 3 — Traffic:**
So sánh với baseline (đường đứt). Nếu CR thấp hơn baseline trong nhiều ngày liên tiếp → vấn đề hệ thống, không phải ngẫu nhiên.

**Biểu đồ 4 — Cơ cấu doanh thu theo danh mục (stacked bar):**
Thấy ngay ngày nào nhẫn cưới (vàng) chiếm nhiều, ngày nào bông tai/lắc (giá thấp) chiếm nhiều.

**Heatmap — Store Health Timeline:**
Màu càng xanh = ngày đó càng tốt. Nhìn ngang thấy pattern theo tuần. Ô đỏ là ngày cần phân tích nguyên nhân.

### Tab 2: Hiệu Suất Nhân Viên

**Ma Trận Hiệu Suất (scatter plot):**
- Trục X: Số đơn trung bình mỗi ngày (NV bận rộn không?)
- Trục Y: Doanh thu trung bình mỗi ngày (NV bán được nhiều không?)
- Kích thước bong bóng: Tổng doanh thu 30 ngày
- Màu: 🟢 Senior | 🟡 Mid | 🟠 Junior

NV **tốt nhất** = bong bóng lớn, màu xanh, ở **góc trên phải** (nhiều đơn + doanh thu cao).

**Bảng chi tiết:** Sắp xếp theo tổng doanh thu, thấy rõ ai đang đóng góp nhiều nhất.

**SKU Opportunity Score:**
Danh sách sản phẩm đang bị bỏ lỡ — tồn kho nhiều, khách hay mua (CVR cao), margin tốt nhưng 7 ngày chưa bán được. Đây là các sản phẩm cần **trưng bày nổi bật** hoặc **chủ động recommend** hơn.

### Tab 3: So Sánh Chuỗi

So sánh cửa hàng của bạn với **tất cả cửa hàng cùng phân khúc** (A/B/C).

```
                  Cửa hàng tôi  |  Trung bình phân khúc A
──────────────────────────────────────────────────────────
% Target              79.2%    |    88.8%         → thấp hơn -9.6%
CR                    19.3%    |    19.0%         → cao hơn +0.3%
Traffic               114      |    116           → thấp hơn -2
AOV                   3.31M    |    3.56M         → thấp hơn -250K
```

→ Thấy ngay mình đang mạnh/yếu ở đâu so với các store cùng loại.

---

## Trang 6 — 🔔 Thông Báo

**Dùng khi nào:** Xem lại tất cả thông báo AI đã gửi, hoặc tạo thông báo demo theo mốc thời gian.

### Feed thông báo

Thông báo hiển thị theo thứ tự thời gian, mới nhất lên trên. Mỗi thông báo có:

```
⚠️ [Cảnh báo]  Cảnh báo trước cao điểm 15:30          2026-04-30 15:30:00  
───────────────────────────────────────────────────────
Dự báo traffic 17h-20h hôm nay: 45-55 lượt (thấp hơn 
10% do thời tiết âm u). ⚠️ RULE-01 kích hoạt: Nhẫn cưới 
đang thấp — cần push ngay khi ca chiều bắt đầu. ✅ Đội 
hình tốt: Bảo Ngọc + Thu Hương sẵn sàng ở ca chiều.

[ Đánh dấu đọc ]
```

**4 loại thông báo:**
- ⚠️ **Cảnh báo** (đỏ) — Vấn đề cần xử lý ngay
- 💡 **Gợi ý** (vàng) — Đề xuất hành động
- 📊 **Tổng kết** (xanh lá) — Báo cáo theo mốc thời gian
- ❤️ **Sức khỏe** (xanh) — Điểm health score

### Tạo thông báo demo

Bấm **➕ Tạo Thông Báo Demo** → Chọn mốc thời gian:

| Thời điểm | Nội dung |
|---|---|
| **📊 07:30** | Tóm tắt kết quả hôm qua + 3 gợi ý cho hôm nay |
| **📈 11:30** | Tiến độ giữa ca + điều chỉnh nhỏ nếu cần |
| **⚡ 15:30** | Cảnh báo trước giờ cao điểm 17h-20h |
| **🌙 21:15** | Tổng kết cuối ngày + bài học |

Bấm **📌 Tạo thông báo mẫu không cần AI** → Tạo 4 thông báo mẫu có sẵn nội dung (không cần Ollama).

---

## Kịch bản demo theo ngày làm việc

### 07:45 — Sáng sớm, mở Dashboard

1. Mở app → **Dashboard**
2. Xem ngay: Health Score + % target hôm qua
3. Đọc **cảnh báo đang kích hoạt** (không cần đọc hết, xem 1-2 cái quan trọng nhất)
4. Bấm **📝 Tạo Báo Cáo AI** nếu muốn tóm tắt đầy đủ

### 08:15 — Trước cuộc họp ca sáng

1. Chuyển sang **☀️ Họp Ca Sáng**
2. Xem **Kết quả hôm qua** + **3 ưu tiên** + **Đội hình hôm nay**
3. Bấm **✍️ AI Soạn Brief** → Có đoạn văn đọc cho team
4. Tải brief nếu cần gửi Zalo

### 11:30 — Giữa ca, check tiến độ

1. Chat → Hỏi: *"Tiến độ sáng nay đang ổn không?"*
2. Hoặc vào Dashboard xem lại KPI realtime (nếu data được cập nhật)

### 15:00 — Trước giờ cao điểm

1. Chuyển sang **⚡ Actions & Rules**
2. Xem actions nào đang kích hoạt cho chiều nay
3. Bấm **✅ Chấp nhận** cho actions bạn muốn thực hiện
4. Quyết định phân ca / focus SKU cho 17h-20h

### Cuối tuần — Phân tích tổng thể

1. Mở **📊 Analytics 30 Ngày**
2. Xem biểu đồ revenue trend: tuần này so với tuần trước
3. Tab **Hiệu Suất NV**: ai đang improve, ai cần hỗ trợ
4. Tab **So Sánh Chuỗi**: store mình đang ở đâu so với phân khúc

---

## Câu hỏi thường gặp

**Q: Dữ liệu lấy từ đâu?**
A: Từ hệ thống POS và dữ liệu nội bộ PNJ. Trong phiên bản POC này, dữ liệu được mô phỏng realistic. Phiên bản production sẽ kết nối trực tiếp với database thực.

**Q: AI có tự gửi lệnh hay thực hiện hành động gì không?**
A: Không. AI chỉ **đề xuất**, **CHT quyết định** có thực hiện không. Tất cả hành động thực tế (điều chuyển nhân viên, thay đổi trưng bày...) vẫn do con người làm.

**Q: Nếu Ollama offline thì sao?**
A: App vẫn hoạt động bình thường — bạn vẫn xem được tất cả dữ liệu, biểu đồ, cảnh báo. Chỉ các nút "Tạo báo cáo AI", "Chat", "Soạn Brief" bị tắt. Banner cảnh báo màu vàng xuất hiện ở đầu trang.

**Q: Tại sao AI mất 30-60 giây để trả lời?**
A: Vì AI chạy local trên máy (không dùng cloud). Model qwen2.5:7b cần thời gian xử lý. Kết quả được cache — lần sau xem lại tức thì.

**Q: Có thể đặt câu hỏi bằng tiếng Anh không?**
A: Được, nhưng AI sẽ trả lời bằng tiếng Việt. Hỏi tiếng Việt sẽ cho kết quả tốt hơn vì prompt được tối ưu cho tiếng Việt.

**Q: Khi nào nên không tin vào đề xuất của AI?**
A: Khi AI đề xuất điều mà bạn biết rõ là không phù hợp với tình huống thực tế (VD: khách đang đông bất thường vì sự kiện khu vực mà hệ thống chưa biết). Hãy skip action đó và AI sẽ học từ feedback của bạn.

**Q: Dữ liệu có bị gửi ra ngoài internet không?**
A: Không. Ollama chạy local hoàn toàn. Dữ liệu cửa hàng không rời khỏi máy tính.

---

## Bảng tham chiếu nhanh — Màu sắc & Ký hiệu

| Màu/Ký hiệu | Ý nghĩa |
|---|---|
| 🟢 Xanh lá | Tốt / Đạt / Online |
| 🟡 Vàng | Cần chú ý / Trung bình |
| 🔴 Đỏ | Vấn đề / Nguy hiểm / Offline |
| A (xanh) | Health Grade A — Tuyệt vời |
| B (vàng) | Health Grade B — Ổn, cần cải thiện một số điểm |
| C (cam) | Health Grade C — Có vấn đề đáng lo ngại |
| D (đỏ) | Health Grade D — Cần can thiệp ngay |
| 🔴 KHẨN | Action cần làm trong vài giờ |
| 🟡 Quan trọng | Action nên làm trong ngày |
| 🟢 Tham khảo | Action có thể cân nhắc |
| [SENIOR] xanh | Nhân viên cấp cao, ưu tiên ca cao điểm |
| [MID] vàng | Nhân viên trung cấp |
| [JUN] cam | Nhân viên mới, cần ghép cặp với senior |

---

*Phiên bản POC — PNJ AI Store Copilot | Powered by Ollama + qwen2.5:7b*
