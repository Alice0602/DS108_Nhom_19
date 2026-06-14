# 📘 Tài liệu Đặc tả Dữ liệu (Data Dictionary / Code Book)

**Đồ án môn học DS108 — Tiền xử lý và Xây dựng Bộ dữ liệu**

Tài liệu này đặc tả chi tiết cấu trúc, kiểu dữ liệu, nguồn gốc và các ràng buộc chất lượng (QA Constraints) của từng thuộc tính trong bộ dữ liệu **Steam Games (2022-2026)** thành phẩm.

Bộ dữ liệu cuối cùng được tổ chức tối ưu theo nguyên lý chuẩn hóa: chỉ lưu trữ các thuộc tính gốc/độc lập trong tệp CSV, các thuộc tính đạo hàm (derived) được tính toán động (**On-the-fly**) khi chạy ứng dụng hoặc nạp vào mô hình để triệt tiêu hoàn toàn sự trùng lặp ý nghĩa.

---

## 1. Thông tin Tổng quan Bộ dữ liệu
* **Tệp dữ liệu:** `data/processed/steam_games_with_genres.csv`
* **Số lượng bản ghi (Rows):** 3,868 trò chơi độc lập (đã lọc theo điều kiện $\ge 100$ lượt đánh giá).
* **Số lượng cột lưu trữ thực tế (CSV Columns):** 42 cột.
* **Số lượng cột tính toán động (Calculated Columns):** 1 cột (total_ratings).
* **Tổng số thuộc tính sử dụng trên Dashboard/Phân tích:** 43 thuộc tính.

---

## 2. Chi tiết các Thuộc tính (Variables Specification)

| Tên cột (Column Name) | Trạng thái (Storage) | Kiểu dữ liệu (Dtype) | Nguồn (Source) | Ý nghĩa ngữ nghĩa (Description) | Miền giá trị / Ràng buộc QA |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`appid`** | Stored (Lưu trữ) | `int64` | SteamSpy API | Mã định danh duy nhất của trò chơi trên hệ thống Steam. | Khoá chính, duy nhất (Unique), không được khuyết (Non-null), $> 0$. |
| **`name`** | Stored (Lưu trữ) | `string` | SteamSpy + Store | Tên gọi chính thức của trò chơi trên cửa hàng Steam. | Chuỗi ký tự, không được khuyết (Non-null). |
| **`release_date`** | Stored (Lưu trữ) | `date` | Steam Store API | Ngày phát hành chính thức của trò chơi (Định dạng: `YYYY-MM-DD`). | Định dạng ngày hợp lệ, từ `2022-01-01` đến `2026-12-31`. |
| **`year`** | Stored (Lưu trữ) | `Int64` (nullable) | Derived (Trích xuất) | Năm phát hành của trò chơi (được trích xuất từ ngày phát hành). | Số nguyên, nằm trong khoảng $[2022, 2026]$. |
| **`developer`** | Stored (Lưu trữ) | `string` | Merged (Spy + Store) | Tên nhà phát triển trò chơi (đã được đồng bộ và làm sạch giữa hai API). | Chuỗi ký tự, không được khuyết (Non-null). |
| **`publisher`** | Stored (Lưu trữ) | `string` | Merged (Spy + Store) | Tên nhà phát hành trò chơi (đã được đồng bộ giữa hai API). | Chuỗi ký tự, cho phép giá trị rỗng (Nullable). |
| **`price`** | Stored (Lưu trữ) | `float64` | Derived (Store / 100) | Giá bán gốc của trò chơi bằng USD (đã chia 100 để sửa lỗi đơn vị cents). | Số thực, $\ge 0.0$ (USD). |
| **`is_free`** | Stored (Lưu trữ) | `int64` (binary) | Derived (Logic) | Gắn cờ trò chơi miễn phí: `1` là miễn phí, `0` là trả phí. | Nhị phân $\{0, 1\}$. Ràng buộc: `is_free = 1` $\iff$ `price = 0.0`. |
| **`discount`** | Stored (Lưu trữ) | `Int64` (nullable) | Steam Store API | Tỷ lệ phần trăm giảm giá hiện tại của trò chơi. | Số nguyên, nằm trong khoảng $[0, 100]$. |
| **`price_group`** | Stored (Lưu trữ) | `string` (categorical) | Derived (Phân nhóm) | Phân khúc giá của game: `Free`, `<$10`, `$10-30`, `>$30`. | Một trong 4 nhóm phân khúc xác định. |
| **`positive_ratings`**| Stored (Lưu trữ) | `Int64` (nullable) | SteamSpy API | Số lượng đánh giá tích cực (Positive Reviews) từ người chơi. | Số nguyên, $\ge 0$. |
| **`negative_ratings`**| Stored (Lưu trữ) | `Int64` (nullable) | SteamSpy API | Số lượng đánh giá tiêu cực (Negative Reviews) từ người chơi. | Số nguyên, $\ge 0$. |
| **`total_ratings`** | Calculated (Tính động) | `Int64` (nullable) | Derived (Logic) | Tổng số lượng đánh giá tích lũy của trò chơi ($pos + neg$). | Số nguyên. Ràng buộc QA: $\ge 100$ (để loại bỏ dữ liệu nhiễu). |
| **`rating_ratio`** | Stored (Lưu trữ) | `float64` | Derived (Logic) | Tỷ lệ đánh giá tích cực thô: $\frac{\text{positive}}{\text{positive} + \text{negative}}$. | Số thực, nằm trong khoảng $[0.0, 1.0]$. |
| **`wilson_score`** | Stored (Lưu trữ) | `float64` | Derived (Wilson CI) | Giới hạn dưới khoảng tin cậy Wilson Score (95%, z=1.96). Biến Target chính. | Số thực, nằm trong khoảng $[0.0, 1.0]$. |
| **`owners_min`** | Stored (Lưu trữ) | `Int64` (nullable) | SteamSpy API | Cận dưới của lượng người sở hữu game ước lượng từ SteamSpy. | Số nguyên, $\ge 0$. Khuyết (`NaN`) đối với nhóm MNAR `'0 .. 20,000'`. |
| **`owners_max`** | Stored (Lưu trữ) | `Int64` (nullable) | SteamSpy API | Cận trên của lượng người sở hữu game ước lượng từ SteamSpy. | Số nguyên, $\ge$ `owners_min`. |
| **`owners_midpoint`** | Stored (Lưu trữ) | `Int64` (nullable) | Derived (Logic) | Giá trị trung vị của lượng người sở hữu ước lượng: $\frac{\text{min} + \text{max}}{2}$. | Số nguyên, $\ge 0$. Khuyết (`NaN`) đối với nhóm MNAR. |
| **`owners_min_known`**| Stored (Lưu trữ) | `boolean` | Derived (Logic) | Đánh cờ trạng thái khuyết thiếu dữ liệu owners cận dưới. | `True` (nếu lượng owners xác định), `False` (nếu khuyết MNAR). |
| **`ccu`** | Stored (Lưu trữ) | `Int64` (nullable) | SteamSpy API | Lượng người chơi đồng thời đỉnh (Peak Concurrent Users). | Số nguyên, $\ge 0$. Đều bằng `0` (MNAR) đối với các game sau 2023. |
| **`genres`** | Stored (Lưu trữ) | `list[string]` | Steam Store API | Danh sách các nhãn thể loại game được gắn trên Steam. | Chuỗi dạng danh sách các nhãn thể loại hợp lệ. |
| **`genre_X` (22 cột)** | Stored (Lưu trữ) | `int64` (binary) | Derived (One-Hot) | 22 cột nhị phân biểu diễn sự xuất hiện của từng thể loại game độc lập. | Nhị phân $\{0, 1\}$ (Ví dụ: `genre_Indie`, `genre_Action`, v.v.). |

---

## 3. Các Ràng buộc Chất lượng Dữ liệu (QA Rules)

Mỗi lần đường ống dẫn dữ liệu (Data Pipeline) chạy hoặc dữ liệu được cập nhật, bộ dữ liệu bắt buộc phải vượt qua các QA Assertions sau đây để được công nhận đạt chuẩn sạch:

1. **Ràng buộc Khóa chính:** Cột `appid` không được chứa giá trị trùng lặp (`is_unique = True`).
2. **Ràng buộc Miền giá trị:** 
   - `price` không được âm ($\ge 0.0$).
   - `rating_ratio` và `wilson_score` phải nằm trong đoạn $[0.0, 1.0]$.
   - `year` phải thuộc tập số nguyên từ $2022$ đến $2026$.
3. **Ràng buộc Ngưỡng Chất lượng:** Tổng số đánh giá (`positive_ratings` + `negative_ratings`) của từng dòng bắt buộc $\ge 100$.
4. **Ràng buộc Logic Nghiệp vụ:** 
   - Nếu `is_free = 1` thì bắt buộc `price = 0.0`.
   - Lượng người sở hữu cận dưới không được lớn hơn cận trên (`owners_min` $\le$ `owners_max`).
5. **Ràng buộc Khuyết thiếu hệ thống (MNAR):**
   - Game thuộc nhóm owners `'0 .. 20,000'` bắt buộc phải có `owners_min = NaN` và `owners_min_known = False`.
6. **Ràng buộc Mã hóa Thể loại:**
   - Tất cả 22 cột thể loại One-Hot `genre_X` chỉ được phép chứa các giá trị nhị phân $\{0, 1\}$.
