"""Package verified Colab outputs for an isolated private Kaggle CPU smoke test."""
import argparse
import ast
import base64
import hashlib
import json
from pathlib import Path
import shutil


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def stage(output, bundle, results, pseudo, model_manifest, wheel):
    output=Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    dataset,runner=output/'dataset',output/'runner'
    dataset.mkdir(parents=True);runner.mkdir()
    inputs={'workspace.bundle':bundle,'colab-results.bundle':results,'pseudo-labels.bundle':pseudo}
    for name,path in inputs.items():
        shutil.copy2(path,dataset/name)
    (dataset/'smoke-input-manifest.json').write_text(json.dumps({'files':{name:sha(path) for name,path in inputs.items()},'purpose':'pipeline_smoke_test_only'},indent=2))
    (dataset/'dataset-metadata.json').write_text(json.dumps({'id':'charlotte4306/soa-colab-15652-pseudo-smoke','title':'SOA Colab 15652 Pseudo Smoke','licenses':[{'name':'other'}]},indent=2))
    root=Path(__file__).resolve().parent
    common=(root/'run_experiment.py').read_text(encoding='utf-8')
    tree=ast.parse(common)
    helpers='\n\n'.join(ast.get_source_segment(common,n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('install_offline_wheels','prepare_offline_models'))
    models=json.loads(Path(model_manifest).read_text(encoding='utf-8'))
    for value in models.values():
        if 'model.safetensors' in value['files']:
            value['files'].pop('pytorch_model.bin',None)
    wheel=Path(wheel)
    payload={wheel.name:{'sha256':sha(wheel),'base64':base64.b64encode(wheel.read_bytes()).decode('ascii')}}
    prefix='from pathlib import Path\nimport os, shutil, subprocess, sys, zipfile, importlib.util, base64, hashlib\n'
    prefix+="WORK=Path('/kaggle/working/pseudo-smoke-15652')\nINPUT=Path('/kaggle/input')\n"
    prefix+='OFFLINE_WHEELS='+repr(payload)+'\nOFFLINE_MODELS='+repr(models)+'\n'
    code=prefix+helpers+'\n\n'+(root/'pseudo_smoke_main.py').read_text(encoding='utf-8')
    ast.parse(code)
    (runner/'run_pseudo_smoke.py').write_text(code,encoding='utf-8')
    meta={'id':'charlotte4306/soa-fashion-pseudo-smoke-15652','title':'SOA Fashion Pseudo Smoke 15652',
          'code_file':'run_pseudo_smoke.py','language':'python','kernel_type':'script','is_private':True,
          'enable_gpu':False,'enable_tpu':False,'enable_internet':True,
          'dataset_sources':['charlotte4306/soa-colab-15652-pseudo-smoke','charlotte4306/soa-e5-offline'],
          'model_sources':['yethukmutt/bge-m3/Transformers/m3/1'],'kernel_sources':[],'competition_sources':[]}
    (runner/'kernel-metadata.json').write_text(json.dumps(meta,indent=2))
    print(json.dumps({'dataset':str(dataset),'runner':str(runner)},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('output','bundle','results','pseudo','model-manifest','wheel'):
        p.add_argument('--'+name,required=True)
    args=p.parse_args();stage(args.output,args.bundle,args.results,args.pseudo,args.model_manifest,args.wheel)
