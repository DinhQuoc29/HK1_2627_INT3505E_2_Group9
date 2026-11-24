"""Tiny deterministic fixtures only; no ML workload runs on the local machine."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
teacher=module('teacher',ROOT/'tools/make_pseudo_labels.py')
resume=module('resume',ROOT/'colab/prepare_resume.py')


class WeakLabelTests(unittest.TestCase):
    def setUp(self):
        self.q={'slots':['women_shoes'],'budget':500000,'text':'Đi ăn cưới, cần giày thanh lịch'}
        self.p={'id':'p','slot':'women_shoes','price':200000,'name':'Giày cao gót công sở','description':'Thanh lịch'}

    def test_explicit_budget_and_owned_id_constraints(self):
        self.assertEqual(teacher.grade(self.q,{**self.p,'price':600000})[0],0)
        self.assertEqual(teacher.grade({**self.q,'owned_product_ids':['p']},self.p)[0],0)

    def test_component_not_the_requested_shoe(self):
        self.assertEqual(teacher.grade(self.q,{**self.p,'name':'Dây giày thay thế'})[0],0)

    def test_split_or_model_scores_do_not_influence_teacher(self):
        first=teacher.grade(self.q,self.p)
        second=teacher.grade({**self.q,'split':'test','model_score':1000},self.p)
        self.assertEqual(first,second)
        self.assertEqual(first[0],3)

    def test_smoke_notebook_is_isolated_and_executes_test(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            for filename in ('bundle.zip','results.zip','pseudo-labels-rule-v1.zip'):
                (folder/filename).write_bytes(b'fixture')
            with contextlib.redirect_stdout(io.StringIO()):
                resume.build(folder/'bundle.zip',folder/'results.zip',folder/'smoke.ipynb',folder/'pseudo-labels-rule-v1.zip')
            notebook=json.loads((folder/'smoke.ipynb').read_text(encoding='utf-8'))
            source='\n'.join(''.join(c['source']) for c in notebook['cells'])
            self.assertIn('PSEUDO_RULE_V1',source)
            self.assertIn('pseudo_label_smoke_test_only',source)
            self.assertIn("run_stage(config_path,'test'",source)
            self.assertIn('Không phải nhãn người chấm',source)


if __name__=='__main__':
    unittest.main()
