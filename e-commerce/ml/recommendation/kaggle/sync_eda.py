"""Upload the frozen workspace privately, run EDA remotely, and retrieve output.

Retries network failures every 3 minutes. Stop by creating artifacts/sync-eda.stop.
No local preprocessing, embedding or training is performed.
"""
import hashlib
import csv
import io
import json
from pathlib import Path
import subprocess
import time
import urllib.request
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = ROOT / 'artifacts/upload-v1'
STATE = ROOT / 'artifacts/sync-eda-state.json'
STOP = ROOT / 'artifacts/sync-eda.stop'
CLI = ROOT.parents[1] / '.venv-kaggle/Scripts/kaggle.exe'
DATASET = 'charlotte4306/soa-ml-workspace'
KERNEL = 'charlotte4306/soa-fashion-recommendation-experiments'


def save(state):
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, indent=2), encoding='utf-8')
    temporary.replace(STATE)


def log(message):
    print(time.strftime('%Y-%m-%d %H:%M:%S'), message, flush=True)


def cli(*args, timeout=180):
    result = subprocess.run([str(CLI.with_name('python.exe')), str(ROOT/'kaggle/kaggle_ipv4.py'), *args], capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=timeout,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout)[-2000:])
    return result.stdout


def reachable():
    try:
        with urllib.request.urlopen('https://api.kaggle.com', timeout=12):
            pass
    except HTTPError:
        pass  # Any HTTP response proves TLS/network reachability, not authentication.


def main():
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    manifest = json.loads((WORKSPACE/'workspace-manifest.json').read_text())
    fingerprint = manifest['catalog_sha256'] + ':' + manifest['source_sha256']
    if state.get('fingerprint') not in (None, fingerprint):
        raise RuntimeError('Workspace changed while synchronization was pending; use a fresh state/run.')
    if hashlib.sha256((WORKSPACE/'catalog.json').read_bytes()).hexdigest() != manifest['catalog_sha256']:
        raise ValueError('Frozen catalog hash mismatch')
    state['fingerprint'] = fingerprint
    save(state)
    metadata = {'title':'SOA ML Workspace', 'id':DATASET,
                'licenses':[{'name':'other'}],
                'description':'Private research snapshot of Tiki product metadata and project code. '
                              'Source catalog provenance is preserved; no customer histories. '
                              'Other license: source rights retained; not a public-domain grant.'}
    (WORKSPACE/'dataset-metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    log(f'Started private Kaggle EDA sync, catalog={manifest.get("product_count")}.')
    while not STOP.exists():
        try:
            if not state.get('uploaded'):
                listing = cli('datasets','list','--mine','--csv','-s','soa-ml-workspace')
                exists = any(row.get('ref', '').strip() == DATASET for row in csv.DictReader(io.StringIO(listing)))
                if exists:
                    cli('datasets','version','-p',str(WORKSPACE),'-m','Frozen snapshot for EDA: '+manifest['catalog_sha256'][:12],
                        '--keep-tabular',timeout=600)
                else:
                    # Absence of --public is intentional: private dataset.
                    cli('datasets','create','-p',str(WORKSPACE),'--keep-tabular',timeout=600)
                state['uploaded'] = True
                save(state)
                log('Private dataset uploaded; waiting for Kaggle processing.')
                time.sleep(30)
            if not state.get('submitted'):
                cli('kernels','push','-p',str(ROOT/'kaggle'),timeout=180)
                state['submitted'] = True
                save(state)
                log('EDA submitted to Kaggle CPU runtime.')
            status = cli('kernels','status',KERNEL)
            log(status.strip())
            if 'complete' in status.lower():
                destination = ROOT/'artifacts/kaggle-eda-latest'
                cli('kernels','output',KERNEL,'-p',str(destination),timeout=600)
                state['downloaded'] = True
                state['output_dir'] = str(destination)
                save(state)
                log('EDA complete; outputs downloaded.')
                return
            if any(word in status.lower() for word in ('error', 'failed', 'cancelled')):
                destination = ROOT/'artifacts/kaggle-eda-failed'
                try:
                    cli('kernels','output',KERNEL,'-p',str(destination),timeout=180)
                except Exception as exc:
                    log(f'Could not download failed-run output: {exc}')
                state['remote_error'] = status
                save(state)
                raise SystemExit('Remote notebook failed; inspect logs before resubmitting.')
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            log(f'Pending; retry in 3 minutes: {exc}')
        for _ in range(18):
            if STOP.exists():
                log('Stopped by flag.')
                return
            time.sleep(10)


if __name__ == '__main__':
    main()
