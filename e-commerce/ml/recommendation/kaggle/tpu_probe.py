"""Probe a real TPU computation remotely before adapting the encoder pipeline."""
import importlib.util
import importlib.metadata
import json
import os
from pathlib import Path

report = {'tpu_available':False, 'modules':{}, 'versions':{}}
for name in ('torch','torch_xla','torch_tpu','sentence_transformers','transformers'):
    report['modules'][name] = importlib.util.find_spec(name) is not None
for name in ('torch','torch-xla','torch_tpu','sentence-transformers','transformers'):
    try:
        report['versions'][name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        pass
try:
    import torch
    if report['modules']['torch_tpu']:
        import torch_tpu
        device = torch.device('tpu')
        value = torch.tensor([1.,2.],device=device).sum().cpu().item()
        report.update(backend='torch_tpu',device=str(device),result=value)
        report['tpu_available'] = device.type=='tpu' and value==3.
    elif report['modules']['torch_xla']:
        # Support the legacy runtime when that is what the Kaggle image supplies.
        os.environ['PJRT_DEVICE'] = 'TPU'
        import torch_xla
        import torch_xla.runtime as xr
        device = torch_xla.device()
        value = torch.tensor([1.,2.],device=device).sum().cpu().item()
        report.update(backend='torch_xla',device=str(device),device_type=xr.device_type(),result=value)
        report['tpu_available'] = xr.device_type()=='TPU' and value==3.
    else:
        raise RuntimeError('No TPU backend installed in assigned environment. Check actual TPU allocation/image.')
except Exception as exc:
    report['error'] = f'{type(exc).__name__}: {exc}'
Path('/kaggle/working/tpu-probe.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
