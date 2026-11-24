"""Build upload files locally; does not upload or train anything."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile


def prepare(catalog, output, labeling=None, previous_run=None, model_manifest=None, wheels=()):
    root = Path(__file__).resolve().parent.parent
    catalog, output = Path(catalog).resolve(), Path(output).resolve()
    if output == root or root.is_relative_to(output):
        raise ValueError('Choose a dedicated output folder, not the source root or its parent')
    if output.is_relative_to(root) and not output.is_relative_to(root / 'artifacts'):
        raise ValueError('Inside this package, put upload workspaces under artifacts/')
    output.mkdir(parents=True, exist_ok=True)
    if (output / 'source.zip').exists():
        raise FileExistsError('Use a fresh output directory to preserve prior frozen workspace')
    with zipfile.ZipFile(output / 'source.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for folder in ('src', 'configs', 'notebooks'):
            for path in sorted((root / folder).rglob('*')):
                if path.is_file() and '__pycache__' not in path.parts and not any(p.endswith('.egg-info') for p in path.parts):
                    archive.write(path, path.relative_to(root).as_posix())
        for name in ('pyproject.toml', 'README.md', 'data/README.md', 'data/queries.jsonl', 'data/splits.json'):
            archive.write(root / name, name)
        archive.write(root/'kaggle/run_experiment.py', 'kaggle/run_experiment.py')
    shutil.copyfile(catalog, output / 'catalog.json')
    if labeling:
        shutil.copytree(Path(labeling), output / 'labeling', dirs_exist_ok=False)
    if previous_run:
        shutil.copytree(Path(previous_run), output / 'previous-run', dirs_exist_ok=False)
    if model_manifest:
        manifest = json.loads(Path(model_manifest).read_text(encoding='utf-8'))
        for record in manifest.values():
            if 'model.safetensors' in record['files']:
                record['files'].pop('pytorch_model.bin', None)
        (output/'offline-model-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    if wheels:
        (output/'offline-wheels').mkdir()
        for wheel in wheels:
            wheel = Path(wheel)
            if wheel.suffix != '.whl':
                raise ValueError('Expected a wheel file')
            shutil.copyfile(wheel, output/'offline-wheels'/wheel.name)
    info = {'catalog_sha256': hashlib.sha256(catalog.read_bytes()).hexdigest(),
            'source_sha256': hashlib.sha256((output/'source.zip').read_bytes()).hexdigest(),
            'note': 'Upload privately. No credentials included. Review data provenance/licensing before distribution.'}
    (output / 'workspace-manifest.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
    print(f'Prepared workspace at {output}; no remote changes made.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--labeling')
    parser.add_argument('--previous-run')
    parser.add_argument('--model-manifest')
    parser.add_argument('--wheel', action='append', default=[])
    args = parser.parse_args()
    prepare(args.catalog, args.output, args.labeling, args.previous_run, args.model_manifest, args.wheel)
