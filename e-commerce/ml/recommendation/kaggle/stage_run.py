"""Prepare a private Kaggle runner with small, verified offline wheel payloads."""
import argparse
import base64
import hashlib
import json
from pathlib import Path


def stage_run(output, stage, kernel, wheels, model_manifest=None, model_sources=(), dataset_sources=(), device='cpu'):
    root = Path(__file__).resolve().parent
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    if device not in ('cpu','cuda'):
        raise ValueError('device must be cpu or cuda')
    payload = {}
    for wheel in wheels:
        wheel = Path(wheel)
        content = wheel.read_bytes()
        if wheel.suffix != '.whl' or len(content) > 1_000_000:
            raise ValueError('Only small wheels can be embedded in the runner')
        payload[wheel.name] = {'sha256': hashlib.sha256(content).hexdigest(),
                               'base64': base64.b64encode(content).decode('ascii')}
    code = (root/'run_experiment.py').read_text(encoding='utf-8')
    code = code.replace("os.getenv('FASHION_STAGE', 'eda')", f"os.getenv('FASHION_STAGE', {stage!r})")
    code = code.replace("DENSE_DEVICE = 'cpu'", f'DENSE_DEVICE = {device!r}')
    if device == 'cuda':
        code = code.replace('DENSE_BATCH_SIZE = 8','DENSE_BATCH_SIZE = 16')
    code = code.replace('OFFLINE_WHEELS = {}', 'OFFLINE_WHEELS = ' + repr(payload))
    if model_manifest:
        manifest = json.loads(Path(model_manifest).read_text(encoding='utf-8'))
        for record in manifest.values():
            if 'model.safetensors' in record['files']:
                record['files'].pop('pytorch_model.bin', None)
        code = code.replace('OFFLINE_MODELS = {}', 'OFFLINE_MODELS = ' + repr(manifest))
    (output/'run_experiment.py').write_text(code, encoding='utf-8')
    metadata = json.loads((root/'kernel-metadata.json').read_text(encoding='utf-8'))
    metadata.update(id=kernel, title='SOA Fashion Labeling' if stage=='label' else 'SOA Fashion Recommendation Experiments',
                    enable_gpu=stage!='eda' and device=='cuda')
    metadata['model_sources'] = list(model_sources)
    metadata['dataset_sources'] += list(dataset_sources)
    (output/'kernel-metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(f'Staged {stage} on {device}: {len(payload)} offline wheels; no remote execution.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--stage', choices=['eda', 'label', 'train', 'test'], required=True)
    parser.add_argument('--kernel', required=True)
    parser.add_argument('--wheel', action='append', default=[])
    parser.add_argument('--model-manifest')
    parser.add_argument('--model-source', action='append', default=[])
    parser.add_argument('--dataset-source', action='append', default=[])
    parser.add_argument('--device', choices=['cpu','cuda'], default='cpu')
    args = parser.parse_args()
    stage_run(args.output, args.stage, args.kernel, args.wheel,
              args.model_manifest, args.model_source, args.dataset_source, args.device)
