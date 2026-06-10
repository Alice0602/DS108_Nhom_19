# 🎓 BÁO CÁO KHOA HỌC: XÂY DỰNG VÀ KIỂM ĐỊNH BỘ DỮ LIỆU STEAM GAMES (2022-2026)

**Môn học:** DS108 - Tiền xử lý và Xây dựng Bộ dữ liệu  
**Cấu trúc văn bản:** Định dạng IEEE 2-Column Style (Draft)  
**Đơn vị thực hiện:** Nhóm Sinh viên Đồ án Capstone  

---

## 📝 TÓM TẮT (ABSTRACT)
Trong Khoa học Dữ liệu và Kỹ nghệ Học máy, chất lượng dữ liệu đầu vào quyết định trực tiếp đến độ tin cậy của mô hình thống kê (*Garbage In, Garbage Out*). Nghiên cứu này trình bày đường ống dẫn dữ liệu (data pipeline) tự động thu thập và tiền xử lý bộ dữ liệu trò chơi trên Steam được phát hành trong giai đoạn 2022–2026. Chúng tôi tích hợp dữ liệu từ hai nguồn phân mảnh (Steam Store API và SteamSpy API), giải quyết các dị biệt hệ thống như lỗi đơn vị giá (Price Cent Bug), khuyết thiếu dữ liệu hệ thống không ngẫu nhiên (MNAR) đối với thuộc tính thời gian chơi và lượng người sở hữu tối thiểu. Để triệt tiêu thiên lệch do cỡ mẫu nhỏ (*small-sample bias*) của tỷ lệ đánh giá thô, chúng tôi thiết kế thuộc tính mục tiêu bằng giới hạn dưới của khoảng tin cậy Wilson Score (ở mức ý nghĩa 95%). Bộ dữ liệu thành phẩm gồm 3,868 bản ghi đã vượt qua 10 kiểm định chất lượng tự động (QA Assertions). Cuối cùng, chúng tôi thực hiện phân tích thống kê đa biến (Welch's T-test, One-way ANOVA, Pearson/Spearman Correlation, Shapiro-Wilk, và VIF) nhằm kiểm định các giả thuyết về mối liên hệ giữa phân khúc giá, thể loại và mức độ đón nhận của người chơi.

---

## 1. GIỚI THIỆU & ĐỊNH HÌNH BÀI TOÁN (INTRODUCTION & PROBLEM FORMULATION)

### 1.1. Bối cảnh và Động lực
Sự bùng nổ của ngành công nghiệp game kỹ thuật số đi kèm với nhu cầu phân tích hành vi tiêu dùng và định giá sản phẩm. Steam, nền tảng phân phối game PC lớn nhất thế giới, cung cấp kho dữ liệu khổng lồ. Tuy nhiên, dữ liệu thô trích xuất từ các API của Steam bị phân mảnh, nhiễu và chứa nhiều dị biệt hệ thống nghiêm trọng.

### 1.2. Định hình bài toán theo Khung Đồ án (Problem Framing)
Đồ án này được định hình dựa trên sự kết hợp chặt chẽ giữa hai khung tiêu chuẩn:
1.  **Frame 1: Data Integration & Tabular Architecture:** Đối mặt với dữ liệu có cấu trúc từ nhiều API phân mảnh (Steam Store và SteamSpy) có hệ quy chiếu khác biệt, yêu cầu hợp nhất thực thể (Entity Resolution) và chuẩn hóa tiền tệ/ngày phát hành.
2.  **Frame 3: Advanced Data Rescue & Algorithmic Imputation:** Nhận diện và xử lý toán học dữ liệu khuyết thiếu hệ thống diện rộng (MNAR) và thiết kế thuộc tính hiệu chỉnh thống kê (Wilson Score) để xử lý bất cân bằng và nhiễu do cỡ mẫu nhỏ.

---

## 2. KIẾN TRÚC THU THẬP DỮ LIỆU & HỢP NHẤT THỰC THỂ (DATA COLLECTION & ENTITY RESOLUTION)

### 2.1. Đường ống thu thập tự động (Data Pipeline)
Chúng tôi thiết kế kiến trúc thu thập dữ liệu thông qua script Python `scripts/collect_steam_data.py`. Quy trình thực thi gồm các bước:
*   **SteamSpy API:** Lấy danh sách AppIDs phổ biến theo trang (1,000 games/trang) cùng các trường thống kê đánh giá, số người chơi đồng thời (CCU), ước lượng người sở hữu (owners range).
*   **Steam Store API:** Lấy thông tin giá gốc, cờ miễn phí, chi tiết ngày phát hành, và thể loại (genres) của từng AppID. Để tuân thủ chính sách giới hạn tần suất gọi (Rate Limits), chúng tôi đặt độ trễ `REQUEST_DELAY = 1.0` giây giữa các lượt gọi.

### 2.2. Hợp nhất Thực thể (Entity Resolution)
Dữ liệu từ hai API có cấu trúc không đồng nhất và có thể xung đột thông tin (ví dụ: tên trò chơi khác biệt nhỏ, tên nhà phát triển định dạng khác nhau). Chúng tôi thực hiện hợp nhất bằng cách:
1.  Sử dụng thuộc tính khóa chính **`appid`** để thực hiện phép nối inner join (`pd.merge`).
2.  Uu tiên thông tin tên trò chơi (`store_name`) và nhà phát triển từ Steam Store API (do được cập nhật chính thức bởi nhà phát hành trên cửa hàng), đồng thời loại bỏ các thuộc tính dư thừa trùng lặp để giảm thiểu dung lượng lưu trữ của tệp thành phẩm.

---

## 3. TIỀN XỬ LÝ & TÍNH CHẶT CHẼ CỦA PHƯƠNG PHÁP (PREPROCESSING & METHODOLOGICAL RIGOR)

### 3.1. Sửa lỗi đơn vị giá (Price Bug Fix)
Một lỗi dị biệt hệ thống lớn của Steam Store API là thuộc tính giá được trả về dưới dạng **cents** (ví dụ: một tựa game giá $14.99 được lưu dưới dạng số nguyên `1499`). Nếu sử dụng trực tiếp dữ liệu này, phân tích thống kê sẽ bị lạm phát giá trị 100 lần. Chúng tôi áp dụng quy tắc tiền xử lý:
$$\text{Price (USD)} = \frac{\text{initialprice}}{100}$$
Quy trình này khôi phục thành công miền giá trị thực tế của game ($0.00 – $99.99).

### 3.2. Chẩn đoán và xử lý dữ liệu khuyết thiếu hệ thống (MNAR)
Chúng tôi thực hiện chẩn đoán cơ chế khuyết thiếu dữ liệu đối với hai thuộc tính quan trọng:
*   **Thời gian chơi (`average_playtime`):** Dữ liệu thống kê cho thấy thuộc tính này bị khuyết thiếu (bằng 0) đối với **100%** trò chơi phát hành sau năm 2023. Đây là khuyết thiếu hệ thống không ngẫu nhiên (MNAR - Missing Not At Random) xuất phát từ việc API SteamSpy bị ngắt kết nối thu thập thời gian chơi. Việc áp dụng các thuật toán nội suy (imputation) như Mean hay KNN trong trường hợp này sẽ tạo ra dữ liệu giả, sai lệch nghiêm trọng. Quyết định kỹ thuật của chúng tôi là **lược bỏ hoàn toàn cột này** khỏi schema thành phẩm.
*   **Lượng người sở hữu tối thiểu (`owners_min`):** Đối với các game mới hoặc ít phổ biến thuộc nhóm ước lượng `0 .. 20,000` người sở hữu, cận dưới thực tế được trả về từ API là 0, tuy nhiên đây là giá trị ước lượng không đáng tin cậy. Chúng tôi gán lại giá trị này thành `NaN` (khuyết thiếu) và gắn cờ `owners_min_known = False` để minh bạch hóa trạng thái khuyết MNAR đối với các phân tích phía sau.

### 3.3. Hiệu chỉnh toán học Wilson Score để tránh sai lệch cỡ mẫu nhỏ
Tỷ lệ đánh giá tích cực thô được tính bằng:
$$\hat{p} = \frac{\text{positive}}{\text{positive} + \text{negative}}$$
Tuy nhiên, tỷ lệ này gặp sai lệch cỡ mẫu nhỏ (*small-sample bias*). Ví dụ: một game có 1 đánh giá tích cực và 0 đánh giá tiêu cực sẽ có tỷ lệ thô $100\%$, vượt trội hơn một game bom tấn có $9,500$ tích cực và $500$ tiêu cực ($95\%$). 
Để giải quyết triệt để vấn đề này, chúng tôi áp dụng **khoảng tin cậy Wilson Score Interval** ở mức ý nghĩa $95\%$ ($z = 1.96$). Giá trị thuộc tính `wilson_score` làm biến mục tiêu chính là giới hạn dưới của khoảng tin cậy này:
$$w = \frac{\hat{p} + \frac{z^2}{2n} - z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$
Trong đó:
*   $\hat{p}$ là tỷ lệ đánh giá tích cực thô.
*   $n$ là tổng số lượng đánh giá ($positive + negative$).
*   $z = 1.96$ là giá trị phân phối chuẩn tích lũy ở mức tin cậy $95\%$.

Nhờ đó, trò chơi ít đánh giá sẽ bị phạt điểm (ví dụ: game 3 positive/0 negative có Wilson Score $\approx 38\%$, trong khi game 10,000 positive/500 negative có Wilson Score $\approx 94.8\%$).

### 3.4. Đảm bảo nguyên tắc Không rò rỉ dữ liệu (Zero Data Leakage)
Vì đây là bộ dữ liệu Benchmark (Dataset Construction), mọi bước chuẩn hóa (như chia tỷ lệ price hay gán giá trị Wilson Score) đều được thực hiện dựa trên công thức toán học độc lập của từng bản ghi, không sử dụng các tham số tổng thể (như Mean, Max của toàn bộ cột dữ liệu). Điều này đảm bảo **Zero Data Leakage**: bất kỳ mô hình Machine Learning nào sử dụng bộ dữ liệu này đều có thể thực hiện phép chia Train/Test Split sau đó mà không sợ thông tin từ tập Test bị rò rỉ vào tập Train trong quá trình tiền xử lý trước đó.

---

## 4. KHAI PHÁ DỮ LIỆU & KIỂM ĐỊNH THỐNG KÊ (EDA & STATISTICAL VALIDATION)

Chúng tôi thực hiện các kiểm định giả thuyết khoa học trực tiếp trên bộ dữ liệu thành phẩm (3,868 games) để chứng minh tính valid của dữ liệu.

### 4.1. Welch's T-test: Game miễn phí (Free) vs Trả phí (Paid)
*   **Giả thuyết:**
    *   $H_0$: Không có sự khác biệt về điểm Wilson Score trung bình giữa game miễn phí và game trả phí.
    *   $H_1$: Có sự khác biệt có ý nghĩa thống kê về điểm Wilson Score giữa hai nhóm.
*   **Kết quả:** Welch's T-test (cho phép phương sai hai nhóm khác nhau) cho giá trị thống kê $t = -7.38$, trị số $p < 0.001$.
*   **Kết luận:** Bác bỏ $H_0$. Điểm số trung bình của game trả phí cao hơn có ý nghĩa thống kê so với game miễn phí. Chỉ số Cohen's $d \approx -0.25$ chỉ ra sức tác động ở mức nhỏ (small effect size).

### 4.2. One-way ANOVA: Khác biệt điểm số giữa các phân khúc giá
*   **Giả thuyết:** Điểm Wilson Score trung bình đồng nhất giữa các nhóm phân khúc giá (`Free`, `<$10`, `$10-30`, `>$30`).
*   **Kết quả:** Giá trị thống kê $F = 22.84$, $p < 0.001$.
*   **Kết luận:** Bác bỏ giả thuyết đồng nhất. Có sự khác biệt đáng kể về mức độ hài lòng của người dùng giữa các mức giá bán khác nhau. Chỉ số lực tác động $\eta^2$ chỉ ra phân khúc giá giải thích khoảng $2.2\%$ biến thiên của điểm Wilson Score.

### 4.3. Kiểm định tính phân phối chuẩn (Shapiro-Wilk)
Chúng tôi kiểm định tính phân phối chuẩn của các biến số chính. Kết quả kiểm định Shapiro-Wilk trên thuộc tính `wilson_score` cho giá trị $p < 0.001$, bác bỏ giả thuyết phân phối chuẩn. 
*   *Biện luận khoa học:* Mặc dù Shapiro-Wilk bác bỏ giả thuyết phân phối chuẩn (do tính chất cực kỳ nhạy cảm của thuật toán này khi cỡ mẫu lớn $N > 3000$), định lý Giới hạn Trung tâm (Central Limit Theorem - CLT) đảm bảo rằng phân phối của các số trung bình nhóm sẽ hội tụ về phân phối chuẩn do cỡ mẫu của chúng ta cực kỳ lớn ($n \gg 30$). Vì vậy, các kiểm định tham số như Welch's T-test và ANOVA vẫn giữ nguyên tính vững và độ tin cậy khoa học.


### 4.4. Kiểm định đa cộng tuyến (VIF)
Chúng tôi chạy kiểm định hệ số phóng đại phương sai (VIF - Variance Inflation Factor) trên các cột thể loại mã hóa một-hot (One-Hot Encoded Genres). Kết quả cho thấy hệ số VIF của tất cả các cột thể loại đều $< 1.5$ (dưới ngưỡng cảnh báo là 5.0). Điều này xác nhận các thể loại game không bị đa cộng tuyến, hoàn toàn phù hợp để làm các đặc trưng độc lập trong mô hình dự báo.

---

## 5. CHUẨN MỰC KỸ THUẬT & KHẢ NĂNG TÁI LẬP (ENGINEERING & REPRODUCIBILITY)

Để đạt chuẩn mực kỹ thuật công nghiệp, toàn bộ quy trình tiền xử lý được lập trình hóa hoàn toàn (không thao tác thủ công qua Excel).
*   **requirements.txt:** Quản lý toàn bộ thư viện phụ thuộc chặt chẽ.
*   **QA Assertions:** Tích hợp bộ 10 quy tắc assertions tự động kiểm tra tính toàn vẹn của dữ liệu mỗi khi chạy pipeline.
*   **Auditor Script (`scripts/audit_project.py`):** Script độc lập kiểm tra tự động kiểu dữ liệu thực tế so với đặc tả trong Code Book, tìm kiếm các cảnh báo logic để ngăn chặn lỗi dữ liệu phát sinh ngoài ý muốn.

---

## 6. ĐẠO ĐỨC AI & GIỚI HẠN BỘ DỮ LIỆU (AI ETHICS & DATASET LIMITATIONS)

### 6.1. Bias và Tính công bằng (Dataset Bias)
Bộ dữ liệu có sự thiên lệch tự nhiên về phía các game thành công thương mại hoặc có lượng người chơi tích cực nhất định, do chúng tôi áp đặt điều kiện lọc chất lượng tối thiểu $100$ lượt đánh giá để loại bỏ nhiễu. Điều này có nghĩa là các nghiên cứu sử dụng bộ dữ liệu này không nên đại diện cho toàn bộ các dự án game indie siêu nhỏ (solo-developer) có ít hơn 100 đánh giá.

### 6.2. Bản quyền và Quyền riêng tư (Licensing & Privacy)
Tất cả các dữ liệu được thu thập đều nằm trong phạm vi công khai được cung cấp bởi các API chính thức của Valve (Steam Store) và SteamSpy. Bộ dữ liệu không chứa bất kỳ thông tin nhận dạng cá nhân nào (PII) của người dùng, đảm bảo tuân thủ đầy đủ luật bảo vệ quyền riêng tư (GDPR/CCPA).

---

## PHỤ LỤC: DATASHEET FOR DATASET (GEBRU ET AL., 2021)

### 1. Motivation (Động lực)
*   *Q: Bộ dữ liệu được tạo ra với mục đích gì?*  
    *A:* Hỗ trợ nghiên cứu học thuật về xu hướng định giá, phân phối thể loại và player satisfaction của game trên nền tảng Steam giai đoạn 2022–2026.

### 2. Composition (Thành phần)
*   *Q: Mỗi thực thể đại diện cho cái gì?*  
    *A:* Một tựa game PC độc lập được phân phối trên Steam có ít nhất 100 ratings.
*   *Q: Bộ dữ liệu có chứa dữ liệu khuyết thiếu không?*  
    *A:* Có, cột `publisher` cho phép Nullable. Cột `owners_min` bị khuyết MNAR đối với nhóm dưới 20k người sở hữu và được đánh dấu bằng `NaN`. Cột `average_playtime` bị khuyết MNAR hoàn toàn và đã bị lược bỏ.

### 3. Collection Process (Quy trình thu thập)
*   *Q: Dữ liệu được thu thập như thế nào?*  
    *A:* Sử dụng API SteamSpy và Steam Store qua script Python tự động.
*   *Q: Thời gian thu thập là khi nào?*  
    *A:* Tháng 5 năm 2026.

### 4. Preprocessing/Cleaning/Labeling (Tiền xử lý & Làm sạch)
*   *Q: Có tài liệu hóa các bước làm sạch không?*  
    *A:* Có, chi tiết các bước được thực hiện trong Notebook `02_data_cleaning_and_imputation.ipynb`. Dữ liệu thô ban đầu được lưu trữ nguyên bản tại `data/raw/steam_games_raw.csv`.

### 5. Uses (Mục đích sử dụng)
*   *Q: Bộ dữ liệu này có được sử dụng cho nhiệm vụ cụ thể nào không?*  
    *A:* Được dùng để phân tích EDA và thực thi các kiểm định thống kê ANOVA, T-test trên Dashboard Streamlit của dự án.

### 6. Distribution (Phân phối)
*   *Q: Giấy phép sử dụng của bộ dữ liệu là gì?*  
    *A:* MIT License.
