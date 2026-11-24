# ML recommendation thời trang

Package nghiên cứu cho use case: **nhu cầu + những loại món cần mua + tổng ngân sách → bộ sản phẩm kèm ảnh**. Code trên nhánh `feature/ml-recommendation`. Chưa tích hợp API marketplace.

## Trạng thái và phạm vi

Đã có pipeline để thử TF-IDF, BM25, multilingual E5-base, BGE-M3 và train LambdaMART. **Chưa có nhãn thật, chưa train LambdaMART và chưa có kết luận mô hình thắng.** Colab T4 đã tạo artifact cho snapshot 15.652 sản phẩm. Các nhu cầu đi kèm là template để nhóm duyệt. Stage train cố ý từ chối nhãn thiếu.

## Kết quả Colab đã nhận và chấm nhãn

Kết quả đã kiểm tra ở `artifacts/colab-results-15652/`. Bản gốc được giữ trong
`output/`, SHA-256 và biên bản kiểm tra trong `verification.json`. Không tải artifact
joblib/pickle để chạy trên máy cá nhân. Chỉ đọc metadata, header vector và CSV.

- 15.652 sản phẩm hợp lệ, E5 `[15652, 768]`, BGE-M3 `[15652, 1024]`.
- 7.123 dòng ứng viên: train 4.246, validation 1.440, test 1.437. Chưa có điểm người chấm.
- Mở `annotation/train-validation.html`, nhập tên/mã, chấm từng món 0–3. Có ảnh,
  ngân sách, mô tả đầy đủ, ghi chú, lưu trong trình duyệt và xuất bản nháp JSON/CSV.
- Hai người test dùng file riêng `test-a.html` / `test-b.html`. Gửi mỗi người đúng
  `annotation-test-a.zip` / `annotation-test-b.zip`, tránh chia sẻ điểm trước khi chấm xong.
- Đọc `HUONG_DAN.md` của lượt chạy. CSV mang tiền tố PARTIAL chưa đủ để train.
- `build-timings.json` đã bị lần preview ghi lại khi tái dùng cache. Không diễn giải
  các số này là thời gian encode toàn bộ catalog từ đầu. `colab-latency.json` đo 24
  truy vấn validation; chất lượng vẫn chưa đánh giá.

Công cụ nhập lượt khác, không ghi đè thư mục hoặc nhãn đã có:

```powershell
python tools/import_colab_results.py --archive <results.zip> --snapshot <frozen-catalog.json> --output <new-directory>
```

### Tiếp tục từ Colab, không tiếp tục snapshot Kaggle cũ

Notebook: `artifacts/colab-results-15652/Fashion_15652_Continue_Train_Colab.ipynb`.
Generator: `colab/prepare_resume.py`. Notebook chỉ chạy trong Colab hosted runtime,
lưu hai ZIP gốc vào `MyDrive/ML_Recommendation_15652/inputs/`, nhãn vào `labels/`,
kết quả vào `runs/`. Khôi phục embedding đã có, kiểm tra fingerprint/revision trước
khi chạy. Nếu thiếu nhãn, dừng trước khi tải encoder hoặc train.

- Upload `fashion-colab-15652.zip` và `colab-15652-artifacts.zip` lần đầu.
- Chấm đủ train/validation và upload `judgments.csv`. File PARTIAL không dùng train.
- Stage mặc định `train`: so sánh 4 retriever và LambdaMART trên validation.
- Chỉ chuyển `test` sau khi khóa model và giải quyết bất đồng giữa hai rater.
- Khi stage hoàn tất/lỗi Python, sao lưu ZIP có timestamp và `latest-results.zip`.
  Nếu máy ảo bị xóa đột ngột, khối sao lưu có thể không chạy, nhưng input ZIP và nhãn
  đã có trên Drive để chạy lại mà không encode catalog từ đầu.
- Kaggle `soa-fashion-labeling` được kiểm tra lại là COMPLETE khi chuyển sang
  Colab. Không resubmit lượt cũ và không trộn snapshot Kaggle 13.538 với Colab 15.652.

### Bản thử nhãn tự sinh trên Kaggle

Theo yêu cầu thử không chấm tay, `tools/make_pseudo_labels.py` đã tạo 7.123 nhãn
`rule_teacher_v1` ở `artifacts/pseudo-smoke-15652-rule-v1/`. Dùng quy tắc văn bản
về loại món/ngữ cảnh/ràng buộc, không dùng điểm model hoặc nội dung ảnh. Nhãn người
chấm và file gốc không bị ghi đè. Có manifest SHA, phân bố điểm và audit từng dòng.

Thí nghiệm riêng `charlotte4306/soa-fashion-pseudo-smoke-15652` chạy CPU Kaggle,
tái sử dụng embedding từ Colab 15.652. Dataset private
`charlotte4306/soa-colab-15652-pseudo-smoke` giữ ZIP với đuôi `.bundle` để tránh
Kaggle tự giải nén làm đổi đường dẫn. Model offline được kiểm SHA với revision gốc.
Đóng gói bằng `kaggle/stage_pseudo_smoke.py`, runner `kaggle/pseudo_smoke_main.py`.

Train/validation/test đều dùng cùng teacher nên điểm chỉ đo mức khớp quy tắc,
**không chứng minh chất lượng recommendation hoặc mô hình thắng trên người dùng**.
File `test-adjudicated.csv` chỉ là tên đầu vào của pipeline cũ, không có hai người
chấm hoặc phân xử thật. Kết quả ghi rõ `pipeline_smoke_test_only`.

Đầu ra: `pseudo-results-summary.json`, NDCG/Recall/Precision trên nhãn yếu,
latency, feature importance và kiểm tra bundle. Monitor chỉ tải output khi hoàn tất,
không tự tạo thêm lượt chạy. Không so sánh latency CPU Kaggle với T4 Colab như cùng
điều kiện phần cứng. Xem `artifacts/kaggle-pseudo-smoke-15652/monitor.log`.

Dataset mở rộng còn đang thu thập; tên thư mục `tiki-fashion-20000` không chứng minh đã có 20.000. Xem `productCount` và `requestedCountReached` trong manifest nguồn. Chốt snapshot trước khi chấm nhãn.

Phân biệt `research` (cho phép hàng nguồn báo hết hàng để nghiên cứu nội dung) và `available_only` (chỉ dùng snapshot `available`). Không sửa tồn kho nguồn. Budget tính **tổng giá sản phẩm**, chưa gồm vận chuyển/khuyến mãi. Tối đa 4 loại món, một món cho mỗi loại. Không tự suy đoán nhu cầu mơ hồ, không có ảnh đầu vào, lịch sử user, ALS, LLM hoặc fine-tuning encoder.

## Cấu trúc

- `notebooks/`: ba notebook trình bày EDA, tạo pool chấm nhãn, training/evaluation/inference.
- `src/fashion_reco/`: logic dùng chung; import package không tải model. `features.py` dùng chung cho train và inference.
- `configs/experiment.yaml`: toàn bộ lựa chọn thí nghiệm. E5/BGE đã ghim revision bằng commit hash; chỉ đổi revision khi bắt đầu một thí nghiệm mới.
- `data/`: nhu cầu, split và hướng dẫn nhãn; catalog/model/embedding/output lớn nằm ngoài Git.
- `kaggle/`: script chạy từ xa và công cụ đóng gói workspace. Chưa upload tài khoản hoặc chạy tốn quota tự động.
- `tests/`: kiểm thử với dữ liệu giả nhỏ, không tải encoder hoặc train trên máy cá nhân.

## Chạy trên Kaggle

**EDA đã kiểm chứng từ xa:** notebook/script nhận cả `source.zip` và thư mục `source/` do Kaggle tự giải nén. Stage EDA chạy bằng thư viện chuẩn, không gọi `pip` và không cần tải build dependencies. Phiên bản Kaggle 3 chạy thành công trên snapshot 13.538 sản phẩm; output ở `artifacts/kaggle-eda-latest/fashion-reco/output/`. Training/labeling vẫn cần các thư viện ML và nhãn như mô tả bên dưới.

Nếu CLI timeout qua IPv6, chạy CLI qua wrapper riêng (không đổi cấu hình mạng): từ `e-commerce`, dùng `.\.venv-kaggle\Scripts\python.exe .\ml\recommendation\kaggle\kaggle_ipv4.py` thay cho `kaggle.exe` trong các lệnh.

1. Từ `e-commerce/ml/recommendation`, chuẩn bị workspace nhẹ trên máy cá nhân:

   ```powershell
   python kaggle/prepare_workspace.py --catalog ../../../recommendation-demo/data/tiki-fashion-20000/tiki-fashion.enriched.json --output artifacts/upload-v1
   ```

2. Tạo dataset **private** `charlotte4306/soa-ml-workspace` trên Kaggle và upload nội dung `upload-v1`. Công cụ chỉ đóng ZIP code và sao chép JSON, không tạo embedding/train. Không tải cả virtualenv, credential hoặc thư mục repo.
3. Mở notebook trong `notebooks/` bằng Kaggle và thêm dataset trên. Cấu hình hiện tại chạy **CPU Kaggle** cho cả `01`, `02` và `03`, kể cả E5/BGE-M3; batch size 8, PyTorch dùng 4 threads. Đây là lựa chọn CPU rõ ràng theo yêu cầu, không chạy trên máy cá nhân. Dùng model/wheel offline đã chuẩn bị, hoặc bật Internet nếu cần tải thêm thư viện. Muốn dùng GPU sau này, đặt `DENSE_DEVICE='cuda'` trong notebook và bật GPU thực tế; chế độ CUDA vẫn báo lỗi khi không có GPU.
4. Chạy theo thứ tự **eda → label → nhóm chấm → train → test**. `label` xuất pool/CSV không có điểm tự sinh; kết quả nằm dưới `/kaggle/working/fashion-reco/output`.
5. Lưu output thành version/dataset private giữa các phiên. `source.zip` và `catalog.json` nằm trên input chỉ đọc. Muốn mang nhãn vào workspace tiếp theo, thêm `--labeling <folder>` khi đóng gói. Mang artifact train sang phiên test bằng `--previous-run <output-folder>`.
6. Notebook `03` mặc định chỉ train/validation. Sau khi chốt lựa chọn mới chuyển `STAGE='test'`, cung cấp `test-adjudicated.csv` và output train. Không gọi test lặp lại để chỉnh model.

### Chạy khi Kaggle lỗi DNS

Không chạy lại GPU liên tục nếu PyPI/Hugging Face chưa truy cập được. Dùng `kaggle/preflight.py` trên CPU trước. `enable_internet=true` trong metadata không thay thế việc kiểm tra kết nối thực tế.

- `kaggle/fetch_model_manifest.py` lấy checksum từ đúng revision Hugging Face; không tải trọng số.
- `kaggle/download_offline_model.py` chỉ chuyển file model gốc về để upload vào dataset **private**; không import encoder, tạo embedding hay train trên máy cá nhân. Có kiểm tra SHA-256 và tiếp tục file đang tải khi máy chủ hỗ trợ Range.
- `kaggle/stage_run.py` nhúng wheel nhỏ vào runner, gắn nguồn model/dataset và manifest checksum. Runner cài wheel bằng `--no-index --no-deps`, xác minh mọi file model cần dùng, rồi tạo cache tại đúng revision. Mirror sai checksum bị từ chối; không tự đổi sang model đã fine-tune của người khác.
- BGE-M3 đã được xác minh từ nguồn Kaggle `yethukmutt/bge-m3/transformers/m3/1` với revision gốc trong config. Những mirror E5 đã kiểm tra chưa khớp; bản E5 gốc đã được chuyển lên dataset private `charlotte4306/soa-e5-offline`. Lượt label phiên bản 2 xác minh thành công cả hai model, nhưng dừng vì không có CUDA.
- Tài khoản chưa xác minh số điện thoại khi kiểm tra ngày 24/11/2026. Hoàn tất Phone verification trong Kaggle Settings trước khi chạy lại GPU. Metadata `enable_gpu=true`, machine shape T4 và quota 30 giờ không chứng minh runtime đã có GPU; runner kiểm tra CUDA thực tế trước khi xử lý model. `kaggle/gpu_probe.py` dùng để kiểm tra GPU mà không tải model hoặc train.
- Notebook mới không build package nội bộ. Khi chuẩn bị workspace tiếp theo, có thể thêm `--model-manifest <json> --wheel <whl>` vào `prepare_workspace.py`, rồi gắn cùng các input model tương ứng trên Kaggle. Snapshot `upload-v1` cũ vẫn được giữ nguyên.
- `kaggle/monitor_run.py` chỉ theo dõi job đã có, tải output khi hoàn thành và lưu log khi lỗi; không tự gửi lại GPU. Tạo `monitor.stop` trong thư mục output để dừng theo dõi.

Tạo pool ứng viên là bước chuẩn bị nhãn. Chỉ train LambdaMART sau khi nhóm chấm nhãn thật; chưa có kết quả chọn mô hình tốt nhất ở bước này.

### Gửi script bằng CLI

`kernel-metadata.json` mặc định private, CPU và stage EDA. Dataset slug phải tồn tại trước khi gửi. Dùng `stage_run.py --device cpu` để chuẩn bị label/train/test chạy CPU, hoặc `--device cuda` khi muốn chuyển lại GPU. Runner ghi `effective-config.yaml` vào output và áp dụng đúng thiết bị dù workspace cũ vẫn chứa config CUDA. Không chạy script Kaggle này trên máy cá nhân.

```powershell
# Chạy từ e-commerce bằng CLI đã đăng nhập
.\.venv-kaggle\Scripts\kaggle.exe kernels push -p ml/recommendation/kaggle
.\.venv-kaggle\Scripts\kaggle.exe kernels status charlotte4306/soa-fashion-recommendation-experiments
.\.venv-kaggle\Scripts\kaggle.exe kernels output charlotte4306/soa-fashion-recommendation-experiments -p ml/recommendation/artifacts/downloaded
```

Upload workspace mới khi code/nhãn thay đổi. Tạo run/output folder riêng cho mỗi snapshot. Không chia sẻ joblib nhận từ nguồn không tin cậy.

## Thí nghiệm

120 nhu cầu, 40 family × 3 ngân sách; chia 72/24/24 theo family để hạn chế rò rỉ biến thể. Tập gộp tối đa 60 ứng viên/nhu cầu từ các retriever bằng reciprocal-rank fusion, chia quota theo slot. Nhãn 0–3 do nhóm chấm, không tự coi sản phẩm chưa chấm là không liên quan. Giữ nguyên mọi phương pháp trên **cùng pool** khi so sánh ranker.

LambdaMART: tối đa 8 cấu hình (`num_leaves` 7/15, `min_child_samples` 10/20, learning rate .03/.05), tối đa 500 cây và early stopping 30. Feature gồm điểm từ khóa, điểm E5/BGE, khớp tên/brand/slot, log giá, tỷ lệ giá/ngân sách, rating/review và cờ thiếu. Không có lượt xem hoặc doanh số theo ngày giả lập. JSON nguồn được giữ riêng, không index HTML hoặc toàn snapshot.

Chọn bằng NDCG@5 validation; nếu chênh dưới .01, ưu tiên P50 inference thấp hơn trên cùng truy vấn. Nhóm kiểm tra chất lượng bộ trên validation trước khi chốt bản triển khai. Đây là pilot với tập nhãn nhỏ, không khẳng định tốt nhất nói chung.

`selection-lock.json` lưu cấu hình, dataset/pool/model hash; stage test từ chối khi các phần đó thay đổi. Bảng test có tất cả phương pháp để báo cáo, nhưng không dùng test chọn lại model.

## Kết quả và cách diễn giải

- NDCG@5, Precision@5 trên từng nhóm (nhu cầu, loại món). Recall chỉ là **pooled recall**, không phải Recall toàn catalog. Nhóm không có nhãn phù hợp báo NDCG/Recall `null`, không biến thành điểm tốt.
- Chọn bộ: duyệt tối đa 20 ứng viên/slot, tổng điểm reciprocal rank lớn nhất trong ngân sách, hòa điểm chọn giá thấp hơn rồi ID. Chưa học phối màu/cỡ/phong cách tương thích.
- Không tìm được bộ trong pool thì trả `no_feasible_bundle` với lý do và lựa chọn từng phần; không kết luận toàn sàn không có bộ phù hợp. Không trả một bộ thiếu món như thể đầy đủ.
- Hai chế độ research/available_only báo tỷ lệ đủ món, vi phạm giá, trùng ID và fallback. `validation-bundles.json` có bộ của hai phương án đứng đầu; `test-bundles.json` chứa ảnh/bằng chứng trên test. `validation-bundle-human-review.csv` và `test-bundle-human-review.csv` để nhóm chấm đáp ứng nhu cầu và tương thích 0–3.
- Độ trễ warm index, xóa cache embedding query giữa lượt, luân phiên thứ tự phương pháp. P95 trên 24 nhu cầu chỉ là tham khảo. Peak RAM/GPU là **toàn process**, không gán thành số bộ nhớ riêng của từng model; chạy tách process nếu cần đo riêng.
- Embedding pretrained **không phải fine-tuning**; phần được huấn luyện là LambdaMART. Không có timeout cưỡng bức online trong bản offline này.

## Dùng lại và kiểm thử

```python
from fashion_reco.schemas import ShoppingRequest
from fashion_reco.inference import recommend
request = ShoppingRequest('demo', 'demo', 'Đi ăn cưới, đã có váy, cần giày và túi',
                          ('women_shoes', 'women_bags'), 700_000)
result = recommend(request, catalog, {'retrievers': retrievers, 'ranker': ranker},
                   mode='available_only', method='lambdamart')
```

Mô hình và catalog phải đến từ cùng snapshot. Có thể dùng stage `build_retrievers` và load `SupervisedRanker` từ artifact đã tạo. Backend sẽ có adapter gọi interface này sau giai đoạn chọn model; không tạo index/train lại trong mỗi request.

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
```

Chỉ dùng fixture nhỏ cho kiểm thử local. Không chạy ba notebook hoặc `run_stage()` trên máy cá nhân để train catalog thật.
