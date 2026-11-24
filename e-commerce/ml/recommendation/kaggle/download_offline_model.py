"""Transfer official weights for a private Kaggle input. Does not load any model."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.request


def checksum(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8*1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def download(record, destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    files = record['files'].copy()
    if 'model.safetensors' in files:
        files.pop('pytorch_model.bin', None)
    for name, expected in files.items():
        target = destination/name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.stat().st_size == expected['size'] and checksum(target) == expected['sha256']:
            print('Verified existing:', name, flush=True)
            continue
        partial = target.with_name(target.name+'.part')
        for attempt in range(4):
            try:
                offset = partial.stat().st_size if partial.exists() else 0
                request = urllib.request.Request(
                    f'https://huggingface.co/{record["model_id"]}/resolve/{record["revision"]}/{name}',
                    headers={'Range':f'bytes={offset}-'} if offset else {})
                with urllib.request.urlopen(request, timeout=60) as response:
                    append = offset > 0 and response.status == 206
                    if append and not response.headers.get('Content-Range','').startswith(f'bytes {offset}-'):
                        raise RuntimeError('Invalid resume range')
                    received = offset if append else 0
                    progress = received
                    with partial.open('ab' if append else 'wb') as stream:
                        while chunk := response.read(4*1024*1024):
                            stream.write(chunk)
                            received += len(chunk)
                            if received-progress >= 64*1024*1024:
                                print(f'{name}: {received:,}/{expected["size"]:,} bytes', flush=True)
                                progress = received
                if partial.stat().st_size != expected['size'] or checksum(partial) != expected['sha256']:
                    raise RuntimeError(f'Checksum/size mismatch: {name}')
                partial.replace(target)
                print('Downloaded and verified:', name, flush=True)
                break
            except Exception as exc:
                print('Transfer retry:', name, attempt+1, type(exc).__name__, flush=True)
                if attempt == 3:
                    raise
                time.sleep(3)
    transferred = dict(record, files=files)
    (destination/'official-manifest.json').write_text(json.dumps(transferred,indent=2),encoding='utf-8')
    print('Transfer complete. No embedding or training performed.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--method', choices=['e5','bge'], required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    manifest = json.loads(Path(args.manifest).read_text(encoding='utf-8'))
    download(manifest[args.method], args.output)
