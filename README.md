# Quy trình Thu thập, Làm sạch & Kiểm định Chất lượng Bộ dữ liệu Steam Games

**Đồ án môn học DS108 — Tiền xử lý và Xây dựng Bộ dữ liệu**

Kho lưu trữ này chứa toàn bộ đường ống dẫn dữ liệu (data pipeline) từ đầu đến cuối cho việc thu thập, làm sạch, thẩm định và chuẩn hóa bộ dữ liệu các trò chơi trên Steam được phát hành trong giai đoạn từ **2022 đến 2026**.

Dự án này tập trung vào **Kiến trúc Dữ liệu theo Nguyên lý (Principle-Driven Data Architecture)**: xử lý các dị biệt tích hợp dữ liệu, sửa lỗi cấu trúc giá, xử lý khuyết thiếu hệ thống (`MNAR`), hiệu chỉnh toán học điểm đánh giá của người dùng để tránh sai lệch mẫu nhỏ (`Wilson Score`), và thực thi bộ kiểm định chất lượng tự động (`QA Assertions`).

---

## Cấu trúc Thư mục Dự án

```
DS108_final/
├── data/
│   ├── raw/           <- Dữ liệu thô gốc bất biến (steam_games_raw.csv)
│   └── processed/     <- Bộ dữ liệu sạch thành phẩm (steam_games_with_genres.csv)
│
├── notebooks/         <- Các Jupyter Notebooks ghi nhận các giai đoạn xử lý
│   ├── 01_data_collection.ipynb                 <- Quy trình thu thập dữ liệu từ APIs
│   ├── 02_data_cleaning_and_imputation.ipynb    <- Làm sạch, sửa cents bug, Wilson Score, QA
│   ├── 03_exploratory_data_analysis.ipynb        <- Phân tích EDA và kiểm định thống kê
│   └── 04_dataset_validation_dictionary.ipynb   <- Data Dictionary, QA, Code Book
│
├── scripts/           <- Mã nguồn thu thập và xử lý dữ liệu
│   ├── collect_steam_data.py           <- Script Python thu thập dữ liệu từ APIs
│   ├── clean_processed_data.py         <- Script Python chuẩn hóa kiểu dữ liệu
│   └── audit_project.py                <- Script tự động kiểm định chất lượng dự án
│
├── requirements.txt   <- Danh sách thư viện phụ thuộc
└── README.md          <- Tài liệu hướng dẫn này
```

---

## Hướng Hướng dẫn Khởi chạy & Tái lập

### Yêu cầu Hệ thống
Python 3.10 trở lên.

### 1. Cài đặt các Thư viện Phụ thuộc
```bash
pip install -r requirements.txt
```

### 2. Khởi chạy Dashboard Streamlit
Chạy giao diện trực quan hóa tương tác của dự án:
```bash
streamlit run app.py
```

### 3. Khởi chạy bằng Docker
Bạn cũng có thể đóng gói và khởi chạy Dashboard bằng Docker:

* **Xây dựng Docker Image:**
  ```bash
  docker build -t steam-dashboard .
  ```
* **Chạy Docker Container:**
  ```bash
  docker run -d -p 8501:8501 --name steam-app steam-dashboard
  ```
*Mở trình duyệt truy cập địa chỉ: `http://localhost:8501`*

### 4. Quy trình Tái lập / Chạy lại Đường ống Dữ liệu (Tùy chọn)
Tập dữ liệu thô (raw) và sạch (processed) đã được đính kèm sẵn trong thư mục `data/`. Nếu bạn muốn chạy lại toàn bộ pipeline để lấy dữ liệu mới hoặc kiểm chứng:

* **Bước 1: Thu thập dữ liệu thô từ API:**
  ```bash
  python scripts/collect_steam_data.py
  ```
  *(Script gọi đến API của SteamSpy và Steam Store để lấy thông tin game phát hành từ 2022 trở đi và lưu lại tại `data/raw/steam_games_raw.csv`)*

* **Bước 2: Tiền xử lý và làm sạch dữ liệu:**
  ```bash
  python scripts/clean_processed_data.py
  ```
  *(Pipeline làm sạch dữ liệu thô: sửa lỗi đơn vị giá tiền cents-USD, gỡ bỏ playtime bị khuyết MNAR, tính Wilson Score target, và lưu lại tại `data/processed/steam_games_with_genres.csv`)*

* **Bước 3: Chạy các Jupyter Notebooks (Tùy chọn):**
  Bạn có thể chạy tuần tự các notebook trong thư mục `notebooks/` để theo dõi các phân tích và biểu đồ trực quan hóa trung gian:
  - `notebooks/01_data_collection.ipynb` (Thu thập dữ liệu)
  - `notebooks/02_data_cleaning_and_imputation.ipynb` (Làm sạch & Điền khuyết)
  - `notebooks/03_exploratory_data_analysis.ipynb` (EDA & Kiểm định giả thuyết)
  - `notebooks/04_dataset_validation_dictionary.ipynb` (Đặc tả QA & Code Book)

* **Bước 4: Chạy kiểm toán tự động dự án (Project Audit):**
  ```bash
  python scripts/audit_project.py
  ```
  *(Script tự động so khớp cấu trúc tệp CSV thành phẩm với Code Book và các ràng buộc logic QA để đảm bảo chất lượng)*

---

## Các Tính năng Chuẩn hóa Dữ liệu Nổi bật

1. **Sửa lỗi đơn vị giá (Price Bug Fix):** Khắc phục lỗi lạm phát giá 100 lần khi Store API trả về giá dạng cents thay việc quy đổi sang USD.
2. **Xử lý Playtime khuyết thiếu hệ thống (MNAR):** Nhận diện việc dữ liệu playtime của SteamSpy bị khuyết 100% sau năm 2023 và tiến hành loại bỏ thuộc tính này để tránh thiên lệch.
3. **Hiệu chỉnh điểm Wilson Score:** Giải quyết vấn đề thiên lệch cỡ mẫu nhỏ bằng cách áp dụng giới hạn dưới của khoảng tin cậy Wilson Score Interval ở mức ý nghĩa 95%.
4. **Kiểm định QA tự động (Automated Quality Assertions):** Tích hợp bộ assertions tự động kiểm tra tính toàn vẹn.
5. **Xử lý MNAR owners_min:** Đánh dấu bucket `"0 .. 20,000"` có `owners_min = NaN` vì API không cung cấp lower bound thực tế.
6. **Loại bỏ biến trùng lặp:** Gỡ bỏ `owners` (string), `total_ratings` (dẫn xuất), và các cột thô/intermediate không cần thiết.
