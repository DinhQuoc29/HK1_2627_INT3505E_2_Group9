import csv
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import yaml
import importlib.util

from fashion_reco.data import load_requests
from fashion_reco.labeling import adjudicate_test
from fashion_reco.workflow import run_stage
from fashion_reco.training import grouped_matrix
from fashion_reco.models.lexical import LexicalRetriever
from helpers import raw_product, product


class WorkflowTests(unittest.TestCase):
    def test_cpu_baseline_preview_without_relevance_labels(self):
        from fashion_reco.schemas import ShoppingRequest
        path = Path(__file__).resolve().parents[1]/'kaggle/cpu_baseline_tail.py'
        spec = importlib.util.spec_from_file_location('cpu_baseline_fixture',path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = ShoppingRequest('q','f','tui du tiec',('women_bags',),200)
            config = {'methods':['e5'],'output_dir':str(root),'seed':42}
            values = (config,[product(1),product(2,price=150)],{'sha256':'fixture'},
                      [request],{'validation':['q']})
            with patch.object(module,'WORK',root,create=True), \
                    patch.object(module,'main',create=True), \
                    patch.object(module,'install_offline_wheels',create=True), \
                    patch('fashion_reco.workflow.configure',return_value=values):
                module.run_cpu_baselines()
            output = root/'output/cpu-baseline'
            summary = json.loads((output/'summary.json').read_text())
            previews = json.loads((output/'bundles-preview.json').read_text())
            self.assertEqual(summary['methods'],['tfidf','bm25'])
            self.assertIsNone(summary['quality_metrics'])
            self.assertEqual(len(previews),4)
            self.assertEqual(previews[0]['query'],request.text)
            self.assertTrue(all(p['total_price']<=request.budget for p in previews))

    def test_dependency_free_eda_outputs_and_budget_coverage(self):
        from fashion_reco.eda_only import run_eda, percentiles
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'catalog.json').write_text(json.dumps([raw_product(1,price=100),raw_product(2,price=200,available=False)]))
            (root/'queries.jsonl').write_text(json.dumps({'query_id':'q','family_id':'f','text':'tui','slots':['women_bags'],'budget':200}))
            report=run_eda(root/'catalog.json',root/'out',root/'queries.jsonl')
            self.assertEqual(report['valid_count'],2)
            self.assertEqual([r['count'] for r in report['coverage']],[2,1])
            self.assertEqual(percentiles([100,200])['50'],150)
            self.assertTrue((root/'out/eda-summary.html').exists())

    def test_cpu_fixture_eda_label_missing_annotations_guard(self):
        """Exercise the actual entrypoint, not only isolated implementation helpers."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'configs').mkdir()
            (root/'data').mkdir()
            raw = [raw_product(1), raw_product(2, price=90), raw_product(3, price=80, available=False)]
            (root/'catalog.json').write_text(json.dumps(raw), encoding='utf-8')
            queries = [{'query_id': name, 'family_id': name, 'text':'túi dự tiệc',
                        'slots':['women_bags'], 'budget':200} for name in ('train','val','test')]
            (root/'data/queries.jsonl').write_text(''.join(json.dumps(q)+'\n' for q in queries), encoding='utf-8')
            (root/'data/splits.json').write_text(json.dumps({'train':['train'],'validation':['val'],'test':['test']}))
            config = {'seed':42,'catalog_path':str(root/'catalog.json'),'data_dir':'data',
                      'output_dir':str(root/'output'),'methods':['tfidf','bm25'],
                      'candidate_pool_size':60,'candidate_per_slot':20,'top_k':5}
            path = root/'configs/experiment.yaml'
            path.write_text(yaml.safe_dump(config))
            with patch.dict(os.environ, {'FASHION_CATALOG': str(root/'catalog.json'), 'FASHION_OUTPUT':str(root/'output')}):
                report = run_stage(path, 'eda')
                self.assertEqual(report['valid_count'],3)
                pool = run_stage(path, 'label')
                self.assertEqual(pool['row_count'],9)
                with self.assertRaisesRegex(ValueError, 'Missing grade'):
                    run_stage(path, 'train')
            self.assertTrue((root/'output/artifacts/lexical/bm25.joblib').exists())

    def test_grouping_contiguous_query_slot_labels(self):
        from fashion_reco.schemas import ShoppingRequest
        products = [product(1), product(2), product(3,'women_shoes')]
        request = ShoppingRequest('q','f','giày và túi',('women_bags','women_shoes'),300)
        retrievers = {name:LexicalRetriever(name).fit(products) for name in ('tfidf','bm25')}
        labels = {('q','women_bags'):{'1':3,'2':0},('q','women_shoes'):{'3':2}}
        matrix,y,sizes,keys = grouped_matrix([request],products,retrievers,labels,{'q'})
        self.assertEqual(sizes,[2,1])
        self.assertEqual(y.tolist(),[3,0,2])
        self.assertEqual(sum(sizes),len(matrix))

    def test_test_adjudication_does_not_invent_disagreement_grade(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            fields=['query_id','slot','product_id','grade','annotator','notes']
            for name,grade in [('alice','3'),('bob','1')]:
                with (root/f'{name}.csv').open('w',encoding='utf-8-sig',newline='') as f:
                    writer=csv.DictWriter(f,fieldnames=fields)
                    writer.writeheader()
                    writer.writerow(dict(zip(fields,['q','women_bags','1',grade,name,''])))
            result=adjudicate_test(root/'alice.csv',root/'bob.csv',root/'resolved.csv')
            self.assertEqual(result['agreement'],0)
            with (root/'resolved.csv').open(encoding='utf-8-sig',newline='') as f:
                row=next(csv.DictReader(f))
            self.assertEqual(row['grade'],'')
            self.assertIn('rater_a=3',row['notes'])
