import csv
import json
from pathlib import Path
import tempfile
import unittest
from fashion_reco.schemas import ShoppingRequest
from fashion_reco.candidates import candidate_pool
from fashion_reco.labeling import export_labeling, load_judgments, adjudicate_test
from fashion_reco.evaluation import ranking_metrics
from fashion_reco.models.lexical import LexicalRetriever
from fashion_reco.data import load_requests, validate_splits
from helpers import product


class RankingTests(unittest.TestCase):
    def test_ndcg_perfect_reverse_no_positive_and_unjudged(self):
        labels = {'a': 3, 'b': 2, 'c': 0}
        self.assertAlmostEqual(ranking_metrics(['a', 'b', 'c'], labels)['ndcg_at_5'], 1)
        self.assertLess(ranking_metrics(['c', 'b', 'a'], labels)['ndcg_at_5'], 1)
        self.assertEqual(ranking_metrics(['a', 'b'], labels)['precision_at_5'], .4)
        self.assertIsNone(ranking_metrics(['a'], {'a': 0})['ndcg_at_5'])
        with self.assertRaises(ValueError):
            ranking_metrics(['unjudged'], labels)
        with self.assertRaises(ValueError):
            ranking_metrics(['a', 'a'], labels)

    def test_pool_roundtrip_annotations_and_no_test_label_consumption(self):
        catalog = [product(1), product(2, text='balo đi học'), product(3, 'women_shoes', text='giày dự tiệc')]
        requests = [ShoppingRequest('train', 'f1', 'túi', ('women_bags',), 200),
                    ShoppingRequest('test', 'f2', 'giày', ('women_shoes',), 200)]
        retrievers = {name: LexicalRetriever(name).fit(catalog) for name in ('tfidf', 'bm25')}
        pool = candidate_pool(requests[0], catalog, retrievers, max_total=1)
        self.assertEqual(len(pool), 1)
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            manifest = export_labeling(requests, catalog, retrievers, {'train':['train'], 'validation':[], 'test':['test']}, {'sha256':'fixed'}, directory)
            path = directory / 'judgments.csv'
            with self.assertRaisesRegex(ValueError, 'Missing grade'):
                load_judgments(path, requests, catalog, manifest, {'sha256':'fixed'}, {'train'})
            with path.open(encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                fields, rows = reader.fieldnames, list(reader)
            for row in rows:
                if row['query_id'] == 'train':
                    row.update(grade='2', annotator='human')
            with path.open('w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fields)
                writer.writeheader()
                writer.writerows(rows)
            labels = load_judgments(path, requests, catalog, manifest, {'sha256':'fixed'}, {'train'})
            self.assertEqual(set(labels), {('train', 'women_bags')})
            with self.assertRaisesRegex(ValueError, 'changed'):
                load_judgments(path, requests, catalog, manifest, {'sha256':'different'}, {'train'})
            with self.assertRaises(FileExistsError):
                export_labeling(requests, catalog, retrievers, {'train':['train'], 'test':['test']}, {'sha256':'fixed'}, directory)

    def test_official_template_split_has_no_family_leakage(self):
        data = Path(__file__).resolve().parents[1] / 'data'
        requests = load_requests(data / 'queries.jsonl')
        splits = json.loads((data / 'splits.json').read_text())
        validate_splits(requests, splits)
        self.assertEqual(len(requests), 120)
        self.assertEqual([len(splits[k]) for k in ('train','validation','test')], [72,24,24])
        self.assertTrue(requests[0].text.startswith('Tôi đi ăn cưới'))
        self.assertFalse(any('?' in request.text for request in requests))

    def test_lexical_artifact_reload_identical_scores(self):
        catalog = [product(1), product(2, text='giày thể thao đi học')]
        for method in ('tfidf', 'bm25'):
            model = LexicalRetriever(method).fit(catalog)
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'model.joblib'
                model.save(path)
                restored = LexicalRetriever.load(path)
                self.assertEqual(model.score('túi dự tiệc', [0,1]).tolist(), restored.score('túi dự tiệc', [0,1]).tolist())
