"""Synthetic, stdlib-only checks. Never execute a cloud model locally."""
import contextlib
import csv
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'colab/prepare_resume.py'
spec = importlib.util.spec_from_file_location('prepare_resume', MODULE)
prepare_resume = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare_resume)


class ResumePreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('bundle.zip', 'results.zip'):
            (self.root/name).write_bytes(b'synthetic packaging fixture')
        with contextlib.redirect_stdout(io.StringIO()):
            prepare_resume.build(self.root/'bundle.zip', self.root/'results.zip', self.root/'continue.ipynb')
        nb = json.loads((self.root/'continue.ipynb').read_text(encoding='utf-8'))
        codes = [''.join(c['source']) for c in nb['cells'] if c['cell_type']=='code']
        self.preflight = codes[2]
        self.assertLess(''.join(codes).index('Nhãn chưa đủ'), ''.join(codes).index('import torch'))
        self.labels, self.original, self.source, self.output = [self.root/name for name in ('labels','original','source','output')]
        for folder in (self.labels, self.original/'labeling',self.source/'data',self.output/'labeling'):
            folder.mkdir(parents=True)
        (self.original/'labeling/pool-manifest.json').write_text(json.dumps({'candidate_keys':[['q1','shoes','p1'],['t1','shoes','p2']]}))
        (self.source/'data/splits.json').write_text(json.dumps({'train':['q1'],'validation':[],'test':['t1']}))
        self.scope = {'LABELS':self.labels,'original':self.original,'source':self.source,
                      'output':self.output,'json':json,'csv':csv,'shutil':shutil}

    def write(self, rows):
        with (self.labels/'judgments.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer = csv.DictWriter(stream,fieldnames=['query_id','slot','product_id','grade','annotator'])
            writer.writeheader()
            writer.writerows(rows)

    def run_cell(self):
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(self.preflight,'label-preflight','exec'),self.scope)

    def row(self,grade='0'):
        return {'query_id':'q1','slot':'shoes','product_id':'p1','grade':grade,'annotator':'person'}

    def test_zero_is_a_valid_human_label_and_test_is_not_consumed(self):
        self.write([self.row(),{'query_id':'t1','slot':'shoes','product_id':'p2','grade':'','annotator':''}])
        self.run_cell()
        self.assertEqual(self.scope['seen'],{('q1','shoes','p1')})
        self.assertTrue((self.output/'labeling/judgments.csv').exists())

    def test_missing_grade_stops_before_copy(self):
        self.write([self.row('')])
        with self.assertRaisesRegex(RuntimeError,'Nhãn chưa đủ'):
            self.run_cell()
        self.assertFalse((self.output/'labeling/judgments.csv').exists())

    def test_duplicate_or_modified_id_rejected(self):
        self.write([self.row(),self.row()])
        with self.assertRaisesRegex(RuntimeError,'ID bị sửa'):
            self.run_cell()

    def test_removed_row_rejected(self):
        self.write([])
        with self.assertRaisesRegex(RuntimeError,'thiếu 1 dòng'):
            self.run_cell()

    def test_existing_notebook_never_overwritten(self):
        with self.assertRaises(FileExistsError):
            prepare_resume.build(self.root/'bundle.zip',self.root/'results.zip',self.root/'continue.ipynb')


if __name__ == '__main__':
    unittest.main()
