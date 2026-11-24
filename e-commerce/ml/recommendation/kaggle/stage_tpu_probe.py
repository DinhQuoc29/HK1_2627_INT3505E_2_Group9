"""Stage only a tiny TPU probe; does not change the active CPU experiment."""
import ast
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
folder = root/'artifacts/tpu-probe'
folder.mkdir(parents=True,exist_ok=True)
code = (root/'kaggle/tpu_probe.py').read_text(encoding='utf-8')
ast.parse(code)
notebook = {'cells':[{'id':'tpu-check','cell_type':'code','metadata':{},
                      'source':code,'execution_count':None,'outputs':[]}],
            'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},
            'nbformat':4,'nbformat_minor':5}
(folder/'probe.ipynb').write_text(json.dumps(notebook,indent=2),encoding='utf-8')
metadata = {'id':'charlotte4306/soa-tpu-probe','title':'SOA TPU Probe','code_file':'probe.ipynb',
            'language':'python','kernel_type':'notebook','is_private':True,
            'enable_gpu':False,'enable_tpu':True,'enable_internet':True,
            'docker_image_pinning_type':'latest','machine_shape':'TpuV5E8',
            'dataset_sources':[],'kernel_sources':[],'competition_sources':[]}
(folder/'kernel-metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
print('Staged TPU probe; no local computation or cloud submission.')
