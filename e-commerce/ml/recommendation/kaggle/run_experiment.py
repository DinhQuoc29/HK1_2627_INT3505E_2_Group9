"""Kaggle entrypoint. Dataset must contain source.zip, catalog.json and optional labels/previous-run."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import zipfile
import importlib.util
import base64
import hashlib

WORK = Path('/kaggle/working/fashion-reco')
INPUT = Path('/kaggle/input')
# Edit before pushing. CPU-only EDA is the safe initial stage.
STAGE = os.getenv('FASHION_STAGE', 'eda')  # eda | label | train | test
DENSE_DEVICE = 'cpu'  # Explicit cloud CPU mode; stage_run.py can select cuda.
DENSE_BATCH_SIZE = 8
OFFLINE_WHEELS = {}  # Filled by stage_run.py: filename -> sha256, base64.
OFFLINE_MODELS = {}  # Official pinned file checksums, filled by stage_run.py.


def prepare_offline_models():
    """Use mirrors only when every required file matches the official revision."""
    if not OFFLINE_MODELS:
        return
    cache = WORK / 'hf' / 'hub'
    os.environ.update(HF_HOME=str(cache.parent), HF_HUB_CACHE=str(cache),
                      HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    candidates = list(INPUT.rglob('config.json'))
    verified = {}
    for method, record in OFFLINE_MODELS.items():
        folder = None
        checks = {}
        for config in candidates:
            candidate = config.parent
            if config.stat().st_size != record['files']['config.json']['size']:
                continue
            matches = True
            candidate_checks = {}
            for name, expected in record['files'].items():
                path = candidate / name
                if not path.is_file() or path.stat().st_size != expected['size']:
                    matches = False
                    break
                digest = hashlib.sha256()
                with path.open('rb') as stream:
                    for chunk in iter(lambda: stream.read(8*1024*1024), b''):
                        digest.update(chunk)
                if digest.hexdigest() != expected['sha256']:
                    matches = False
                    break
                candidate_checks[name] = digest.hexdigest()
            if matches:
                folder, checks = candidate, candidate_checks
                break
        if folder is None:
            raise RuntimeError(f'No verified offline files for {record["model_id"]}; refusing a mismatched mirror')
        model_cache = cache / ('models--' + record['model_id'].replace('/', '--'))
        snapshot = model_cache / 'snapshots' / record['revision']
        for name in record['files']:
            target = snapshot / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.symlink_to(folder/name)
        (model_cache/'refs').mkdir(parents=True, exist_ok=True)
        (model_cache/'refs/main').write_text(record['revision'])
        verified[method] = {'model_id': record['model_id'], 'revision': record['revision'],
                            'source': str(folder), 'sha256': checks}
        print('Verified offline model:', record['model_id'], record['revision'], flush=True)
    output = WORK / 'output'
    output.mkdir(parents=True, exist_ok=True)
    import json
    (output/'offline-models.json').write_text(json.dumps(verified, indent=2))


def install_offline_wheels():
    if not OFFLINE_WHEELS:
        return
    directory = WORK / 'wheels'
    directory.mkdir(parents=True, exist_ok=True)
    for name, record in OFFLINE_WHEELS.items():
        if Path(name).name != name or not name.endswith('.whl'):
            raise ValueError('Unsafe wheel filename')
        content = base64.b64decode(record['base64'], validate=True)
        if hashlib.sha256(content).hexdigest() != record['sha256']:
            raise ValueError('Offline wheel checksum mismatch')
        wheel = directory / name
        wheel.write_bytes(content)
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-index',
                        '--no-deps', str(wheel)], check=True)


def main():
    candidates = list(INPUT.rglob('source.zip'))
    package = WORK / 'source'
    package.mkdir(parents=True, exist_ok=True)
    if len(candidates) == 1:
        workspace = candidates[0].parent
        with zipfile.ZipFile(candidates[0]) as archive:
            for member in archive.infolist():
                target = (package / member.filename).resolve()
                if not target.is_relative_to(package.resolve()):
                    raise ValueError('Unsafe archive member')
            archive.extractall(package)
    elif not candidates:
        sources = [p.parent for p in INPUT.rglob('pyproject.toml') if (p.parent/'src/fashion_reco').is_dir()]
        if len(sources) != 1:
            raise RuntimeError('Attach one workspace with source.zip or extracted source/')
        workspace = sources[0].parent
        shutil.copytree(sources[0], package, dirs_exist_ok=True)
    else:
        raise RuntimeError('Multiple source archives found')
    sys.path.insert(0, str(package / 'src'))
    output = WORK / 'output'
    if (workspace / 'previous-run').exists():
        shutil.copytree(workspace / 'previous-run', output, dirs_exist_ok=True)
    os.environ['FASHION_CATALOG'] = str(workspace / 'catalog.json')
    os.environ['FASHION_OUTPUT'] = str(output)
    if STAGE == 'eda':
        from fashion_reco.eda_only import run_eda
        run_eda(workspace/'catalog.json', output, package/'data/queries.jsonl')
        return
    install_offline_wheels()
    requirements = {
        'numpy':'numpy>=1.26,<3', 'sklearn':'scikit-learn>=1.4,<2',
        'yaml':'PyYAML>=6,<7', 'joblib':'joblib>=1.3,<2',
        'rank_bm25':'rank-bm25>=0.2.2,<1',
        'torch':'torch', 'sentence_transformers':'sentence-transformers>=3,<6',
    }
    if STAGE in ('train','test'):
        requirements['lightgbm']='lightgbm>=4,<5'
    missing = [requirement for module,requirement in requirements.items() if importlib.util.find_spec(module) is None]
    print('ML environment:', {module:importlib.util.find_spec(module) is not None for module in requirements}, flush=True)
    if missing:
        # Source is already on sys.path: do not build/install our local package.
        subprocess.run([sys.executable,'-m','pip','install','--timeout','25','--retries','1',*missing],check=True)
    import json
    import torch
    import yaml
    output.mkdir(parents=True, exist_ok=True)
    config = yaml.safe_load((package/'configs/experiment.yaml').read_text(encoding='utf-8'))
    if DENSE_DEVICE not in ('cpu','cuda'):
        raise ValueError('Choose cpu or cuda explicitly')
    config.setdefault('dense',{}).update(device=DENSE_DEVICE,batch_size=DENSE_BATCH_SIZE)
    if DENSE_DEVICE == 'cpu':
        torch.set_num_threads(4)
    (package/'configs/experiment.yaml').write_text(yaml.safe_dump(config,sort_keys=False),encoding='utf-8')
    (output/'effective-config.yaml').write_text(yaml.safe_dump(config,sort_keys=False),encoding='utf-8')
    gpu = {'torch':torch.__version__, 'torch_cuda':torch.version.cuda,
           'cuda_available':torch.cuda.is_available(), 'device_count':torch.cuda.device_count()}
    output.mkdir(parents=True, exist_ok=True)
    (output/'gpu-runtime.json').write_text(json.dumps(gpu,indent=2))
    print('Selected device:', DENSE_DEVICE, 'Actual runtime:', gpu, flush=True)
    if DENSE_DEVICE == 'cuda' and any(m not in ('tfidf','bm25') for m in config['methods']) and not gpu['cuda_available']:
        raise RuntimeError('CUDA unavailable. Verify Kaggle phone verification, actual accelerator and GPU image before retrying; no CPU fallback.')
    prepare_offline_models()
    from fashion_reco.workflow import run_stage
    result = run_stage(package / 'configs/experiment.yaml', STAGE,
                       labeling_dir=workspace / 'labeling' if (workspace / 'labeling').exists() else None)
    print(result)


if __name__ == '__main__':
    main()
