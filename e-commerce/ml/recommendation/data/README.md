# Dữ liệu và nhãn

- `queries.jsonl`: 120 **nhu cầu mẫu do code chuẩn bị**, gồm 40 tình huống × 3 ngân sách. Chưa phải nhu cầu thu thập từ người dùng thật. Nhóm cần duyệt độ tự nhiên, loại món và tính khả thi trước khi đóng băng.
- `splits.json`: seed 42, chia theo `family_id`: 72 train / 24 validation / 24 test. Ba biến thể ngân sách của một tình huống không đi qua nhiều tập.
- `judgments.csv` trong Git chỉ là header. File gán nhãn thật được stage `label` xuất ra kèm `pool-manifest.json`. Không thay file đó bằng header trong Git.
- Catalog không commit thêm vào module này. Dùng JSON đã bổ sung từ bộ Tiki, ghi SHA-256 vào manifest và upload bản riêng tư lên Kaggle.

## Quy trình chấm

1. Chốt catalog và 120 nhu cầu, chạy EDA để thấy loại món không đủ hàng. Duyệt/chỉnh nhu cầu rồi mới tạo pool.
2. Stage `label` lấy tập gộp ứng viên từ TF-IDF/BM25/E5/BGE, tối đa 60 sản phẩm mỗi nhu cầu và phân bổ theo loại món. Không thể coi tập gộp là toàn catalog.
3. Chấm `grade`: **0** không liên quan/sai nhu cầu, **1** liên quan một phần, **2** phù hợp, **3** rất phù hợp. Không tự điền ô trống thành 0. Điền tên/mã người chấm ở `annotator`.
4. File `judgments.csv`: điền train/validation. Hai file `test-rater-a.csv`, `test-rater-b.csv`: hai người chấm độc lập phần test.
5. Dùng `adjudicate_test()` xuất `test-adjudicated.csv`; chỗ bất đồng để trống để nhóm thảo luận và điền lại. Training không đọc điểm test.
6. Không xóa/thêm hàng hoặc đổi ID/slot sau đóng băng pool. Nếu cần thay catalog/nhu cầu, tạo workspace và pool mới, không trộn kết quả cũ.

Không đánh giá cỡ mặc hoặc phối màu từ thông tin không có trong nguồn. `collectionGroup` được thu theo nhóm truy vấn nên cần kiểm tra thủ công; không tự xem là nhãn thời trang hoàn hảo.

## Kiểm tra nhãn test

```python
from fashion_reco.labeling import adjudicate_test
adjudicate_test('labeling/test-rater-a.csv', 'labeling/test-rater-b.csv',
                'labeling/test-adjudicated.csv')
```

Kiểm tra ít nhất một lần các trường ID/giá/ảnh với catalog, phân biệt điểm liên quan của từng món và đánh giá phối hợp của cả bộ. Nhãn test chỉ mở sau khi chốt mô hình bằng validation.
