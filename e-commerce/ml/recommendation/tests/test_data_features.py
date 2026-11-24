import json
from pathlib import Path
import tempfile
import unittest
import numpy as np

from fashion_reco.data import load_catalog, normalize, validate_splits
from fashion_reco.schemas import ShoppingRequest
from fashion_reco.features import FEATURE_NAMES, feature_matrix
from fashion_reco.models.lexical import LexicalRetriever
from helpers import product, raw_product


class DataTests(unittest.TestCase):
    def test_invalid_rows_duplicates_and_source_availability(self):
        rows = [raw_product(1, available=False), raw_product(1), raw_product(2, price=0),
                raw_product(3, price=True), raw_product(4, slot='women_party_dresses'),
                {**raw_product(5), 'brandName': {'name': 'Brand'}}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'catalog.json'
            path.write_text(json.dumps(rows), encoding='utf-8')
            catalog, manifest = load_catalog(path)
        self.assertEqual(len(catalog), 3)
        self.assertFalse(catalog[0]['available'])
        self.assertEqual(catalog[1]['slot'], 'women_dresses')
        self.assertEqual(catalog[2]['brand'], 'Brand')
        self.assertEqual(manifest['issues']['duplicate_id'], 1)
        self.assertEqual(manifest['issues']['invalid_id_name_price_currency'], 2)

    def test_family_leakage_rejected(self):
        a = ShoppingRequest('a', 'same-family', 'túi', ('women_bags',), 100)
        b = ShoppingRequest('b', 'same-family', 'túi khác', ('women_bags',), 200)
        with self.assertRaisesRegex(ValueError, 'family leakage'):
            validate_splits([a, b], {'train': ['a'], 'validation': [], 'test': ['b']})

    def test_features_stable_and_missing_flags(self):
        catalog = [product(1), product(2, text='balo đi học')]
        retrievers = {name: LexicalRetriever(name).fit(catalog) for name in ('tfidf', 'bm25')}
        request = ShoppingRequest('q', 'f', 'túi dự tiệc', ('women_bags',), 200)
        matrix = feature_matrix(request, 'women_bags', [0, 1], catalog, retrievers)
        self.assertEqual(matrix.shape, (2, len(FEATURE_NAMES)))
        self.assertTrue(np.isfinite(matrix).all())
        self.assertEqual(matrix[0][FEATURE_NAMES.index('price_budget_ratio')], .5)
        self.assertEqual(matrix[0][FEATURE_NAMES.index('rating_missing')], 1)
        self.assertEqual(normalize('ĐẦM dự tiệc'), 'dam du tiec')

    def test_requests_require_clarified_roles_and_valid_budget(self):
        for slots, budget in [((), 100), (('unknown',), 100), (('women_bags',), 0), (('women_bags',), True)]:
            with self.assertRaises(ValueError):
                ShoppingRequest('q', 'f', 'nhu cầu', slots, budget)
