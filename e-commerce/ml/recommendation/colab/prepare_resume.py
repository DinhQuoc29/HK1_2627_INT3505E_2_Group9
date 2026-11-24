"""Generate a cloud-only continuation notebook from verified Colab artifacts."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import textwrap


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def build(bundle, results, output, pseudo=None):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    cells = []
    def cell(kind, text):
        source = textwrap.dedent(text).strip() + '\n'
        if kind == 'code':
            ast.parse(source)
        entry = {'cell_type': kind, 'id': f'resume-{len(cells):02}', 'metadata': {}, 'source': source.splitlines(True)}
        if kind == 'code':
            entry.update(execution_count=None, outputs=[])
        cells.append(entry)
    md = lambda text: cell('markdown', text)
    code = lambda text: cell('code', text)
    md('''
    # Tiếp nối thí nghiệm Colab — 15.652 sản phẩm

    Dùng lại snapshot, pool chấm nhãn và embedding của lượt đã chạy, không tạo pool mới.
    Quy trình: lưu đầu vào vào Drive → kiểm tra dữ liệu và nhãn → nạp cache → train LambdaMART
    và so sánh TF-IDF/BM25/E5/BGE-M3 → lưu kết quả vào Drive.

    **Bật GPU T4 trong Thời gian chạy → Thay đổi loại thời gian chạy.**
    Dùng tài khoản Drive của bạn và upload hai ZIP khi được hỏi:
    `fashion-colab-15652.zip` (đầu vào gốc) và `colab-15652-artifacts.zip` (kết quả đã tải).
    Sau lần đầu, notebook dùng bản đã lưu trên Drive. Không tải hay train ML trên máy cá nhân.

    **Chưa có nhãn thì notebook dừng trước khi tải model.** Chấm 5.686 dòng train/validation,
    xuất `judgments.csv` rồi upload ở bước 3. Không dùng file PARTIAL để train.
    Không mở điểm test để điều chỉnh mô hình.
    ''')
    code('''
    from pathlib import Path
    import os, sys, json, hashlib, zipfile, shutil, csv, importlib.util
    from datetime import datetime, timezone
    if importlib.util.find_spec('google.colab') is None:
        raise RuntimeError('Notebook này chỉ chạy trên Google Colab, không chạy local.')
    from google.colab import drive, files
    drive.mount('/content/drive')
    DRIVE = Path('/content/drive/MyDrive/ML_Recommendation_15652')
    INPUTS = DRIVE / 'inputs'
    LABELS = DRIVE / 'labels'
    for folder in (INPUTS, LABELS, DRIVE / 'runs'):
        folder.mkdir(parents=True, exist_ok=True)
    WORK = Path('/content/fashion-resume-15652')
    WORK.mkdir(exist_ok=True)
    os.chdir(WORK)
    def file_sha(path):
        h = hashlib.sha256()
        with Path(path).open('rb') as stream:
            for block in iter(lambda: stream.read(1024*1024), b''):
                h.update(block)
        return h.hexdigest()
    def unzip_safe(archive, target):
        target = Path(target).resolve()
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            names = z.namelist()
            if len(names) != len(set(names)) or sum(i.file_size for i in z.infolist()) > 2_000_000_000:
                raise ValueError('Archive bất thường')
            for name in names:
                if chr(92) in name or not (target/name).resolve().is_relative_to(target):
                    raise ValueError('Đường dẫn ZIP không an toàn')
            bad = z.testzip()
            if bad:
                raise ValueError('ZIP hỏng: '+bad)
            z.extractall(target)
    print('Thư mục Drive:', DRIVE)
    ''')
    code(f'''
    EXPECTED = {{
        'fashion-colab-15652.zip': '{digest(bundle)}',
        'colab-15652-artifacts.zip': '{digest(results)}',
    }}
    for filename, expected in EXPECTED.items():
        dest = INPUTS / filename
        if not dest.exists():
            print('Chọn đúng file:', filename)
            uploaded = files.upload()
            if filename not in uploaded:
                raise RuntimeError('Chưa chọn đúng file '+filename)
            local = WORK / filename
            if file_sha(local) != expected:
                raise RuntimeError('Sai checksum '+filename)
            shutil.copy2(local, dest)
            del uploaded
        if file_sha(dest) != expected:
            raise RuntimeError('Bản trên Drive sai checksum '+filename)
    workspace, source = WORK/'workspace', WORK/'source'
    original, output = WORK/'original-output', WORK/'output'
    unzip_safe(INPUTS/'fashion-colab-15652.zip', workspace)
    manifest = json.loads((workspace/'workspace-manifest.json').read_text())
    for name, field in [('catalog.json','catalog_sha256'), ('source.zip','source_sha256')]:
        if file_sha(workspace/name) != manifest[field]:
            raise RuntimeError('Sai checksum '+name)
    unzip_safe(workspace/'source.zip', source)
    unzip_safe(INPUTS/'colab-15652-artifacts.zip', original)
    old_manifest = json.loads((original/'snapshot-manifest.json').read_text())
    if old_manifest['catalog_sha256'] != manifest['catalog_sha256'] or old_manifest['product_count'] != 15652:
        raise RuntimeError('Kết quả không thuộc snapshot 15.652')
    if not output.exists():
        previous = DRIVE/'runs/latest-results.zip'
        if previous.exists():
            unzip_safe(previous, output)
        else:
            shutil.copytree(original, output)
    if file_sha(output/'labeling/pool-manifest.json') != file_sha(original/'labeling/pool-manifest.json'):
        raise RuntimeError('Pool bị thay đổi. Không trộn các lượt chấm nhãn.')
    # Giữ metadata thời gian của lượt gốc, không gọi đây là thời gian encode từ đầu.
    shutil.copy2(original/'build-timings.json', output/'colab-original-cache-load-timings.json')
    print('Đã lưu hai ZIP gốc trên Drive. Kết quả và pool đã khôi phục.')
    ''')
    md('''
    ## 3. Kiểm tra nhãn người chấm

    Chọn `judgments.csv` đã chấm nếu chưa có trên Drive. Nhóm không đổi query/slot/ID,
    không xóa hoặc thêm dòng. File chỉ chứa train/validation được chấp nhận.
    Nếu nhu cầu hoặc nhóm sản phẩm không đúng, dừng để sửa protocol trước khi train.
    `STAGE='train'` dùng validation để chọn model. Chỉ đổi thành `test` sau khi đã chốt
    model, hoàn tất hai rater và có `test-adjudicated.csv` giải quyết bất đồng.
    ''')
    code('''
    STAGE = 'train'  # Chỉ đổi sang 'test' sau khi đã chốt mô hình và nhãn test.
    filename = 'judgments.csv' if STAGE == 'train' else 'test-adjudicated.csv'
    if STAGE not in ('train', 'test'):
        raise ValueError('Stage phải là train hoặc test')
    label_file = LABELS/filename
    if not label_file.exists():
        print('Chọn file nhãn đã hoàn tất:', filename)
        uploaded = files.upload()
        if filename not in uploaded:
            raise RuntimeError('Cần file '+filename+' thật, không tự sinh nhãn.')
        shutil.copy2(WORK/filename, label_file)
        del uploaded
    pool = json.loads((original/'labeling/pool-manifest.json').read_text())
    splits = json.loads((source/'data/splits.json').read_text())
    required = set(splits['test']) if STAGE=='test' else set(splits['train'])|set(splits['validation'])
    expected_keys = {tuple(k) for k in pool['candidate_keys'] if k[0] in required}
    seen, missing = set(), 0
    with label_file.open(encoding='utf-8-sig',newline='') as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        if row['query_id'] not in required:
            continue
        key = (row['query_id'], row['slot'], row['product_id'])
        if key in seen or key not in expected_keys:
            raise RuntimeError('ID bị sửa, trùng hoặc không thuộc pool: '+str(key))
        seen.add(key)
        missing += row['grade'] not in ('0','1','2','3') or not row.get('annotator','').strip()
    if seen != expected_keys or missing:
        raise RuntimeError(f'Nhãn chưa đủ: thiếu {len(expected_keys-seen)} dòng, {missing} dòng thiếu điểm/người chấm. Hoàn tất chấm rồi thay file trong Drive/labels.')
    if STAGE=='test' and not (output/'selection-lock.json').exists():
        raise RuntimeError('Chưa có selection-lock từ lượt train. Không dùng test để chọn model.')
    shutil.copy2(label_file, output/'labeling'/filename)
    print('Nhãn hợp lệ:', len(seen), 'dòng. Tiếp tục chạy ML trên Colab.')
    ''')
    md('''
    ## 4. Cài thư viện và kiểm tra GPU

    Giữ Torch CUDA có sẵn của Colab. Các trọng số gốc được tải từ Hugging Face,
    nhưng vector catalog được nạp lại từ cache đã có. Hai baseline lexical được build
    bằng code từ snapshot thay vì nạp pickle nhận từ file ZIP.
    ''')
    code('''
    import subprocess
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError('Chưa có GPU. Chọn Thời gian chạy → Thay đổi loại thời gian chạy → T4 GPU.')
    requirements = {'numpy':'numpy>=1.26,<3', 'sklearn':'scikit-learn>=1.4,<2',
                    'yaml':'PyYAML>=6,<7', 'joblib':'joblib>=1.3,<2',
                    'sentence_transformers':'sentence-transformers>=3,<6',
                    'lightgbm':'lightgbm>=4,<5', 'pandas':'pandas'}
    if importlib.util.find_spec('rank_bm25') is None:
        wheel = next((workspace/'offline-wheels').glob('rank_bm25-*.whl'))
        subprocess.run([sys.executable,'-m','pip','install','--no-index','--no-deps',str(wheel)],check=True)
    missing_packages = [v for k,v in requirements.items() if importlib.util.find_spec(k) is None]
    if missing_packages:
        subprocess.run([sys.executable,'-m','pip','install',*missing_packages],check=True)
    sys.path.insert(0,str(source/'src'))
    import yaml
    config_path = source/'configs/experiment.yaml'
    cfg = yaml.safe_load(config_path.read_text())
    cfg['dense'].update(device='cuda',batch_size=16)
    cfg['catalog_path'] = str(workspace/'catalog.json')
    cfg['output_dir'] = str(output)
    config_path.write_text(yaml.safe_dump(cfg,sort_keys=False))
    os.environ['FASHION_CATALOG'] = cfg['catalog_path']
    os.environ['FASHION_OUTPUT'] = cfg['output_dir']
    print('GPU:',torch.cuda.get_device_name(0))
    ''')
    code('''
    from fashion_reco.workflow import configure
    from fashion_reco.labeling import load_judgments
    cfg, products, catalog_manifest, requests, splits = configure(config_path)
    # Semantic validation against the exact frozen requests/catalog, before encoding queries.
    load_judgments(output/'labeling'/filename, requests, products, pool, catalog_manifest, required)
    dense = cfg['dense']
    for method in ('e5','bge'):
        cache = output/'artifacts/dense'/method
        metadata = json.loads((cache/'index.json').read_text())
        fingerprint = hashlib.sha256(json.dumps([(p['id'],p['text']) for p in products],ensure_ascii=False).encode()).hexdigest()
        expected = {'model_id':dense['models'][method], 'revision':dense['revisions'][method],
                    'max_length':dense['max_length'], 'fingerprint':fingerprint, 'method':method}
        if metadata != expected or not (cache/'vectors.npy').exists():
            raise RuntimeError('Cache không khớp '+method+'. Dừng, không tự encode lại toàn bộ catalog.')
    print('Hai cache đúng fingerprint và revision, sẵn sàng tái sử dụng.')
    ''')
    md('''
    ## 5. Huấn luyện và đánh giá

    Train LambdaMART trên train, chọn cấu hình bằng validation, rồi so sánh năm phương pháp.
    NDCG@5 chỉ tính từ nhãn người chấm. Kiểm tra cả chất lượng từng món và bộ sản phẩm.
    Không gọi đây là fine-tuning E5/BGE: hai encoder hiện vẫn pretrained.
    ''')
    code('''
    from fashion_reco.workflow import run_stage
    def backup_results(label):
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        local_zip = Path(shutil.make_archive(str(WORK/'continuation-results'),'zip',root_dir=output))
        history = DRIVE/'runs'/f'{stamp}-{label}.zip'
        shutil.copy2(local_zip,history)
        temporary = DRIVE/'runs/latest-results.zip.tmp'
        shutil.copy2(local_zip,temporary)
        temporary.replace(DRIVE/'runs/latest-results.zip')
        print('Đã sao lưu:',history)
    try:
        result = run_stage(config_path,STAGE,labeling_dir=output/'labeling')
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except Exception:
        backup_results(STAGE+'-interrupted')
        raise
    else:
        backup_results(STAGE+'-complete')
    ''')
    md('''
    ## 6. Lấy kết quả và quyết định bước tiếp

    Kết quả luôn có bản trong `MyDrive/ML_Recommendation_15652/runs/` sau khi stage hoàn tất.
    Nếu GPU bị thu hồi giữa stage, bản ZIP đầu vào và nhãn đã nằm trên Drive để khôi phục.
    Code không thể bảo đảm chạy khối sao lưu khi máy ảo bị xóa đột ngột.

    Sau train, xem `selection-lock.json`, `validation-details.json`, `training-trials.json`,
    `feature-importance.json`, `validation-bundle-summary.json` và các bộ cần người đánh giá.
    Chốt model bằng validation trước khi mở test. Gửi ZIP kết quả để rà soát trước tích hợp API.
    ''')
    code('''
    if STAGE == 'train':
        lock = json.loads((output/'selection-lock.json').read_text())
        import pandas as pd
        display(pd.DataFrame(lock['validation']).T)
        print('Lựa chọn pilot:',lock['selected_method'])
        print('Cần người kiểm tra bundle trước khi tích hợp, chưa bảo đảm phối đồ thẩm mỹ.')
    files.download(str(WORK/'continuation-results.zip'))
    ''')
    if pseudo is not None:
        # Isolate this demonstration from human labels, locks, and evaluation outputs.
        cells[0]['source'] = textwrap.dedent('''
        # Nhãn tự sinh — kiểm tra luồng train/test trên Colab

        Bản thử trên snapshot 15.652 sản phẩm, sử dụng lại embedding đã tạo.
        Nhãn 0–3 do bộ quy tắc sinh từ loại món, nội dung, ngữ cảnh và ràng buộc.
        Không phân tích nội dung ảnh. Không phải nhãn người chấm.
        Chỉ số chỉ đo mức khớp với bộ quy tắc này, không chứng minh mô hình tốt nhất.

        Bật T4 GPU. Chạy tất cả và chọn ba file khi được hỏi:
        `fashion-colab-15652.zip`, `colab-15652-artifacts.zip`, `pseudo-labels-rule-v1.zip`.
        Dữ liệu lưu riêng trong `MyDrive/ML_Recommendation_15652/PSEUDO_RULE_V1/`.
        Notebook tự chạy train/validation rồi test bằng nhãn yếu, xuất kết quả để kiểm tra.
        Không ghi đè nhãn người chấm hoặc kết quả thí nghiệm thật.
        ''').strip().splitlines(True)
        runtime = next(c for c in cells if c['cell_type']=='code')
        runtime['source'] = ''.join(runtime['source']).replace("MyDrive/ML_Recommendation_15652'", "MyDrive/ML_Recommendation_15652/PSEUDO_RULE_V1'").replace('/content/fashion-resume-15652','/content/fashion-pseudo-15652').splitlines(True)
        codes = [c for c in cells if c['cell_type']=='code']
        source_text = ''.join(codes[1]['source'])
        source_text = source_text.replace('EXPECTED = {', 'EXPECTED = {\n    '+repr(Path(pseudo).name)+': '+repr(digest(pseudo))+',')
        source_text += textwrap.dedent(f'''
        pseudo_dir = WORK/'pseudo-labels'
        unzip_safe(INPUTS/{Path(pseudo).name!r},pseudo_dir)
        pseudo_manifest = json.loads((pseudo_dir/'pseudo-label-manifest.json').read_text())
        if pseudo_manifest['purpose'] != 'pipeline_smoke_test_only' or pseudo_manifest['catalog_sha256'] != manifest['catalog_sha256'] or pseudo_manifest['pool_sha256'] != file_sha(original/'labeling/pool-manifest.json'):
            raise RuntimeError('Nhãn yếu không thuộc đúng snapshot/pool')
        for name,checksum in pseudo_manifest['files'].items():
            if file_sha(pseudo_dir/name) != checksum:
                raise RuntimeError('Nhãn yếu sai checksum')
            target = LABELS/name
            if target.exists() and file_sha(target) != checksum:
                raise RuntimeError('Không ghi đè nhãn đã thay đổi trong Drive')
            shutil.copy2(pseudo_dir/name,target)
        shutil.copy2(pseudo_dir/'test-adjudicated.csv',output/'labeling/test-adjudicated.csv')
        shutil.copy2(pseudo_dir/'pseudo-label-manifest.json',output/'pseudo-label-manifest.json')
        print('PSEUDO LABELS ONLY — Không phải nhãn người chấm.')
        ''')
        codes[1]['source'] = source_text.splitlines(True)
        execution = ''.join(codes[5]['source'])
        execution = execution.replace("result = run_stage(config_path,STAGE,labeling_dir=output/'labeling')", """result = run_stage(config_path,'train',labeling_dir=output/'labeling')
    result['evaluation_status'] = 'pseudo_label_smoke_test_only'
    (output/'selection-lock.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    backup_results('pseudo-train-complete')
    test_result = run_stage(config_path,'test',labeling_dir=output/'labeling')
    (output/'pseudo-results-summary.json').write_text(json.dumps({
        'purpose':'pipeline_smoke_test_only',
        'warning':'Train and test labels come from the same rules, not independent human ground truth. No production winner established.',
        'teacher':pseudo_manifest, 'validation':result, 'test':test_result},ensure_ascii=False,indent=2))""")
        codes[5]['source'] = execution.splitlines(True)
        for c in cells:
            if c['cell_type']=='markdown':
                text = ''.join(c['source'])
                if text.lstrip().startswith('## 3.'):
                    text = '## 3. Kiểm tra nhãn yếu\n\nNhãn được nạp tự động từ ZIP riêng. Kiểm tra đủ ID, điểm 0–3 và nguồn rule_teacher_v1. File test dùng cùng bộ quy tắc, không có hai rater hoặc phân xử của con người. Giữ STAGE=\'train\'; bước 5 tự chạy cả train và test trong thí nghiệm riêng này.\n'
                elif text.lstrip().startswith('## 5.'):
                    text = '## 5. Thử train và test tự động\n\nTrain LambdaMART, so sánh với TF-IDF/BM25/E5/BGE trên validation, rồi chạy test. Tất cả điểm relevance là nhãn yếu, chỉ phục vụ kiểm tra pipeline và mức khớp teacher. Encoder E5/BGE giữ nguyên pretrained. Không diễn giải lựa chọn pilot thành mô hình tốt nhất cho người dùng.\n'
                elif text.lstrip().startswith('## 6.'):
                    text = '## 6. Kết quả bản thử\n\nXem pseudo-results-summary.json, validation-details.json, test-ranking-summary.json, training-trials.json và các bundle. Kết quả được lưu trên Drive ở PSEUDO_RULE_V1/runs và tải xuống dạng ZIP. Nếu máy ảo bị xóa giữa stage, khối backup có thể không chạy, nhưng ZIP đầu vào và nhãn đã có trên Drive. Cần nhãn độc lập trước khi kết luận chất lượng hoặc chọn mô hình cho sản phẩm.\n'
                c['source']=text.splitlines(True)
        for c in codes:
            ast.parse(''.join(c['source']))
    notebook = {'cells':cells,'nbformat':4,'nbformat_minor':5,
                'metadata':{'colab':{'name':output.name},'accelerator':'GPU',
                            'kernelspec':{'display_name':'Python 3','name':'python3','language':'python'}}}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(notebook,ensure_ascii=False,indent=2),encoding='utf-8')
    print(output)
    print('Code cells AST-validated:',sum(c['cell_type']=='code' for c in cells))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',required=True)
    parser.add_argument('--results',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--pseudo',help='Optional weak-label ZIP; creates an isolated smoke-test notebook')
    args = parser.parse_args()
    build(args.bundle,args.results,args.output,args.pseudo)
