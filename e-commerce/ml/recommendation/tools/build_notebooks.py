"""Build the three UTF-8 Kaggle notebooks from one reviewable source."""
import json
from pathlib import Path


def markdown(text):
    return {'cell_type':'markdown','metadata':{},'source':text.splitlines(True)}


def code(text):
    return {'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':text.splitlines(True)}


SETUP = '''from pathlib import Path
import os, sys, subprocess, zipfile, shutil, importlib.util
if not Path('/kaggle/input').exists():
    raise RuntimeError('Notebook này chỉ chạy trên Kaggle, không train trên máy cá nhân.')
archives = list(Path('/kaggle/input').rglob('source.zip'))
source = Path('/kaggle/working/fashion-reco/source')
source.mkdir(parents=True, exist_ok=True)
if len(archives) == 1:
    workspace = archives[0].parent
    with zipfile.ZipFile(archives[0]) as archive:
        for member in archive.infolist():
            if not (source / member.filename).resolve().is_relative_to(source.resolve()):
                raise ValueError('Unsafe archive path')
        archive.extractall(source)
elif not archives:
    sources = [p.parent for p in Path('/kaggle/input').rglob('pyproject.toml') if (p.parent/'src/fashion_reco').is_dir()]
    if len(sources) != 1:
        raise RuntimeError('Thêm đúng một workspace có source.zip hoặc thư mục source/.')
    workspace = sources[0].parent
    shutil.copytree(sources[0], source, dirs_exist_ok=True)
else:
    raise RuntimeError('Có nhiều file source.zip trong input.')
if EXTRAS:
    # Import our source directly; never invoke a package build on Kaggle.
    requirements = {'numpy':'numpy>=1.26,<3', 'sklearn':'scikit-learn>=1.4,<2',
                    'yaml':'PyYAML>=6,<7', 'joblib':'joblib>=1.3,<2',
                    'rank_bm25':'rank-bm25>=0.2.2,<1', 'torch':'torch',
                    'sentence_transformers':'sentence-transformers>=3,<6',
                    'lightgbm':'lightgbm>=4,<5', 'pandas':'pandas'}
    wheels = list(workspace.rglob('rank_bm25-*.whl'))
    if importlib.util.find_spec('rank_bm25') is None and len(wheels)==1:
        subprocess.run([sys.executable,'-m','pip','install','--no-index','--no-deps',str(wheels[0])],check=True)
    missing = [value for name,value in requirements.items() if importlib.util.find_spec(name) is None]
    if missing:
        subprocess.run([sys.executable,'-m','pip','install','--timeout','25','--retries','1',*missing],check=True)
    manifest_path = workspace/'offline-model-manifest.json'
    if manifest_path.exists():
        import json
        spec = importlib.util.spec_from_file_location('fashion_kaggle_runtime',source/'kaggle/run_experiment.py')
        runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runtime)
        runtime.OFFLINE_MODELS = json.loads(manifest_path.read_text(encoding='utf-8'))
        runtime.prepare_offline_models()
sys.path.insert(0, str(source / 'src'))
output = Path('/kaggle/working/fashion-reco/output')
if (workspace / 'previous-run').exists():
    shutil.copytree(workspace / 'previous-run', output, dirs_exist_ok=True)
os.environ['FASHION_CATALOG'] = str(workspace / 'catalog.json')
os.environ['FASHION_OUTPUT'] = str(output)
config_path = source / 'configs/experiment.yaml'
if EXTRAS:
    import torch, yaml
    device = globals().get('DENSE_DEVICE','cpu')
    if device not in ('cpu','cuda'):
        raise ValueError('Choose cpu or cuda explicitly')
    config = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    config['dense'].update(device=device,batch_size=8 if device=='cpu' else 16)
    if device == 'cpu':
        torch.set_num_threads(4)
    elif not torch.cuda.is_available():
        raise RuntimeError('CUDA unavailable. Choose CPU or enable an actual GPU on Kaggle.')
    config_path.write_text(yaml.safe_dump(config,sort_keys=False),encoding='utf-8')
    print('Selected cloud device:',device)
'''


def main():
    notebooks = {
        '01_eda_preprocessing.ipynb': [
            markdown('# 01 — EDA và xử lý catalog thời trang\nChạy CPU trên Kaggle. Đọc snapshot thực tế, không mặc định đủ 20.000. Chưa train model.'),
            code("EXTRAS = None  # EDA không cần pip/build dependencies.\n" + SETUP),
            code("from fashion_reco.eda_only import run_eda\nreport = run_eda(workspace/'catalog.json', output, source/'data/queries.jsonl')\nprint({k: report[k] for k in ['raw_count', 'valid_count', 'sha256', 'issues']})"),
            code("from IPython.display import HTML, display\ndisplay(HTML((output/'eda-summary.html').read_text(encoding='utf-8')))\nprint('Phân vị giá:', report['price_percentiles'])\nprint('Độ dài mô tả:', report['description_lengths'])"),
            code("missing = [row for row in report['coverage'] if row['count']==0]\nprint('Các trường hợp thiếu loại món:', len(missing))\nfor row in missing[:30]: print(row)\nprint('Xem đầy đủ eda-groups.csv và eda-query-coverage.csv trong output.')"),
            markdown('## Nhóm cần duyệt\nKiểm tra tên/loại món, mô tả, ảnh và độ phủ của 120 nhu cầu mẫu. Không biến hàng hết thành còn hàng. Duyệt nhu cầu trước khi tạo pool, đóng băng snapshot và lưu output bằng Save Version.'),
        ],
        '02_labeling_dataset.ipynb': [
            markdown('# 02 — Tạo tập ứng viên để nhóm chấm nhãn\nMặc định chạy CPU Kaggle. Dùng model và wheel offline đã gắn vào input. Tạo embedding pretrained, **chưa fine-tune**. Grade để trống; không dùng tập test để lựa chọn model.'),
            code("DENSE_DEVICE = 'cpu'\nEXTRAS = '[kaggle]'\n" + SETUP),
            code("from fashion_reco.workflow import run_stage\npool_manifest = run_stage(config_path, 'label')\nprint('Số hàng cần chấm:', pool_manifest['row_count'])\nprint('Các loại món thiếu ứng viên:', pool_manifest['empty_slots'])"),
            code("import pandas as pd\nlabels = pd.read_csv(output / 'labeling/judgments.csv')\ndisplay(labels[['query_id','query','slot','product_name','price','grade']].head(20))\nprint('Lưu thư mục:', output / 'labeling')"),
            markdown('## Chấm và đóng băng nhãn\n0: không phù hợp; 1: một phần; 2: phù hợp; 3: rất phù hợp. Điền annotator; không xóa hàng. Hai người chấm test-rater-a/b độc lập; dùng adjudicate_test rồi giải quyết các ô bất đồng trong test-adjudicated.csv. Lưu labeling và artifact thành output/dataset private cho phiên sau. Không chạy label đè pool đã chấm.'),
        ],
        '03_train_evaluate_inference.ipynb': [
            markdown('# 03 — Training, evaluation và inference\nMặc định chạy CPU Kaggle. Cần labeling/pool-manifest.json và judgments.csv đã chấm. Stage train chỉ dùng train/validation. Chỉ mở test sau khi khóa lựa chọn; cần test-adjudicated.csv và previous-run chứa selection-lock cùng artifact train.'),
            code("DENSE_DEVICE = 'cpu'\nEXTRAS = '[kaggle]'\n" + SETUP),
            code("STAGE = 'train'  # Chỉ đổi sang test sau khi chốt mô hình.\nfrom fashion_reco.workflow import run_stage\nlabeling_dir = workspace / 'labeling'\nif not labeling_dir.exists():\n    raise RuntimeError('Chưa có nhãn thật. Hoàn thành notebook 02 và upload labeling trước.')\nresult = run_stage(config_path, STAGE, labeling_dir=labeling_dir)\nprint(result)"),
            code("import pandas as pd, json\nsummary = result['validation'] if STAGE == 'train' else result['test_ranking']\ndisplay(pd.DataFrame(summary).T)\nprint('Lựa chọn khóa bằng validation:', result['selected_method'])"),
            markdown('## Xem bộ sản phẩm kèm ảnh\nSau train: xem bộ validation của hai phương án đứng đầu. Sau test: xem kết quả của phương án đã chọn. Ảnh là URL nguồn và có thể lỗi. Chưa có bảo đảm về tính tương thích thẩm mỹ.'),
            code('''from IPython.display import HTML, display
from html import escape
bundle_file = output / ('validation-bundles.json' if STAGE == 'train' else 'test-bundles.json')
if bundle_file.exists():
    bundles = json.loads(bundle_file.read_text(encoding='utf-8'))
    examples = [b for b in bundles if b['method'] == result['selected_method'] and b['mode'] == 'available_only'][:4]
    for bundle in examples:
        html = f"<h3>{escape(bundle['query_id'])} — {escape(bundle['status'])}</h3><p>Tổng: {bundle['total_price']:,} / {bundle['budget']:,} VND</p>"
        for p in bundle['items']:
            image = p['image_url'] if p['image_url'].startswith('https://') else ''
            html += f"<div style='display:inline-block;vertical-align:top;width:220px;padding:12px'><img src='{escape(image, quote=True)}' width='160'><p>{escape(p['name'])}</p><p>{p['price']:,} VND</p></div>"
        display(HTML(html))
else:
    print('Chưa có kết quả bộ sản phẩm.')'''),
            markdown('## Bàn giao\nLưu model, embedding, selection-lock, environment và build timings. Nhóm chấm validation/test-bundle-human-review.csv về đáp ứng nhu cầu và tương thích. Không chọn lại model bằng test. Peak memory là toàn process; muốn đo từng model cần process riêng.'),
        ],
    }
    destination = Path(__file__).resolve().parent.parent / 'notebooks'
    destination.mkdir(exist_ok=True)
    for name, cells in notebooks.items():
        for index, cell in enumerate(cells):
            cell['id'] = f'cell-{index:02d}'
        notebook = {'cells':cells, 'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
                                             'language_info':{'name':'python','version':'3.11'}}, 'nbformat':4,'nbformat_minor':5}
        (destination/name).write_text(json.dumps(notebook,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Generated three UTF-8 notebooks.')


if __name__ == '__main__':
    main()
