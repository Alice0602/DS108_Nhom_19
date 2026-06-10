# Datasheet cho Bộ dữ liệu Steam Games (2022-2026)

*Tài liệu Datasheet này tuân thủ theo khung đặc tả (framework) đề xuất bởi Gebru et al. (2021) để minh bạch hóa và chuẩn hóa tài liệu bộ dữ liệu trong Khoa học Dữ liệu.*

---

## 1. Motivation (Động lực hình thành bộ dữ liệu)

*   **Tại sao bộ dữ liệu này được xây dựng?**  
    Bộ dữ liệu được xây dựng nhằm mục đích nghiên cứu các xu hướng phát hành game, cấu trúc phân khúc giá (pricing) và mức độ đón nhận của người dùng đối với các tựa game được phát hành trên nền tảng Steam trong giai đoạn từ năm 2022 đến năm 2026. Các bộ dữ liệu Steam hiện có trên mạng thường đã lỗi thời hoặc gặp các lỗi dữ liệu thô nghiêm trọng (như lỗi đơn vị giá cents-USD hoặc khuyết thiếu thông tin playtime).
*   **Ai là người xây dựng bộ dữ liệu?**  
    Được xây dựng bởi nhóm sinh viên thực hiện đồ án cuối kỳ môn DS108 (Capstone Project).
*   **Đơn vị nào tài trợ cho việc xây dựng bộ dữ liệu này?**  
    Không có đơn vị tài trợ tài chính bên ngoài. Đây hoàn toàn là một dự án nghiên cứu học thuật phục vụ môn học.

---

## 2. Composition (Thành phần bộ dữ liệu)

*   **Các thực thể (instances) trong bộ dữ liệu đại diện cho điều gì?**  
    Mỗi dòng (bản ghi) đại diện cho một tựa game độc lập được phát hành chính thức trên cửa hàng Steam từ năm 2022 đến năm 2026 và đã tích lũy được tối thiểu 100 lượt đánh giá từ người dùng.
*   **Tổng số lượng thực thể trong bộ dữ liệu là bao nhiêu?**  
    3,868 thực thể.
*   **Bộ dữ liệu này chứa toàn bộ các thực thể hay chỉ là một tập mẫu (sample)?**  
    Bộ dữ liệu này là một tập con của toàn bộ các game được phát hành trên Steam trong giai đoạn này, được lọc theo điều kiện biên (threshold) chất lượng là phải có tối thiểu 100 lượt đánh giá để loại bỏ các dữ liệu nhiễu (noise) từ các game thử nghiệm hoặc không có lượt chơi thực tế.
*   **Các đặc trưng (features) cốt lõi của bộ dữ liệu là gì?**  
    Bộ dữ liệu bao gồm 21 đặc trưng chính (bao gồm `appid`, `name`, `developer`, `publisher`, `release_date`, `year`, `positive_ratings`, `negative_ratings`, `total_ratings`, `rating_ratio`, `wilson_score`, `price`, `is_free`, `discount`, `price_group`, `owners_min_known`, `owners_min`, `owners_max`, `owners_midpoint`, `ccu`, `genres`) và 22 cột nhị phân biểu diễn các thể loại game đã được mã hóa dạng `One-Hot Encoding`.
*   **Bộ dữ liệu có chứa dữ liệu khuyết thiếu (missing values) không?**  
    Có, trường thông tin `publisher` chứa một số lượng nhỏ các giá trị khuyết thiếu và được chấp nhận dạng Nullable. Trường thông tin về thời gian chơi trung bình (`average_playtime`) bị khuyết thiếu hệ thống hoàn toàn cho các game sau năm 2023 (`Missing Not At Random - MNAR` do giới hạn kỹ thuật của API) và đã được chủ động lược bỏ khỏi bộ dữ liệu thành phẩm để tránh gây thiên lệch (bias) trong phân tích thống kê.
*   **Bộ dữ liệu có chứa thông tin bảo mật hay nhạy cảm không?**  
    Không. Tất cả thông tin trong bộ dữ liệu này đều là dữ liệu công khai trên cửa hàng Steam Store và hệ thống SteamSpy APIs.

---

## 3. Collection Process (Quy trình thu thập dữ liệu)

*   **Dữ liệu được thu thập bằng cách nào?**  
    Dữ liệu được thu thập tự động thông qua một script Python (`scripts/collect_steam_data.py`) gọi trực tiếp đến **SteamSpy API** (để lấy số lượng đánh giá và CCU) và **Steam Store API** (để lấy ngày phát hành, giá và các thể loại game).
*   **Dữ liệu được thu thập vào thời gian nào?**  
    Được thu thập vào tháng 5 năm 2026.
*   **Bộ dữ liệu bao quát khung thời gian phát hành nào của game?**  
    Bộ dữ liệu bao gồm các game có ngày phát hành chính thức từ 01/01/2022 đến ngày 31/12/2026 (bao gồm cả các game sắp phát hành đã đăng ký trên hệ thống của Steam trong năm 2026).

---

## 4. Preprocessing/Cleaning/Labeling (Tiền xử lý/Làm sạch/Gán nhãn)

*   **Những quy trình tiền xử lý và làm sạch nào đã được thực hiện?**  
    Các bước xử lý bao gồm:
    1.  **Sửa lỗi đơn vị giá (Price Bug Correction):** Chia thuộc tính `initialprice` của Steam Store API cho 100 để chuyển đổi từ đơn vị cents sang USD thực tế (đảo ngược lỗi lạm phát giá 100 lần của hệ thống).
    2.  **Lược bỏ thuộc tính khuyết thiếu (Playtime Pruning):** Lược bỏ hoàn toàn thuộc tính `average_playtime` do gặp lỗi khuyết thiếu hệ thống `MNAR` sau năm 2023.
    3.  **Kỹ nghệ đặc trưng Target (Wilson Score Engineering):** Xây dựng thuộc tính `wilson_score` đại diện cho giới hạn dưới của khoảng tin cậy `Wilson Score Interval` ở mức ý nghĩa 95% ($z = 1.96$) để làm biến target chính, nhằm triệt tiêu thiên lệch do cỡ mẫu nhỏ (`small-sample bias`) của tỷ lệ đánh giá thô.
    4.  **Lược bỏ thuộc tính dư thừa (Redundancy Pruning):** Loại bỏ hoàn toàn các thuộc tính thô và trùng lặp ý tưởng sau khi đã hợp nhất (bao gồm `owners` (raw range string), `developer_x`, `developer_y`, `publisher_x`, `publisher_y`, `score_rank`, `userscore`, `average_forever`, `average_2weeks`, `median_forever`, `median_2weeks`, `store_name`, `store_price`, `initialprice`, `price` (original SteamSpy cents), `name` (duplicate from store)).
*   **Dữ liệu thô gốc có được lưu trữ không?**  
    Có, dữ liệu thô gốc không qua chỉnh sửa được lưu trữ bất biến tại đường dẫn `data/raw/steam_games_raw.csv`.

---

## 5. Uses (Mục đích sử dụng bộ dữ liệu)

*   **Bộ dữ liệu này đã được sử dụng cho các tác vụ nào?**  
    Bộ dữ liệu đã được phân tích thống kê mô tả, kiểm định phân phối của target, và chạy các kiểm định giả thuyết khoa học (Welch's T-test, One-way ANOVA, Pearson Correlation) để chứng minh mối quan hệ giữa phân khúc giá, thể loại và sự thành công của game.
*   **Các mục đích sử dụng tiềm năng trong tương lai là gì?**  
    Bộ dữ liệu có thể được sử dụng cho các nghiên cứu thị trường game, dự đoán xu hướng thị hiếu thể loại, hoặc đánh giá tác động của chiến lược định giá (pricing strategy) lên mức độ tiếp nhận của người chơi.

---

## 6. Distribution (Phương thức phân phối)

*   **Bộ dữ liệu được phân phối bằng cách nào?**  
    Được phân phối dưới dạng file định dạng CSV đi kèm trong mã nguồn của dự án này.
*   **Bộ dữ liệu được phân phối dưới giấy phép (license) nào?**  
    Được phân phối dưới giấy phép mã nguồn mở MIT License phục vụ các mục đích học tập và nghiên cứu.

---

## 7. Maintenance (Bảo trì bộ dữ liệu)

*   **Ai là người chịu trách nhiệm hỗ trợ và bảo trì bộ dữ liệu?**  
    Bộ dữ liệu được bảo trì bởi nhóm sinh viên tác giả của đồ án.
*   **Bộ dữ liệu có thể được cập nhật bằng cách nào?**  
    Bộ dữ liệu có thể dễ dàng được cập nhật bằng cách chạy lại script cào dữ liệu `scripts/collect_steam_data.py` và chạy lại các notebook làm sạch để xuất ra file CSV mới.
