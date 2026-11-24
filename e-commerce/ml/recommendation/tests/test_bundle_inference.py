import unittest
from fashion_reco.schemas import ShoppingRequest
from fashion_reco.bundle import choose_bundle
from fashion_reco.eligibility import eligible
from fashion_reco.inference import recommend
from fashion_reco.models.lexical import LexicalRetriever
from helpers import product


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.request = ShoppingRequest('q', 'f', 'giày và túi dự tiệc', ('women_shoes', 'women_bags'), 200)

    def test_total_budget_requires_second_choice_and_boundary_inclusive(self):
        ranked = {'women_shoes': [product(1, 'women_shoes', 150), product(2, 'women_shoes', 100)],
                  'women_bags': [product(3, price=100)]}
        result = choose_bundle(self.request, ranked)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(result['total_price'], 200)
        self.assertEqual([p['id'] for p in result['items']], ['2', '3'])

    def test_over_budget_and_missing_slot_not_complete(self):
        ranked = {'women_shoes': [product(1, 'women_shoes', 101)], 'women_bags': [product(2, price=100)]}
        result = choose_bundle(self.request, ranked)
        self.assertEqual(result['status'], 'no_feasible_bundle')
        self.assertEqual(result['items'], [])
        result = choose_bundle(self.request, {'women_bags': ranked['women_bags']})
        self.assertEqual(result['missing_slots'], ['women_shoes'])

    def test_eligibility_stock_exclusions_and_price(self):
        self.assertTrue(eligible(product(1, price=200), self.request))
        self.assertFalse(eligible(product(1, price=201), self.request))
        self.assertTrue(eligible(product(1, available=False), self.request, 'research'))
        self.assertFalse(eligible(product(1, available=False), self.request, 'available_only'))
        request = ShoppingRequest('q', 'f', 'túi', ('women_bags',), 200, owned_product_ids=('1',))
        self.assertFalse(eligible(product(1), request))

    def test_duplicate_id_and_wrong_slot_not_returned(self):
        ranked = {'women_shoes': [product(1, 'women_shoes', 100), product(1, 'women_shoes', 100)],
                  'women_bags': [product(2, 'men_bags', 100), product(3, price=100)]}
        result = choose_bundle(self.request, ranked)
        self.assertEqual([p['id'] for p in result['items']], ['1', '3'])

    def test_ranker_failure_uses_filtered_baseline(self):
        class BrokenRanker:
            def predict(self, matrix):
                raise RuntimeError('fixture failure')
        catalog = [product(1, 'women_shoes', 100, text='giày dự tiệc'), product(2, price=100),
                   product(3, price=1, available=False)]
        retrievers = {name: LexicalRetriever(name).fit(catalog) for name in ('tfidf', 'bm25')}
        result = recommend(self.request, catalog, {'retrievers': retrievers, 'ranker': BrokenRanker()},
                           mode='available_only', method='lambdamart')
        self.assertEqual(result['status'], 'complete')
        self.assertIn('ranker_error', result['fallback_reason'])
        self.assertNotIn('3', [p['id'] for p in result['items']])
