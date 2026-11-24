"""Fetch tiny official metadata only, never model weights or training."""
import hashlib
import json
from pathlib import Path
import urllib.request

MODELS = {
    'e5': ('intfloat/multilingual-e5-base', 'd128750597153bb5987e10b1c3493a34e5a4502a'),
    'bge': ('BAAI/bge-m3', '5617a9f61b028005a4858fdac845db406aefb181'),
}


def main():
    manifest = {}
    for method, (repo, revision) in MODELS.items():
        url = f'https://huggingface.co/api/models/{repo}/revision/{revision}?blobs=true'
        with urllib.request.urlopen(url, timeout=40) as response:
            metadata = json.load(response)
        files = {}
        for item in metadata['siblings']:
            name = item['rfilename']
            if name.endswith(('.json', '.model', '.safetensors', '.bin')) and not name.startswith(('onnx/', 'openvino/')):
                if item.get('lfs'):
                    files[name] = {'sha256': item['lfs']['sha256'], 'size': item['lfs']['size']}
                else:
                    with urllib.request.urlopen(f'https://huggingface.co/{repo}/resolve/{revision}/{name}', timeout=40) as response:
                        content = response.read(10_000_000)
                    files[name] = {'sha256': hashlib.sha256(content).hexdigest(), 'size': len(content)}
        manifest[method] = {'model_id': repo, 'revision': revision, 'files': files}
    destination = Path(__file__).resolve().parents[1]/'artifacts/official-model-manifest.json'
    destination.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Saved official metadata/checksums:', destination)


if __name__ == '__main__':
    main()
