# ML recommendation: gợi ý sản phẩm theo ngân sách (REES46)

Khối **V1 · Product recommendations** của hệ thống (use case B03): gợi ý top N sản phẩm cho người mua, chỉ giữ món nằm trong ngân sách. Toàn bộ phần ML (dữ liệu, EDA, sinh ứng viên, feature engineering, huấn luyện, đánh giá, inference) nằm trong 2 notebook; mỗi bước có giải thích và kết quả chạy.

Người làm: Dương.

## Kết quả chính

| Mô hình (tập test, mẫu 5% user) | NDCG@10 |
|---|---|
| **LightGBM ranker, 47 feature (bàn giao)** | **≈ 0.269** |
| Baseline tốt nhất: gợi ý lại món vừa xem | 0.217 |
| Baseline món phổ biến | 0.117 |

Hơn baseline tốt nhất khoảng 24% (khoảng tin cậy 95% không chứa 0). Chi tiết, hạn chế và yêu cầu dữ liệu cho database: mục 11 của `02_recommendation_model.ipynb`.

## Cấu trúc

```
recommendation/
├── README.md
├── requirements.txt
├── prepare_data.py                  # tạo mẫu 5% user từ dữ liệu gốc
├── 01_eda_rees46.ipynb              # EDA trên dữ liệu gốc tháng 1/2020 (đã có kết quả chạy)
├── 02_recommendation_model.ipynb    # toàn bộ pipeline mô hình (tự chứa code)
├── data/                            # dữ liệu, không commit (xem data/README.md)
└── artifacts/                       # sinh ra khi chạy notebook 02, không commit
```

## Cách chạy

**1. Môi trường** (Python 3.10+):

```
pip install -r requirements.txt
```

**2. Dữ liệu.** Notebook mô hình chỉ cần 2 file trong `data/`:

- `data/2019-Dec_5pct.parquet`
- `data/2020-Jan_5pct.parquet`

Có hai cách để có 2 file này:

- **Nhận từ Dương** (nhanh nhất), đặt vào `data/`.
- **Tự tạo từ dữ liệu gốc:** tải `2019-Dec.csv.gz` và `2020-Jan.csv.gz` của bộ *eCommerce behavior data from multi category store* của REES46 (https://data.rees46.com/datasets/marketplace/), đặt vào `data/`, rồi chạy:

  ```
  python prepare_data.py
  ```

  Script lấy toàn bộ hành vi của khoảng 5% user (chọn theo `hash(user_id)`), mất vài phút mỗi tháng. Máy ít RAM thì thêm `--memory 2GB`.

**3. Chạy notebook.** Mở `02_recommendation_model.ipynb`, chọn kernel có các thư viện trên, **Restart & Run All**. Khoảng 15–20 phút; RAM khoảng 4–6 GB.

- Đặt `RUN_ABLATION = False` (mục 0) để bỏ qua phần ablation (tiết kiệm 5–10 phút) khi đã có `artifacts/results/ablation.csv`.
- Kết quả, mô hình và metadata được lưu vào `artifacts/` (mục 9 của notebook).

`01_eda_rees46.ipynb` cần file gốc `data/2020-Jan.csv.gz` (khoảng 56 triệu dòng); chỉ chạy lại khi muốn xem lại EDA, vì notebook đã lưu sẵn kết quả.

## Lưu ý khi commit

- **Không commit** dữ liệu (`data/`) và kết quả (`artifacts/`): quá nặng, và chạy lại là có. `.gitignore` đã chặn sẵn.
- **Commit notebook sau khi đã chạy và lưu** (Ctrl+S), để người đọc thấy kết quả mà không phải chạy lại.
