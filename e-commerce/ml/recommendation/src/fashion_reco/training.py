from itertools import product
import numpy as np
from .features import feature_matrix, FEATURE_NAMES
from .evaluation import ranking_metrics, summarize
from .models.ranker import SupervisedRanker


def grouped_matrix(requests, products, retrievers, judgments, query_ids):
    by_id = {p['id']: i for i, p in enumerate(products)}
    lookup = {q.query_id: q for q in requests}
    matrices, labels, sizes, keys = [], [], [], []
    for (qid, slot), grades in sorted(judgments.items()):
        if qid not in query_ids:
            continue
        ids = sorted(grades)
        matrices.append(feature_matrix(lookup[qid], slot, [by_id[pid] for pid in ids], products, retrievers))
        labels.extend(grades[pid] for pid in ids)
        sizes.append(len(ids))
        keys.append((qid, slot, ids))
    if not matrices:
        raise ValueError('No labeled ranking groups for this split')
    return np.vstack(matrices), np.asarray(labels), sizes, keys


def evaluate_ranker(model, matrix, keys, judgments):
    scores, offset, records = model.predict(matrix), 0, []
    for qid, slot, ids in keys:
        group_scores = scores[offset:offset + len(ids)]
        order = sorted(zip(ids, group_scores), key=lambda pair: (-float(pair[1]), pair[0]))
        records.append({'query_id': qid, 'slot': slot,
                        **ranking_metrics([pid for pid, _ in order], judgments[(qid, slot)])})
        offset += len(ids)
    return summarize(records), records


def train_ranker(requests, products, retrievers, judgments, splits, config, seed=42):
    import lightgbm as lgb
    train_x, train_y, groups, _ = grouped_matrix(requests, products, retrievers, judgments, set(splits['train']))
    val_x, val_y, val_groups, val_keys = grouped_matrix(requests, products, retrievers, judgments, set(splits['validation']))
    offset, useful = 0, 0
    for size in groups:
        useful += len(set(train_y[offset:offset+size])) > 1
        offset += size
    if useful < 2:
        raise ValueError('Need at least two train groups with differing relevance labels')
    if not np.any(val_y > 0):
        raise ValueError('Validation set has no positive relevance labels')
    trials, best, best_score = [], None, -1.0
    for leaves, minimum, rate in product(config['num_leaves'], config['min_child_samples'], config['learning_rate']):
        params = {'num_leaves': leaves, 'min_child_samples': minimum, 'learning_rate': rate}
        model = lgb.LGBMRanker(objective='lambdarank', metric='ndcg',
                              n_estimators=config['n_estimators'], random_state=seed,
                              deterministic=True, force_col_wise=True, n_jobs=2, verbosity=-1, **params)
        model.fit(train_x, train_y, group=groups, feature_name=FEATURE_NAMES,
                  eval_set=[(val_x, val_y)], eval_group=[val_groups], eval_at=[5],
                  callbacks=[lgb.early_stopping(config['early_stopping_rounds'], verbose=False)])
        summary, _ = evaluate_ranker(model, val_x, val_keys, judgments)
        score = summary['ndcg_at_5']
        trials.append({**params, 'best_iteration': model.best_iteration_, 'validation': summary})
        if score is not None and score > best_score:
            best, best_score = SupervisedRanker(model), score
    if best is None:
        raise ValueError('No valid validation result')
    return best, trials
