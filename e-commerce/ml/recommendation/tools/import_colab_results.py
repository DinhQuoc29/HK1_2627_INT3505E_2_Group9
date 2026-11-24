"""Verify and preserve Colab outputs; prepare human annotation without loading ML models."""
import argparse
import ast
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import zipfile


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def array_header(path):
    # Only parse the NumPy header. Never load weights, pickle, or execute an artifact.
    with Path(path).open('rb') as stream:
        if stream.read(6) != b'\x93NUMPY':
            raise ValueError('Invalid NumPy file')
        version = stream.read(2)
        size_bytes = 2 if version[0] == 1 else 4
        size = int.from_bytes(stream.read(size_bytes), 'little')
        if size > 65536:
            raise ValueError('Oversized NumPy header')
        header = ast.literal_eval(stream.read(size).decode('latin1').strip())
        shape = header['shape']
        if header['descr'] != '<f4' or header['fortran_order'] or len(shape) != 2:
            raise ValueError('Expected a two-dimensional float32 embedding')
        if path.stat().st_size != stream.tell() + shape[0] * shape[1] * 4:
            raise ValueError('Truncated embedding')
        return {'shape': list(shape), 'dtype': header['descr']}


def read_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def prepare(source, destination, snapshot):
    destination = Path(destination).resolve()
    if destination.exists():
        raise FileExistsError('Keep existing labels and imports; choose a new destination.')
    with zipfile.ZipFile(source) as archive:
        paths = [item.filename for item in archive.infolist()]
        if len(paths) != len(set(paths)):
            raise ValueError('Duplicate archive paths')
        if sum(item.file_size for item in archive.infolist()) > 2_000_000_000:
            raise ValueError('Unexpectedly large archive')
        for name in paths:
            target = (destination / 'output' / name).resolve()
            if '\\' in name or not target.is_relative_to(destination / 'output'):
                raise ValueError('Unsafe archive path')
        required = {'snapshot-manifest.json', 'catalog-manifest.json', 'catalog.cleaned.json',
                    'labeling/pool-manifest.json', 'labeling/judgments.csv',
                    'labeling/test-rater-a.csv', 'labeling/test-rater-b.csv', 'colab-latency.json'}
        if not required.issubset(paths):
            raise ValueError('Missing required Colab artifacts')
        frozen = json.loads(archive.read('snapshot-manifest.json'))
        if sha(snapshot) != frozen['catalog_sha256']:
            raise ValueError('The original frozen catalog does not match this run')
        destination.mkdir(parents=True)
        archive.extractall(destination / 'output')
    output = destination / 'output'
    load = lambda name: json.loads((output / name).read_text(encoding='utf-8'))
    catalog, pool, latency = load('catalog-manifest.json'), load('labeling/pool-manifest.json'), load('colab-latency.json')
    if any(item['catalog_sha256'] != frozen['catalog_sha256'] for item in (pool, latency)) or catalog['sha256'] != frozen['catalog_sha256']:
        raise ValueError('Mismatched catalog provenance')
    products = load('catalog.cleaned.json')
    by_id = {p['id']: p for p in products}
    if len(by_id) != len(products) or len(products) != catalog['valid_count']:
        raise ValueError('Invalid cleaned catalog')
    rows = read_rows(output / 'labeling/judgments.csv')
    keys = [(r['query_id'], r['slot'], r['product_id']) for r in rows]
    if len(set(keys)) != len(keys) or [list(k) for k in keys] != pool['candidate_keys'] or len(rows) != pool['row_count']:
        raise ValueError('Annotation keys changed')
    for row in rows:
        product = by_id[row['product_id']]
        if row['slot'] != product['slot'] or int(row['price']) != product['price']:
            raise ValueError('Annotation product differs from frozen catalog')
    headers = {}
    for method, dim in (('e5', 768), ('bge', 1024)):
        header = array_header(output / f'artifacts/dense/{method}/vectors.npy')
        if header['shape'] != [len(products), dim]:
            raise ValueError('Embedding shape does not match catalog')
        headers[method] = header
    test = [r for r in rows if r['split'] == 'test']
    for role in ('a', 'b'):
        if read_rows(output / f'labeling/test-rater-{role}.csv') != test:
            raise ValueError('Test rater file does not match frozen pool')
    annotation = destination / 'annotation'
    annotation.mkdir()
    template = Path(__file__).with_name('annotation_template.html').read_text(encoding='utf-8')
    pool_sha = sha(output / 'labeling/pool-manifest.json')
    packets = [('train-validation', [r for r in rows if r['split'] in ('train', 'validation')], 'judgments.csv'),
               ('test-a', test, 'test-rater-a.csv'), ('test-b', test, 'test-rater-b.csv')]
    for role, subset, filename in packets:
        payload = {'role': role, 'filename': filename, 'pool_sha256': pool_sha,
                   'columns': list(rows[0]), 'rows': subset, 'empty_slots': pool['empty_slots']}
        encoded = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
        (annotation / f'{role}.html').write_text(template.replace('/*__PAYLOAD__*/', encoded), encoding='utf-8')
    report = {'archive_sha256': sha(source), 'snapshot': frozen, 'catalog': catalog,
              'embedding_headers': headers, 'rows_by_split': dict(Counter(r['split'] for r in rows)),
              'queries_by_split': {s: len({r['query_id'] for r in rows if r['split'] == s}) for s in ('train', 'validation', 'test')},
              'existing_grades': sum(r['grade'] in ('0', '1', '2', '3') for r in rows),
              'empty_slots': pool['empty_slots'], 'latency': latency,
              'quality_evaluated': False, 'verification': 'SHA provenance, pool keys, product IDs/prices, rater copies and embedding headers checked. No pickle/model loaded.'}
    (destination / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    table = '\n'.join(f"| {m} | {v['mean_ms']:.1f} | {v['p50_ms']:.1f} | {v['p95_ms']:.1f} |" for m, v in latency['latency'].items())
    instructions = f'''# Kết quả Colab 15.652 và bước chấm nhãn

Đã nhận và kiểm tra archive. Giữ nguyên `output/`, không ghi đè file gốc.
Catalog hợp lệ: {len(products):,} sản phẩm. Phần cứng báo cáo: {latency['hardware']}.
Số dòng ứng viên: {len(rows):,}. Phân bố: {report['rows_by_split']}.
Chưa có kết luận về chất lượng hoặc mô hình tốt nhất.
Có {len(pool['empty_slots'])} trường hợp thiếu ứng viên theo loại món trong pool:
{pool['empty_slots']}. Không tự điền sản phẩm hay điểm để bù những trường hợp này.

| Phương pháp | Mean ms | P50 ms | P95 ms |
| --- | ---: | ---: | ---: |
{table}

24 truy vấn validation, warm index và luân phiên phương pháp. TF-IDF/BM25 dùng CPU,
E5/BGE dùng GPU trong cùng phiên. Đây là độ trễ của pipeline đã cấu hình, không phải
so sánh riêng phần cứng. Build-timings đã bị ô preview ghi lại khi tái dùng cache:
không dùng những số đó làm thời gian encode catalog từ đầu.

## Làm ngay

1. Mở `annotation/train-validation.html` bằng Edge hoặc Chrome.
2. Nhập tên/mã người chấm, bấm Bắt đầu. Duyệt độ tự nhiên của nhu cầu và loại món.
3. Chấm từng sản phẩm 0–3 theo nhu cầu, loại món và ngân sách. Không có thông tin
   về cỡ, màu hoặc tương thích thì không tự suy diễn. Nếu nhu cầu/nhóm sản phẩm sai,
   ghi chú và báo lại trước khi train; không đổi ID, không xóa hàng.
4. Bấm Tải bản nháp JSON thường xuyên để sao lưu. Điểm lưu trong trình duyệt chỉ
   là tiện ích, không thay thế bản sao. Gửi bản JSON nếu cần tiếp tục trên máy khác.
5. Khi hoàn tất, Tải CSV. File thiếu nhãn mang tiền tố PARTIAL, không dùng để train.
6. Hai người khác nhau dùng riêng `test-a.html` và `test-b.html`. Không trao đổi điểm
   hoặc xem nhãn của nhau trước khi hoàn tất. Giữ test kín khi chọn model bằng validation.
7. Gửi lại judgments.csv đã chấm. Train LambdaMART và đánh giá tiếp trên Colab/Kaggle,
   không chạy ML trên máy cá nhân. Sau khi chốt model mới xử lý bất đồng và mở test.

Ảnh là URL Tiki: cần Internet để hiện ảnh, có thể có ảnh hỏng. Trang không hiển thị
model đã đề xuất sản phẩm. Không biến ô chưa chấm thành 0.
'''
    (destination / 'HUONG_DAN.md').write_text(instructions, encoding='utf-8')
    with zipfile.ZipFile(destination / 'annotation-share.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for file in annotation.glob('*.html'):
            archive.write(file, file.name)
        archive.write(destination / 'HUONG_DAN.md', 'HUONG_DAN.md')
    for role, _, _ in packets:
        with zipfile.ZipFile(destination / f'annotation-{role}.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.write(annotation / f'{role}.html', f'{role}.html')
            archive.write(destination / 'HUONG_DAN.md', 'HUONG_DAN.md')
    print(json.dumps({k: report[k] for k in ('rows_by_split', 'queries_by_split', 'existing_grades', 'embedding_headers')}, ensure_ascii=False))
    print(destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--snapshot', required=True)
    args = parser.parse_args()
    prepare(args.archive, args.output, args.snapshot)
