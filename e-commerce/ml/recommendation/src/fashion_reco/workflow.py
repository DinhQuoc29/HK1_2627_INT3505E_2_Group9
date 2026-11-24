"""Reproducible stages shared by notebooks and the Kaggle batch entrypoint."""
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import random
from time import perf_counter
import numpy as np
import yaml

from .data import load_catalog, load_requests, dump_json, validate_splits
from .features import FEATURE_NAMES, FEATURE_VERSION
from .labeling import export_labeling, load_judgments
from .models.lexical import LexicalRetriever
from .evaluation import ranking_metrics, summarize, latency_summary
from .candidates import sorted_indices
from .eligibility import eligible
from .inference import recommend


def configure(config_path):
    config_path = Path(config_path).resolve()
    config = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    if config.get('top_k', 5) != 5:
        raise ValueError('This experiment reports @5; keep top_k=5')
    if not 1 <= config.get('candidate_per_slot', 20) <= 20:
        raise ValueError('candidate_per_slot must be 1–20')
    root = config_path.parent.parent
    config['data_dir'] = str((root / config['data_dir']).resolve()) if not Path(config['data_dir']).is_absolute() else config['data_dir']
    config['catalog_path'] = os.getenv('FASHION_CATALOG', config['catalog_path'])
    config['output_dir'] = os.getenv('FASHION_OUTPUT', config['output_dir'])
    Path(config['output_dir']).mkdir(parents=True, exist_ok=True)
    random.seed(config['seed'])
    np.random.seed(config['seed'])
    products, manifest = load_catalog(config['catalog_path'])
    requests = load_requests(Path(config['data_dir']) / 'queries.jsonl')
    splits = json.loads((Path(config['data_dir']) / 'splits.json').read_text(encoding='utf-8'))
    validate_splits(requests, splits)
    return config, products, manifest, requests, splits


def environment():
    versions = {}
    for package in ('numpy', 'scikit-learn', 'rank-bm25', 'sentence-transformers', 'lightgbm', 'torch'):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            pass
    return {'python': platform.python_version(), 'platform': platform.platform(), 'packages': versions}


def build_retrievers(config, products):
    output = Path(config['output_dir'])
    retrievers, timings = {}, {}
    for method in config['methods']:
        started = perf_counter()
        if method in ('tfidf', 'bm25'):
            retriever = LexicalRetriever(method).fit(products)
            retriever.save(output / 'artifacts' / 'lexical' / f'{method}.joblib')
        else:
            import torch
            from .models.dense import DenseRetriever
            torch.manual_seed(config['seed'])
            dense = config['dense']
            if dense['device'] == 'cuda' and not torch.cuda.is_available():
                raise RuntimeError('GPU required for dense stage. Enable GPU on Kaggle; no silent CPU fallback.')
            retriever = DenseRetriever(method, dense['models'][method], device=dense['device'],
                                       batch_size=dense['batch_size'], max_length=dense['max_length'],
                                       revision=dense.get('revisions', {}).get(method))
            retriever.fit(products, output / 'artifacts' / 'dense' / method)
        retrievers[method] = retriever
        timings[method] = {'build_seconds': perf_counter() - started,
                           'identity': getattr(retriever, 'identity', None)}
    dump_json(output / 'build-timings.json', timings)
    return retrievers


def eda(config, products, manifest, requests):
    output = Path(config['output_dir'])
    dump_json(output / 'catalog-manifest.json', manifest)
    dump_json(output / 'catalog.cleaned.json', products)
    prices = [p['price'] for p in products]
    report = {**manifest, 'price_percentiles': {str(k): float(np.percentile(prices, k)) for k in (0, 25, 50, 75, 95, 100)},
              'description_lengths': {str(k): float(np.percentile([len(p['description']) for p in products], k)) for k in (0, 50, 95, 100)},
              'coverage': []}
    for request in requests:
        for mode in ('research', 'available_only'):
            for slot in request.slots:
                report['coverage'].append({'query_id': request.query_id, 'mode': mode, 'slot': slot,
                                          'count': sum(eligible(p, request, mode, slot) for p in products)})
    dump_json(output / 'eda.json', report)
    try:
        import pandas as pd
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        frame = pd.DataFrame(products)
        frame.groupby('slot').agg(products=('id','size'), available=('available','sum')).to_csv(output/'eda-groups.csv')
        pd.DataFrame(report['coverage']).to_csv(output/'eda-query-coverage.csv',index=False)
        fig, axes = plt.subplots(1, 3, figsize=(18, 7))
        frame['slot'].value_counts().plot.barh(ax=axes[0],title='Products by role')
        np.log10(frame['price']).plot.hist(bins=40,ax=axes[1],title='Price distribution (log10 VND)')
        frame['description'].str.len().plot.hist(bins=40,ax=axes[2],title='Description length')
        fig.tight_layout()
        fig.savefig(output/'eda-overview.png',dpi=150)
        plt.close(fig)
    except ImportError:
        # Minimal fixture tests do not require plotting libraries.
        pass
    return report


def evaluate_methods(requests, products, retrievers, judgments, query_ids, ranker=None):
    lookup = {q.query_id: q for q in requests}
    by_id = {p['id']: i for i, p in enumerate(products)}
    records = {name: [] for name in retrievers}
    if ranker is not None:
        records['lambdamart'] = []
    from .features import feature_matrix
    for (qid, slot), grades in sorted(judgments.items()):
        if qid not in query_ids:
            continue
        request = lookup[qid]
        indices = [by_id[pid] for pid in sorted(grades)]
        for method in records:
            scores = ranker.predict(feature_matrix(request, slot, indices, products, retrievers)) if method == 'lambdamart' else retrievers[method].score(request.slot_query(slot), indices)
            ranked = sorted_indices(indices, scores, products)
            records[method].append({'query_id': qid, 'slot': slot,
                                    **ranking_metrics([products[i]['id'] for i, _ in ranked], grades)})
    return {name: summarize(rows) for name, rows in records.items()}, records


def benchmark(requests, products, retrievers, ranker=None):
    """Warm catalog, uncached query embeddings; same requests and alternating order."""
    methods = list(retrievers) + (['lambdamart'] if ranker else [])
    samples = {m: [] for m in methods}
    model_bundle = {'retrievers': retrievers, 'ranker': ranker}
    if not requests:
        return {}
    for method in methods:
        recommend(requests[0], products, model_bundle, method=method)
    for turn, request in enumerate(requests):
        for method in (methods if turn % 2 == 0 else list(reversed(methods))):
            for retriever in retrievers.values():
                if hasattr(retriever, 'clear_query_cache'):
                    retriever.clear_query_cache()
            started = perf_counter()
            recommend(request, products, model_bundle, method=method)
            if 'torch' in __import__('sys').modules:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
            samples[method].append((perf_counter() - started) * 1000)
    return {name: latency_summary(values) for name, values in samples.items()}


def resource_snapshot():
    # Linux ru_maxrss is KiB and includes the whole process, not one model.
    result = {}
    try:
        import resource
        result['process_peak_rss_mib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except ImportError:
        result['process_peak_rss_mib'] = None
    if 'torch' in __import__('sys').modules:
        import torch
        if torch.cuda.is_available():
            result.update(gpu=torch.cuda.get_device_name(0), gpu_peak_allocated_mib=torch.cuda.max_memory_allocated() / 2**20)
    result['note'] = 'Process-wide peak; isolate model runs for fair per-model memory measurements.'
    return result


def code_hash():
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.rglob('*.py')):
        digest.update(path.relative_to(Path(__file__).parent).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def export_bundles(requests, products, retrievers, ranker, methods, query_ids, config, prefix):
    output = Path(config['output_dir'])
    bundles, manual, aggregate = [], [], []
    for request in requests:
        if request.query_id not in query_ids:
            continue
        for mode in ('research', 'available_only'):
            for method in methods:
                result = recommend(request, products, {'retrievers': retrievers, 'ranker': ranker}, mode, method, config['candidate_per_slot'])
                items = result['items']
                if result['total_price'] > request.budget or len({p['id'] for p in items}) != len(items):
                    raise AssertionError('Invalid bundle price or duplicate product')
                if items and (len(items) != len(request.slots) or {p['slot'] for p in items} != set(request.slots)):
                    raise AssertionError('Bundle role coverage mismatch')
                bundles.append(result)
                manual.append({'query_id': request.query_id, 'method': method, 'mode': mode,
                               'status': result['status'], 'need_satisfaction_0_3': '', 'compatibility_0_3': '', 'annotator': '', 'notes': ''})
    dump_json(output / f'{prefix}-bundles.json', bundles)
    review_path = output / f'{prefix}-bundle-human-review.csv'
    if manual and not review_path.exists():
        with review_path.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(manual[0]))
            writer.writeheader()
            writer.writerows(manual)
    for method in methods:
        for mode in ('research', 'available_only'):
            rows = [r for r in bundles if r['method'] == method and r['mode'] == mode]
            aggregate.append({'method': method, 'mode': mode, 'query_count': len(rows),
                              'complete_rate': sum(r['status']=='complete' for r in rows)/len(rows) if rows else None,
                              'budget_violations': sum(r['total_price']>r['budget'] for r in rows),
                              'duplicate_violations': sum(len({p['id'] for p in r['items']})!=len(r['items']) for r in rows),
                              'fallback_count': sum(r['fallback_reason'] is not None for r in rows)})
    dump_json(output / f'{prefix}-bundle-summary.json', aggregate)
    return aggregate


def retrieval_coverage(requests, products, retrievers, judgments, query_ids):
    records = []
    lookup = {q.query_id: q for q in requests}
    for (qid, slot), grades in sorted(judgments.items()):
        if qid not in query_ids:
            continue
        request = lookup[qid]
        relevant = {pid for pid, grade in grades.items() if grade >= 2}
        indices = [i for i, p in enumerate(products) if eligible(p, request, 'research', slot)]
        for method, retriever in retrievers.items():
            ranking = sorted_indices(indices, retriever.score(request.slot_query(slot), indices), products)[:20]
            ids = {products[i]['id'] for i, _ in ranking}
            records.append({'query_id': qid, 'slot': slot, 'method': method,
                            'known_positive_retrieval_at_20': len(ids & relevant)/len(relevant) if relevant else None,
                            'judged_fraction_at_20': len(ids & grades.keys())/len(ids) if ids else None,
                            'warning': 'Pooled judgments only; unjudged retrieved items are not treated as negatives.'})
    return records


def run_stage(config_path, stage, labeling_dir=None):
    if stage not in ('eda', 'label', 'train', 'test'):
        raise ValueError('Unknown stage')
    config, products, manifest, requests, splits = configure(config_path)
    output = Path(config['output_dir'])
    dump_json(output / 'environment.json', environment())
    if stage == 'eda':
        return eda(config, products, manifest, requests)
    retrievers = build_retrievers(config, products)
    labels = Path(labeling_dir or output / 'labeling')
    if stage == 'label':
        return export_labeling(requests, products, retrievers, splits, manifest, labels, config['candidate_pool_size'])
    pool = json.loads((labels / 'pool-manifest.json').read_text(encoding='utf-8'))
    validation_ids = set(splits['train']) | set(splits['validation'])
    required = set(splits['test']) if stage == 'test' else validation_ids
    grade_file = labels / ('test-adjudicated.csv' if stage == 'test' else 'judgments.csv')
    judgments = load_judgments(grade_file, requests, products, pool, manifest, required)
    from .models.ranker import SupervisedRanker
    ranker_path = output / 'artifacts/ranker/model.joblib'
    if stage == 'train':
        if set(retrievers) != {'tfidf', 'bm25', 'e5', 'bge'}:
            raise ValueError('Official LambdaMART features require all four configured retrievers')
        from .training import train_ranker
        ranker, trials = train_ranker(requests, products, retrievers, judgments, splits, config['ranker'], config['seed'])
        ranker.save(ranker_path)
        dump_json(output / 'artifacts/feature-schema.json', {'names': FEATURE_NAMES, 'version': FEATURE_VERSION})
        dump_json(output / 'feature-importance.json', {
            'kind': 'LightGBM split counts, not causal effects',
            'features': dict(zip(FEATURE_NAMES, map(int, ranker.model.feature_importances_)))})
        dump_json(output / 'training-trials.json', trials)
        summary, details = evaluate_methods(requests, products, retrievers, judgments, set(splits['validation']), ranker)
        times = benchmark([q for q in requests if q.query_id in splits['validation']], products, retrievers, ranker)
        valid = {name: s['ndcg_at_5'] for name, s in summary.items() if s['ndcg_at_5'] is not None}
        if not valid:
            raise ValueError('No evaluable validation queries')
        maximum = max(valid.values())
        eligible_methods = [m for m, score in valid.items() if maximum - score < 0.01]
        selected = min(eligible_methods, key=lambda m: (times[m]['p50_ms'], m))
        finalists = sorted(valid, key=lambda m: (-valid[m], m))[:2]
        export_bundles(requests, products, retrievers, ranker, finalists, set(splits['validation']), config, 'validation')
        lock = {'selected_method': selected, 'catalog_sha256': manifest['sha256'], 'pool_sha256': hashlib.sha256((labels/'pool-manifest.json').read_bytes()).hexdigest(),
                'config': config, 'feature_version': FEATURE_VERSION,
                'code_sha256': code_hash(), 'splits': splits,
                'retriever_identities': {name: getattr(model, 'identity', None) for name, model in retrievers.items()},
                'ranker_sha256': hashlib.sha256(ranker_path.read_bytes()).hexdigest(),
                'training_judgments_sha256': hashlib.sha256(grade_file.read_bytes()).hexdigest(),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'validation': summary, 'latency': times,
                'finalists': finalists,
                'note': 'Pilot selection from validation ranking/latency. Review validation bundles before deployment; no aesthetic-compatibility guarantee.'}
        dump_json(output / 'selection-lock.json', lock)
        dump_json(output / 'validation-details.json', details)
        dump_json(output / 'resources.json', resource_snapshot())
        return lock
    if stage != 'test':
        raise ValueError('Unknown stage')
    lock = json.loads((output / 'selection-lock.json').read_text(encoding='utf-8'))
    if lock['catalog_sha256'] != manifest['sha256'] or lock['config'] != config or lock['pool_sha256'] != hashlib.sha256((labels/'pool-manifest.json').read_bytes()).hexdigest() or lock['ranker_sha256'] != hashlib.sha256(ranker_path.read_bytes()).hexdigest() or lock['code_sha256'] != code_hash() or lock['splits'] != splits or lock['retriever_identities'] != {name: getattr(model, 'identity', None) for name, model in retrievers.items()}:
        raise ValueError('Frozen dataset, pool, config or ranker changed after model selection')
    ranker = SupervisedRanker.load(ranker_path)
    summary, details = evaluate_methods(requests, products, retrievers, judgments, set(splits['test']), ranker)
    dump_json(output / 'test-ranking-summary.json', summary)
    dump_json(output / 'test-ranking-details.json', details)
    dump_json(output / 'test-retrieval-coverage.json', retrieval_coverage(requests, products, retrievers, judgments, set(splits['test'])))
    methods = list(retrievers) + ['lambdamart']
    aggregate = export_bundles(requests, products, retrievers, ranker, methods, set(splits['test']), config, 'test')
    dump_json(output / 'resources.json', resource_snapshot())
    return {'selected_method': lock['selected_method'], 'test_ranking': summary, 'bundles': aggregate}
