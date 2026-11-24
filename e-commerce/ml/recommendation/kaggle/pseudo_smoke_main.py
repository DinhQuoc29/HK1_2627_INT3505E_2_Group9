"""Cloud-only pseudo-label train/test on frozen Colab outputs. Not a quality benchmark."""
def main():
    import json
    import time
    WORK.mkdir(parents=True,exist_ok=True)
    candidates=list(INPUT.rglob('smoke-input-manifest.json'))
    if len(candidates)!=1:
        raise RuntimeError('Attach exactly one frozen pseudo-smoke input dataset')
    dataset=candidates[0].parent
    inputs=json.loads(candidates[0].read_text())
    def sha(path):
        digest=hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):
                digest.update(block)
        return digest.hexdigest()
    def unpack(path,root):
        root=root.resolve();root.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if chr(92) in name or not (root/name).resolve().is_relative_to(root):
                    raise ValueError('Unsafe archive path')
            archive.extractall(root)
    for name,checksum in inputs['files'].items():
        if sha(dataset/name)!=checksum:
            raise RuntimeError('Input checksum mismatch: '+name)
    workspace,source,original,output,pseudo=[WORK/name for name in ('workspace','source','original','output','pseudo')]
    unpack(dataset/'workspace.bundle',workspace)
    manifest=json.loads((workspace/'workspace-manifest.json').read_text())
    for name,field in [('catalog.json','catalog_sha256'),('source.zip','source_sha256')]:
        if sha(workspace/name)!=manifest[field]:
            raise RuntimeError('Workspace checksum mismatch')
    unpack(workspace/'source.zip',source)
    unpack(dataset/'colab-results.bundle',original)
    unpack(dataset/'pseudo-labels.bundle',pseudo)
    teacher=json.loads((pseudo/'pseudo-label-manifest.json').read_text())
    snapshot=json.loads((original/'snapshot-manifest.json').read_text())
    if teacher['purpose']!='pipeline_smoke_test_only' or teacher['catalog_sha256']!=manifest['catalog_sha256'] or snapshot['catalog_sha256']!=manifest['catalog_sha256'] or teacher['pool_sha256']!=sha(original/'labeling/pool-manifest.json'):
        raise RuntimeError('Frozen catalog/pool/teacher mismatch')
    for name,checksum in teacher['files'].items():
        if sha(pseudo/name)!=checksum:
            raise RuntimeError('Pseudo-label checksum mismatch')
    shutil.copytree(original,output,dirs_exist_ok=True)
    shutil.copy2(output/'build-timings.json',output/'colab-original-cache-load-timings.json')
    for name in teacher['files']:
        shutil.copy2(pseudo/name,output/'labeling'/name)
    shutil.copy2(pseudo/'pseudo-label-manifest.json',output/'pseudo-label-manifest.json')
    (output/'READ_ME_FIRST.txt').write_text('PSEUDO LABEL SMOKE TEST ONLY. Same deterministic teacher labels train and test. Metrics do not establish real-world recommendation quality. No human annotation or test adjudication.\n')
    install_offline_wheels()
    requirements={'numpy':'numpy','sklearn':'scikit-learn','yaml':'PyYAML','joblib':'joblib',
                  'torch':'torch','sentence_transformers':'sentence-transformers>=3,<6','lightgbm':'lightgbm>=4,<5'}
    missing=[req for module,req in requirements.items() if importlib.util.find_spec(module) is None]
    if missing:
        subprocess.run([sys.executable,'-m','pip','install','--timeout','30','--retries','1',*missing],check=True)
    import torch
    import yaml
    torch.set_num_threads(4)
    prepare_offline_models()
    sys.path.insert(0,str(source/'src'))
    config_path=source/'configs/experiment.yaml'
    config=yaml.safe_load(config_path.read_text())
    config['dense'].update(device='cpu',batch_size=8)
    config.update(catalog_path=str(workspace/'catalog.json'),output_dir=str(output))
    config_path.write_text(yaml.safe_dump(config,sort_keys=False))
    os.environ.update(FASHION_CATALOG=config['catalog_path'],FASHION_OUTPUT=config['output_dir'])
    from fashion_reco.workflow import configure,run_stage
    from fashion_reco.labeling import load_judgments
    config,products,catalog_manifest,requests,splits=configure(config_path)
    pool=json.loads((output/'labeling/pool-manifest.json').read_text())
    for filename,ids in [('judgments.csv',set(splits['train'])|set(splits['validation'])),('test-adjudicated.csv',set(splits['test']))]:
        load_judgments(output/'labeling'/filename,requests,products,pool,catalog_manifest,ids)
    fingerprint=hashlib.sha256(json.dumps([(p['id'],p['text']) for p in products],ensure_ascii=False).encode()).hexdigest()
    for method in ('e5','bge'):
        cache=output/'artifacts/dense'/method
        expected={'model_id':config['dense']['models'][method],'revision':config['dense']['revisions'][method],
                  'max_length':config['dense']['max_length'],'fingerprint':fingerprint,'method':method}
        if json.loads((cache/'index.json').read_text())!=expected or not (cache/'vectors.npy').exists():
            raise RuntimeError('Cache mismatch; stop rather than re-encode catalog')
    (output/'cloud-runtime.json').write_text(json.dumps({'platform':'Kaggle','device':'cpu','threads':4,
        'torch':torch.__version__,'cuda_available':torch.cuda.is_available(),'product_count':len(products),
        'label_origin':teacher['label_origin'],'purpose':'pipeline_smoke_test_only'},indent=2))
    print('Verified Colab cache:',len(products),'products. PSEUDO labels, Kaggle CPU.',flush=True)
    try:
        started=time.perf_counter()
        train=run_stage(config_path,'train',labeling_dir=output/'labeling')
        train['evaluation_status']='pseudo_label_smoke_test_only'
        (output/'selection-lock.json').write_text(json.dumps(train,ensure_ascii=False,indent=2))
        print('Train finished; validation teacher agreement:',train['validation'],flush=True)
        test=run_stage(config_path,'test',labeling_dir=output/'labeling')
        report={'purpose':'pipeline_smoke_test_only','warning':'Same teacher generated train/test labels; no independent quality evidence.',
                'teacher':teacher,'validation':train,'test':test,'elapsed_seconds':time.perf_counter()-started}
        (output/'pseudo-results-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
        print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    except Exception as exc:
        (output/'smoke-error.json').write_text(json.dumps({'status':'error','error':repr(exc),'purpose':'pipeline_smoke_test_only'}))
        raise


if __name__=='__main__':
    main()
