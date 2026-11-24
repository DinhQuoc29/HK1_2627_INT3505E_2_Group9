import math
import numpy as np


def ranking_metrics(ranked_ids, judgments, k=5):
    if len(set(ranked_ids)) != len(ranked_ids):
        raise ValueError("Duplicate product in evaluated ranking")
    if any(pid not in judgments for pid in ranked_ids):
        raise ValueError("Unjudged product must not be silently treated as irrelevant")
    if any(not isinstance(g, int) or not 0 <= g <= 3 for g in judgments.values()):
        raise ValueError("Grades must be integers 0–3")
    grades = [judgments[pid] for pid in ranked_ids[:k]]
    dcg = lambda values: sum((2 ** g - 1) / math.log2(i + 2) for i, g in enumerate(values))
    ideal = dcg(sorted(judgments.values(), reverse=True)[:k])
    relevant = sum(g >= 2 for g in judgments.values())
    return {
        "precision_at_5": sum(g >= 2 for g in grades) / k,
        "ndcg_at_5": dcg(grades) / ideal if ideal else None,
        "pooled_recall_at_5": sum(g >= 2 for g in grades) / relevant if relevant else None,
    }


def mean_defined(values):
    values = [value for value in values if value is not None]
    return float(np.mean(values)) if values else None


def summarize(records):
    keys = ("precision_at_5", "ndcg_at_5", "pooled_recall_at_5")
    return {**{key: mean_defined([r[key] for r in records]) for key in keys},
            "group_count": len(records), "groups_with_relevant_labels": sum(r["ndcg_at_5"] is not None for r in records)}


def latency_summary(samples):
    return {"count": len(samples), "mean_ms": float(np.mean(samples)),
            "p50_ms": float(np.percentile(samples, 50)), "p95_ms": float(np.percentile(samples, 95))} if samples else {}
