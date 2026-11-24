import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


class ResumeTests(unittest.TestCase):
    def test_submit_exactly_once_only_after_actual_gpu_confirmation(self):
        folder = Path(__file__).resolve().parents[1]/'kaggle'
        old_path = sys.path.copy()
        try:
            sys.path.insert(0,str(folder))
            spec = importlib.util.spec_from_file_location('resume_label_test',folder/'resume_label.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            sys.path[:] = old_path
        for available in (False,True):
            with self.subTest(gpu=available), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                def remote(*args, **kwargs):
                    if args[:2] == ('kernels','status'):
                        return 'KernelWorkerStatus.COMPLETE'
                    if args[:2] == ('kernels','output'):
                        directory = root/'gpu-probe-verified'
                        directory.mkdir()
                        (directory/'gpu-probe.json').write_text(json.dumps({
                            'cuda_available':available,'devices':int(available)}))
                        return 'downloaded'
                    if args[:2] == ('kernels','push'):
                        return 'Kernel version 3 successfully pushed.'
                    raise AssertionError(args)
                def finish(kernel,directory,pattern):
                    directory.mkdir()
                    (directory/'run-status.json').write_text('{"status":"complete"}')
                with patch.object(module,'ARTIFACTS',root), patch.object(module,'STATE',root/'state.json'), \
                        patch.object(module,'STOP',root/'stop'), patch.object(module,'call',side_effect=remote) as calls, \
                        patch.object(module,'stage_run') as stage, patch.object(module,'monitor',side_effect=finish) as monitor:
                    module.main()
                    pushes = [c for c in calls.call_args_list if c.args[:2]==('kernels','push')]
                    self.assertEqual(len(pushes),int(available))
                    self.assertEqual(stage.call_count,int(available))
                    self.assertEqual(monitor.call_count,int(available))
                    state = json.loads((root/'state.json').read_text())
                    self.assertEqual(state['phase'],'complete' if available else 'waiting_for_gpu_access')
                    if available:
                        with self.assertRaisesRegex(RuntimeError,'already recorded'):
                            module.main()
                        self.assertEqual(len([c for c in calls.call_args_list if c.args[:2]==('kernels','push')]),1)
