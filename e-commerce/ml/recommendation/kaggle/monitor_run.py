"""Monitor an existing Kaggle run and download selected outputs. Never submits work."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT.parents[1] / '.venv-kaggle/Scripts/python.exe'
WRAPPER = ROOT / 'kaggle/kaggle_ipv4.py'


def call(*args, timeout=120):
    result = subprocess.run([str(PYTHON), str(WRAPPER), *args], capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=timeout,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout)[-1500:])
    return result.stdout


def monitor(kernel, directory, pattern):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    while not (directory / 'monitor.stop').exists():
        try:
            status = call('kernels', 'status', kernel)
            print(datetime.now().isoformat(), status.strip(), flush=True)
            if 'complete' in status.lower():
                call('kernels', 'output', kernel, '-p', str(directory), '--file-pattern', pattern, timeout=600)
                pools = list(directory.rglob('pool-manifest.json'))
                summary = {'kernel':kernel, 'status':'complete', 'downloaded_at':datetime.now().astimezone().isoformat()}
                if pools:
                    pool = json.loads(pools[0].read_text(encoding='utf-8'))
                    summary.update(annotation_rows=pool['row_count'], catalog_sha256=pool['catalog_sha256'],
                                   empty_slots=pool['empty_slots'])
                (directory/'run-status.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
                print('Output downloaded:', summary, flush=True)
                return
            if any(word in status.lower() for word in ('error','failed','cancelled')):
                logs = call('kernels','logs',kernel)
                (directory/'remote-error.log').write_text(logs,encoding='utf-8')
                (directory/'run-status.json').write_text(json.dumps({'kernel':kernel,'status':'error'}))
                print('Remote run failed. Logs saved; no automatic GPU resubmission.',flush=True)
                return
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            print('Monitor retry:',str(exc),flush=True)
        for _ in range(6):
            if (directory/'monitor.stop').exists():
                return
            time.sleep(10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kernel',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--pattern',default=r'fashion-reco/output/(labeling/.*|build-timings.json|environment.json|offline-models.json|gpu-runtime.json|effective-config.yaml)$')
    args = parser.parse_args()
    monitor(args.kernel,args.output,args.pattern)
