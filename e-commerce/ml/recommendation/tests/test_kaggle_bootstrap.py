import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import hashlib
import base64
import json
import shutil
from types import SimpleNamespace


class BootstrapTests(unittest.TestCase):
    def runner(self):
        path = Path(__file__).resolve().parents[1] / 'kaggle/run_experiment.py'
        spec = importlib.util.spec_from_file_location('kaggle_runner_offline_test', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_offline_model_checksum_mismatch_rejected(self):
        module = self.runner()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            candidate = root/'input/model'
            candidate.mkdir(parents=True)
            (candidate/'config.json').write_bytes(b'{}')
            (candidate/'model.safetensors').write_bytes(b'bad')
            manifest = {'e5': {'model_id':'fixture/model', 'revision':'abc', 'files': {
                'config.json': {'size':2, 'sha256':hashlib.sha256(b'{}').hexdigest()},
                'model.safetensors': {'size':3, 'sha256':hashlib.sha256(b'good').hexdigest()},
            }}}
            with patch.object(module,'WORK',root/'working'), patch.object(module,'INPUT',root/'input'), \
                    patch.object(module,'OFFLINE_MODELS',manifest), patch.dict(os.environ):
                with self.assertRaisesRegex(RuntimeError, 'No verified offline files'):
                    module.prepare_offline_models()
                self.assertFalse((root/'working/output/offline-models.json').exists())

    def test_dense_job_stops_before_model_processing_without_gpu(self):
        module = self.runner()
        fake_torch = SimpleNamespace(__version__='fixture+cpu',version=SimpleNamespace(cuda=None),
                                     cuda=SimpleNamespace(is_available=lambda:False,device_count=lambda:0))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root/'input/workspace/source'
            (source/'src/fashion_reco').mkdir(parents=True)
            (source/'configs').mkdir()
            (source/'pyproject.toml').write_text('[project]\nname="fixture"\n')
            (source/'configs/experiment.yaml').write_text('methods: [tfidf, bm25, e5, bge]\n')
            old_path = sys.path.copy()
            try:
                with patch.object(module,'WORK',root/'working'), patch.object(module,'INPUT',root/'input'), \
                        patch.object(module,'STAGE','label'), patch.object(module,'DENSE_DEVICE','cuda'), \
                        patch.dict(sys.modules,{'torch':fake_torch}), \
                        patch.object(module.importlib.util,'find_spec',return_value=object()), \
                        patch.object(module,'prepare_offline_models') as prepare_models, patch.dict(os.environ):
                    with self.assertRaisesRegex(RuntimeError,'CUDA unavailable'):
                        module.main()
                    prepare_models.assert_not_called()
                    gpu = json.loads((root/'working/output/gpu-runtime.json').read_text())
                    self.assertFalse(gpu['cuda_available'])
            finally:
                sys.path[:] = old_path

    def test_explicit_cpu_job_overrides_frozen_cuda_config(self):
        module = self.runner()
        fake_torch = SimpleNamespace(__version__='fixture+cpu',version=SimpleNamespace(cuda=None),
                                     set_num_threads=lambda count:None,
                                     cuda=SimpleNamespace(is_available=lambda:False,device_count=lambda:0))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root/'input/workspace/source'
            (source/'src/fashion_reco').mkdir(parents=True)
            (source/'configs').mkdir()
            (source/'pyproject.toml').write_text('[project]\nname="fixture"\n')
            (source/'configs/experiment.yaml').write_text('methods: [e5, bge]\ndense:\n  device: cuda\n  batch_size: 16\n')
            old_path = sys.path.copy()
            try:
                with patch.object(module,'WORK',root/'working'), patch.object(module,'INPUT',root/'input'), \
                        patch.object(module,'STAGE','label'), patch.object(module,'DENSE_DEVICE','cpu'), \
                        patch.dict(sys.modules,{'torch':fake_torch}), \
                        patch.object(module.importlib.util,'find_spec',return_value=object()), \
                        patch.object(module,'prepare_offline_models') as prepare_models, \
                        patch('fashion_reco.workflow.run_stage',return_value={'fixture':'ok'}) as run, \
                        patch.dict(os.environ):
                    module.main()
                    prepare_models.assert_called_once()
                    run.assert_called_once()
                    import yaml
                    effective = yaml.safe_load((root/'working/output/effective-config.yaml').read_text())
                    self.assertEqual(effective['dense']['device'],'cpu')
                    self.assertEqual(effective['dense']['batch_size'],8)
            finally:
                sys.path[:] = old_path

    def test_offline_wheel_corruption_never_installed(self):
        module = self.runner()
        with tempfile.TemporaryDirectory() as temp:
            payload = {'fixture.whl': {'base64':base64.b64encode(b'bad').decode(),
                                       'sha256':hashlib.sha256(b'good').hexdigest()}}
            with patch.object(module,'WORK',Path(temp)), patch.object(module,'OFFLINE_WHEELS',payload), \
                    patch.object(module.subprocess,'run') as install:
                with self.assertRaisesRegex(ValueError,'checksum mismatch'):
                    module.install_offline_wheels()
                install.assert_not_called()

    def test_verified_model_creates_pinned_offline_cache(self):
        module = self.runner()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            candidate = root/'input/model'
            candidate.mkdir(parents=True)
            contents = {'config.json': b'{}', 'model.safetensors': b'fixture'}
            for name, content in contents.items():
                (candidate/name).write_bytes(content)
            manifest = {'e5': {'model_id':'fixture/model', 'revision':'abc', 'files': {
                name:{'size':len(content), 'sha256':hashlib.sha256(content).hexdigest()}
                for name,content in contents.items()
            }}}
            def fixture_link(target, source):
                shutil.copyfile(source, target)
            with patch.object(module,'WORK',root/'working'), patch.object(module,'INPUT',root/'input'), \
                    patch.object(module,'OFFLINE_MODELS',manifest), patch.dict(os.environ), \
                    patch.object(Path, 'symlink_to', fixture_link):
                module.prepare_offline_models()
                self.assertEqual(os.environ['HF_HUB_OFFLINE'], '1')
                cached = root/'working/hf/hub/models--fixture--model/snapshots/abc'
                self.assertEqual((cached/'model.safetensors').read_bytes(), b'fixture')
                record = json.loads((root/'working/output/offline-models.json').read_text())
                self.assertEqual(record['e5']['revision'], 'abc')

    def test_kaggle_accepts_zip_and_auto_extracted_dataset(self):
        path = Path(__file__).resolve().parents[1] / 'kaggle/run_experiment.py'
        spec = importlib.util.spec_from_file_location('kaggle_runner_test', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for zipped in (True, False):
            with self.subTest(zipped=zipped), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                dataset = root / 'input/workspace'
                dataset.mkdir(parents=True)
                (dataset/'catalog.json').write_text('[]')
                if zipped:
                    with zipfile.ZipFile(dataset/'source.zip','w') as archive:
                        archive.writestr('pyproject.toml','[project]\nname="fixture"\n')
                        archive.writestr('src/fashion_reco/__init__.py','')
                else:
                    (dataset/'source/src/fashion_reco').mkdir(parents=True)
                    (dataset/'source/pyproject.toml').write_text('[project]\nname="fixture"\n')
                old_path = sys.path.copy()
                try:
                    with patch.object(module,'WORK',root/'working'), patch.object(module,'INPUT',root/'input'), \
                            patch.object(module.subprocess,'run') as install, \
                            patch('fashion_reco.eda_only.run_eda',return_value={'fixture':'ok'}) as stage, \
                            patch.dict(os.environ):
                        module.main()
                        stage.assert_called_once()
                        self.assertEqual(os.environ['FASHION_CATALOG'],str(dataset/'catalog.json'))
                        self.assertTrue((root/'working/source/pyproject.toml').exists())
                        install.assert_not_called()
                finally:
                    sys.path[:] = old_path

    def test_workspace_bundles_offline_runtime_and_assets(self):
        path = Path(__file__).resolve().parents[1]/'kaggle/prepare_workspace.py'
        spec = importlib.util.spec_from_file_location('workspace_offline_test', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'catalog.json').write_text('[]')
            (root/'fixture.whl').write_bytes(b'fixture')
            manifest = {'e5':{'model_id':'fixture/model','revision':'abc','files': {
                'model.safetensors':{'size':7,'sha256':'fixture'},
                'pytorch_model.bin':{'size':7,'sha256':'fixture'},
            }}}
            (root/'models.json').write_text(json.dumps(manifest))
            module.prepare(root/'catalog.json', root/'upload', model_manifest=root/'models.json',
                           wheels=[root/'fixture.whl'])
            with zipfile.ZipFile(root/'upload/source.zip') as archive:
                self.assertIn('kaggle/run_experiment.py', archive.namelist())
                self.assertFalse(any('__pycache__' in n for n in archive.namelist()))
            output_manifest = json.loads((root/'upload/offline-model-manifest.json').read_text())
            self.assertNotIn('pytorch_model.bin',output_manifest['e5']['files'])
            self.assertEqual((root/'upload/offline-wheels/fixture.whl').read_bytes(),b'fixture')
