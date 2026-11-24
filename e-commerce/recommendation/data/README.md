# Thư mục dữ liệu

Không commit dữ liệu lên git (đã có trong `.gitignore`). Mỗi người tự đặt file vào đây.

| File | Dùng cho | Cách có |
|---|---|---|
| `2019-Dec.csv.gz` (hoặc `.csv`) | Tạo mẫu 5% | Tải từ REES46 (xem `README.md` ở thư mục cha) |
| `2020-Jan.csv.gz` (hoặc `.csv`) | Tạo mẫu 5%, notebook EDA | Tải từ REES46 |
| `2019-Dec_5pct.parquet` | Notebook mô hình | `python prepare_data.py`, hoặc nhận file từ Dương |
| `2020-Jan_5pct.parquet` | Notebook mô hình | `python prepare_data.py`, hoặc nhận file từ Dương |

Chỉ chạy notebook mô hình thì **chỉ cần 2 file `_5pct.parquet`**.
