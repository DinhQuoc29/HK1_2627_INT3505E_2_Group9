"""Wait for the existing GPU probe, submit one label job, then retrieve outputs.

No model computation runs locally. Never resubmits a failed or uncertain GPU job.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time

from monitor_run import call, monitor
from stage_run import stage_run

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT/'artifacts'
STATE = ARTIFACTS/'label-resume-state.json'
STOP = ARTIFACTS/'label-resume.stop'
PROBE = 'charlotte4306/soa-gpu-probe'
KERNEL = 'charlotte4306/soa-fashion-labeling'


def save(phase, **details):
    state = {'phase':phase, 'updated_at':datetime.now(timezone.utc).isoformat(), **details}
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(state,indent=2),encoding='utf-8')
    temporary.replace(STATE)
    print(json.dumps(state),flush=True)


def main():
    if STATE.exists():
        old = json.loads(STATE.read_text(encoding='utf-8'))
        if old['phase'] in ('submission_requested','label_running','complete','label_error'):
            raise RuntimeError('A submission is already recorded. Inspect its status; do not submit twice.')
    deadline = time.monotonic()+3600
    while not STOP.exists() and time.monotonic()<deadline:
        status = call('kernels','status',PROBE).strip()
        if 'complete' in status.lower():
            directory = ARTIFACTS/'gpu-probe-verified'
            call('kernels','output',PROBE,'-p',str(directory),
                 '--file-pattern',r'^gpu-probe.json$',timeout=180)
            gpu = json.loads((directory/'gpu-probe.json').read_text(encoding='utf-8'))
            if not gpu.get('cuda_available') or gpu.get('devices',0)<1:
                save('waiting_for_gpu_access',gpu=gpu)
                return
            save('gpu_verified',gpu=gpu)
            break
        if any(word in status.lower() for word in ('error','failed','cancelled')):
            save('probe_error',status=status)
            return
        save('waiting_for_probe',status=status)
        for _ in range(6):
            if STOP.exists():
                save('stopped_before_submission')
                return
            time.sleep(10)
    else:
        save('stopped_or_queue_timeout')
        return
    if STOP.exists():
        save('stopped_before_submission')
        return
    staged = ARTIFACTS/'kaggle-label-run'
    stage_run(staged,'label',KERNEL,
              [ARTIFACTS/'offline-wheels/rank_bm25-0.2.2-py3-none-any.whl'],
              ARTIFACTS/'official-model-manifest.json',
              ['yethukmutt/bge-m3/transformers/m3/1'],['charlotte4306/soa-e5-offline'],device='cuda')
    # Persist before the API call: a network error must not cause another submission.
    save('submission_requested',kernel=KERNEL)
    response = call('kernels','push','-p',str(staged),'--accelerator','NvidiaTeslaT4','-t','3600')
    version = re.search(r'Kernel version (\d+)',response)
    save('label_running',kernel=KERNEL,version=int(version[1]) if version else None,response=response)
    output = ARTIFACTS/'kaggle-label-latest'
    monitor(KERNEL,output,r'fashion-reco/output/(labeling/.*|build-timings.json|environment.json|offline-models.json|gpu-runtime.json)$')
    result = json.loads((output/'run-status.json').read_text(encoding='utf-8'))
    save('complete' if result['status']=='complete' else 'label_error',result=result)


if __name__ == '__main__':
    main()
