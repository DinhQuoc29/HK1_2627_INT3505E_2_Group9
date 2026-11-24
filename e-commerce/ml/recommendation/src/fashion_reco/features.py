"""Query-product features shared by training and inference; no fabricated events."""
import math
import numpy as np
from .data import normalize

FEATURE_NAMES = [
    "tfidf_score", "bm25_score", "e5_score", "bge_score", "name_token_overlap",
    "name_exact_match", "description_token_overlap", "brand_match", "has_brand",
    "log_price", "price_budget_ratio", "slot_match", "rating", "log_review_count",
    "rating_missing", "review_count_missing", "description_missing",
]
FEATURE_VERSION = "1"


def numeric(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0:
        return float(value), 0.0
    return 0.0, 1.0


def feature_matrix(request, slot, indices, products, retrievers):
    query = request.slot_query(slot)
    scores = {name: retriever.score(query, indices) for name, retriever in retrievers.items()}
    tokens = set(normalize(request.text).split())
    denominator = max(1, len(tokens))
    result = []
    for position, index in enumerate(indices):
        p = products[index]
        name, description, brand = normalize(p["name"]), normalize(p["description"]), normalize(p["brand"])
        rating, missing_rating = numeric(p.get("rating"))
        reviews, missing_reviews = numeric(p.get("review_count"))
        result.append([
            *[float(scores[m][position]) if m in scores else 0.0 for m in ("tfidf", "bm25", "e5", "bge")],
            len(tokens.intersection(name.split())) / denominator,
            float(name == normalize(request.text)),
            len(tokens.intersection(description.split())) / denominator,
            float(bool(brand) and brand in normalize(request.text)), float(bool(brand)),
            math.log1p(p["price"]), p["price"] / request.budget, float(p["slot"] == slot),
            min(rating, 5.0), math.log1p(reviews), missing_rating, missing_reviews,
            float(not description),
        ])
    return np.asarray(result, dtype=np.float32).reshape((-1, len(FEATURE_NAMES)))
