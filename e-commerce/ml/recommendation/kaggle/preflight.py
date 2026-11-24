"""Small CPU-only network/environment probe; never downloads model weights."""
import importlib.util
import json
from pathlib import Path
import socket
import urllib.request
import hashlib


def main():
    report = {'modules': {}, 'network': {}}
    for name in ('numpy', 'sklearn', 'yaml', 'joblib', 'rank_bm25', 'torch',
                 'sentence_transformers', 'lightgbm'):
        report['modules'][name] = importlib.util.find_spec(name) is not None
    urls = {
        'pypi.org': 'https://pypi.org/simple/rank-bm25/',
        'huggingface.co': 'https://huggingface.co/intfloat/multilingual-e5-base/resolve/d128750597153bb5987e10b1c3493a34e5a4502a/config.json',
    }
    for host, url in urls.items():
        result = {}
        try:
            result['dns'] = sorted({r[4][0] for r in socket.getaddrinfo(host, 443)})
            with urllib.request.urlopen(url, timeout=20) as response:
                result.update(status=response.status, bytes=len(response.read(16384)))
        except Exception as exc:
            result['error'] = f'{type(exc).__name__}: {exc}'
        report['network'][host] = result
    report['model_files'] = []
    for config in Path('/kaggle/input').rglob('config.json'):
        if any(part in config.parts for part in ('source', 'onnx', '1_Pooling', 'openvino')):
            continue
        folder = config.parent
        files = []
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                record = {'path': str(path), 'size': path.stat().st_size}
                if path.suffix in ('.safetensors', '.json', '.model', '.bin'):
                    digest = hashlib.sha256()
                    with path.open('rb') as stream:
                        for chunk in iter(lambda: stream.read(8*1024*1024), b''):
                            digest.update(chunk)
                    record['sha256'] = digest.hexdigest()
                files.append(record)
        report['model_files'].append({'config': str(config), 'files': files})
    print(json.dumps(report, indent=2), flush=True)
    Path('/kaggle/working/preflight.json').write_text(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
