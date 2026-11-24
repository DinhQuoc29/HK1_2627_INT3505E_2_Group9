"""Freeze a requested catalog and prepare an upload notebook. No local ML runs."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile


def markdown(text, index):
    return {'cell_type':'markdown','id':f'cell-{index:02d}','metadata':{},'source':text.splitlines(True)}


def code(text, index):
    return {'cell_type':'code','id':f'cell-{index:02d}','metadata':{},'execution_count':None,
            'outputs':[],'source':text.splitlines(True)}


def notebook(manifest, bundle_name):
    cells=[]
    def md(value): cells.append(markdown(value,len(cells)))
    def py(value): cells.append(code(value,len(cells)))
    md(f'''# Recommendation thời trang — {manifest['product_count']:,} sản phẩm — Colab GPU

Lượt độc lập với Kaggle. Chạy **Runtime → Change runtime type → GPU** rồi **Run all**.
Chỉ upload `{bundle_name}` ở ô chọn file. Model tải trực tiếp từ Hugging Face trên Colab.

Quy trình: kiểm tra GPU → dữ liệu và source đã đóng băng → EDA → TF-IDF/BM25/E5/BGE-M3 → tập ứng viên → preview → tải artifact.
Đây là bước tạo ứng viên để nhóm chấm nhãn, **chưa train LambdaMART hoặc chọn mô hình tốt nhất**.
Nhãn không tự sinh. Không so sánh trực tiếp tốc độ Colab GPU với Kaggle CPU như thí nghiệm cùng điều kiện.
''')
    py('''from pathlib import Path
import sys, os, json, hashlib, zipfile, subprocess, importlib.util
if importlib.util.find_spec('google.colab') is None:
    raise RuntimeError('Notebook này chỉ chạy trên Google Colab hosted runtime, không chạy ML trên máy cá nhân.')
import torch
if not torch.cuda.is_available():
    raise RuntimeError('Chưa có GPU CUDA. Chọn Runtime > Change runtime type > GPU và kết nối lại.')
print('GPU:', torch.cuda.get_device_name(0))
print('PyTorch:', torch.__version__, 'CUDA:', torch.version.cuda)
WORK = Path('/content/fashion-colab-15652')
WORK.mkdir(parents=True, exist_ok=True)
''')
    py(f'''from google.colab import files
BUNDLE_NAME = {bundle_name!r}
BUNDLE_SHA256 = {manifest['bundle_sha256']!r}
os.chdir(WORK)
bundle = WORK/BUNDLE_NAME
if not bundle.exists():
    uploaded = files.upload()
    if BUNDLE_NAME not in uploaded:
        raise RuntimeError('Hãy upload đúng file ' + BUNDLE_NAME)
    del uploaded
if hashlib.sha256(bundle.read_bytes()).hexdigest() != BUNDLE_SHA256:
    raise RuntimeError('Bundle không khớp snapshot đã đóng băng.')
workspace = WORK/'workspace'
workspace.mkdir(exist_ok=True)
def extract_checked(archive_path, destination):
    destination = destination.resolve()
    with zipfile.ZipFile(archive_path) as archive:
        for item in archive.infolist():
            if not (destination/item.filename).resolve().is_relative_to(destination):
                raise ValueError('Unsafe archive member')
        archive.extractall(destination)
extract_checked(bundle,workspace)
source = WORK/'source'
source.mkdir(exist_ok=True)
extract_checked(workspace/'source.zip',source)
manifest = json.loads((workspace/'workspace-manifest.json').read_text(encoding='utf-8'))
for name, field in [('catalog.json','catalog_sha256'),('source.zip','source_sha256')]:
    if hashlib.sha256((workspace/name).read_bytes()).hexdigest() != manifest[field]:
        raise RuntimeError('Sai checksum: '+name)
raw = json.loads((workspace/'catalog.json').read_text(encoding='utf-8'))
if len(raw) != {manifest['product_count']} or len({{str(p['productId']) for p in raw}}) != len(raw):
    raise RuntimeError('Sai số lượng hoặc trùng productId.')
print('Snapshot:', len(raw), 'sản phẩm', manifest['catalog_sha256'])
del raw
''')
    py('''requirements = {
    'numpy':'numpy>=1.26,<3', 'sklearn':'scikit-learn>=1.4,<2',
    'yaml':'PyYAML>=6,<7', 'joblib':'joblib>=1.3,<2',
    'sentence_transformers':'sentence-transformers>=3,<6', 'pandas':'pandas'
}
if importlib.util.find_spec('rank_bm25') is None:
    wheel = next((workspace/'offline-wheels').glob('rank_bm25-*.whl'))
    subprocess.run([sys.executable,'-m','pip','install','--no-index','--no-deps',str(wheel)],check=True)
missing = [req for name,req in requirements.items() if importlib.util.find_spec(name) is None]
if missing:
    subprocess.run([sys.executable,'-m','pip','install','--timeout','60','--retries','2',*missing],check=True)
sys.path.insert(0,str(source/'src'))
import yaml
config_path = source/'configs/experiment.yaml'
config = yaml.safe_load(config_path.read_text(encoding='utf-8'))
config['dense'].update(device='cuda',batch_size=16)
config['catalog_path'] = str(workspace/'catalog.json')
config['output_dir'] = str(WORK/'output')
config_path.write_text(yaml.safe_dump(config,sort_keys=False),encoding='utf-8')
os.environ['FASHION_CATALOG'] = config['catalog_path']
os.environ['FASHION_OUTPUT'] = config['output_dir']
output = Path(config['output_dir'])
output.mkdir(exist_ok=True)
(output/'snapshot-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Model revisions:', config['dense']['revisions'])
''')
    md('## EDA của snapshot mới\nBáo cáo này thuộc riêng 15.652 sản phẩm. Giữ nguyên trạng thái tồn kho của nguồn.')
    py('''from fashion_reco.eda_only import run_eda
eda = run_eda(workspace/'catalog.json',output,source/'data/queries.jsonl')
print({k:eda[k] for k in ['raw_count','valid_count','inventory_statuses','issues']})
from IPython.display import HTML, display
display(HTML((output/'eda-summary.html').read_text(encoding='utf-8')))
''')
    md('## Tạo tập ứng viên trên GPU\nE5/BGE là embedding pretrained. Giữ ô chạy này để xem tiến độ. Chạy lại trên cùng runtime sẽ dùng lại index đã lưu khi fingerprint và revision khớp.')
    py('''from fashion_reco.workflow import run_stage
pool = run_stage(config_path,'label')
print('Số dòng cần chấm:', pool['row_count'])
print('Thiếu ứng viên:', pool['empty_slots'])
''')
    md('## Xem bộ sản phẩm mẫu có ảnh\nPreview thử nghiệm theo tổng ngân sách, tách khỏi yêu cầu V1 cap từng món. Bộ lọc roles/giá/tồn kho không bảo đảm phối màu, kích cỡ hoặc thẩm mỹ.')
    py('''from fashion_reco.workflow import configure, build_retrievers, benchmark
from fashion_reco.inference import recommend
from fashion_reco.data import dump_json
from html import escape
cfg, products, catalog_manifest, requests, splits = configure(config_path)
# Tải lại retriever từ cache vector đã tạo, không encode lại catalog.
retrievers = build_retrievers(cfg,products)
examples = []
for request in [q for q in requests if q.query_id in splits['validation']][:3]:
    for method in cfg['methods']:
        result = recommend(request,products,{'retrievers':retrievers,'ranker':None},method=method,mode='available_only')
        examples.append({'query':request.text,**result})
        html = f'<h3>{escape(method)} — {escape(request.text)}</h3><p>{escape(result["status"])}: {result["total_price"]:,}/{request.budget:,} VND</p>'
        for item in result['items']:
            image = item['image_url'] if item['image_url'].startswith('https://') else ''
            html += f'<div style="display:inline-block;vertical-align:top;width:210px;padding:10px"><img width="150" src="{escape(image,quote=True)}"><p>{escape(item["name"])}</p><p>{item["price"]:,} VND</p></div>'
        display(HTML(html))
dump_json(output/'bundle-previews.json',examples)
validation = [q for q in requests if q.query_id in splits['validation']]
timings = benchmark(validation,products,retrievers)
dump_json(output/'colab-latency.json',{'hardware':torch.cuda.get_device_name(0),'catalog_sha256':catalog_manifest['sha256'],'latency':timings,'quality_metrics':None})
import pandas as pd
display(pd.DataFrame(timings).T)
''')
    md('## Tải kết quả và chấm nhãn\nRuntime Colab có thể ngắt hoặc hết thời gian. Tải artifact để giữ embedding và kết quả. Nhóm chấm judgments.csv, test-rater-a.csv và test-rater-b.csv theo hướng dẫn. Chưa chạy train/test khi chưa có nhãn thật.')
    py('''import shutil
archive = shutil.make_archive(str(WORK/'colab-15652-artifacts'),'zip',root_dir=output)
print('Artifact:',archive)
files.download(archive)
''')
    return {'cells':cells,'metadata':{'colab':{'name':'Fashion_15652_Colab_GPU.ipynb'},
            'accelerator':'GPU','kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},
            'nbformat':4,'nbformat_minor':5}


def prepare(catalog,output,count=15652):
    root = Path(__file__).resolve().parents[1]
    output = Path(output).resolve()
    if not output.is_relative_to(root/'artifacts'):
        raise ValueError('Write frozen Colab uploads below recommendation/artifacts')
    output.mkdir(parents=True,exist_ok=True)
    if (output/'fashion-colab-15652.zip').exists():
        raise FileExistsError('Snapshot already exists; preserve it and choose a new folder')
    raw = json.loads(Path(catalog).read_text(encoding='utf-8'))
    if len(raw)<count:
        raise ValueError('Source does not contain the requested number of products')
    snapshot = raw[:count]
    if len({str(p['productId']) for p in snapshot}) != count:
        raise ValueError('Duplicate productId in snapshot')
    source_count=len(raw)
    frozen = output/'snapshot-input.json'
    frozen.write_text(json.dumps(snapshot,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    spec=importlib.util.spec_from_file_location('kaggle_workspace_prepare',root/'kaggle/prepare_workspace.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    workspace=output/'workspace'
    module.prepare(frozen,workspace,wheels=[root/'artifacts/offline-wheels/rank_bm25-0.2.2-py3-none-any.whl'])
    info=json.loads((workspace/'workspace-manifest.json').read_text(encoding='utf-8'))
    info.update(product_count=count,source_count_at_freeze=source_count,
                frozen_at=datetime.now(timezone.utc).isoformat(),selection='First requested products in preserved collection order',
                platform='Colab GPU, independent from Kaggle 13538 snapshot')
    (workspace/'workspace-manifest.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    bundle=output/'fashion-colab-15652.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(workspace.rglob('*')):
            if file.is_file():
                archive.write(file,file.relative_to(workspace).as_posix())
    info['bundle_sha256']=hashlib.sha256(bundle.read_bytes()).hexdigest()
    (output/'bundle-manifest.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    nb=output/'Fashion_15652_Colab_GPU.ipynb'
    nb.write_text(json.dumps(notebook(info,bundle.name),ensure_ascii=False,indent=2),encoding='utf-8')
    frozen.unlink()  # Only our temporary input copy; the frozen catalog is in workspace/.
    print(json.dumps({'count':count,'source_count':source_count,'bundle':str(bundle),'bytes':bundle.stat().st_size,'notebook':str(nb)},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--count',type=int,default=15652)
    args=parser.parse_args()
    prepare(args.catalog,args.output,args.count)
