"""Inspect actual cloud GPU allocation without model data or training."""
import json
from pathlib import Path
import subprocess
import sys

report = {'python':sys.version}
try:
    result = subprocess.run(['nvidia-smi'],capture_output=True,text=True,timeout=15)
    report['nvidia_smi'] = {'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
except Exception as exc:
    report['nvidia_smi'] = {'error':str(exc)}
try:
    import torch
    report.update(torch=torch.__version__,torch_cuda=torch.version.cuda,
                  cuda_available=torch.cuda.is_available(),devices=torch.cuda.device_count())
except Exception as exc:
    report['torch_error'] = str(exc)
Path('/kaggle/working/gpu-probe.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
