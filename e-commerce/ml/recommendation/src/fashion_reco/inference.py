from .bundle import choose_bundle
from .candidates import sorted_indices
from .eligibility import eligible
from .features import feature_matrix


def recommend(request, catalog, model_bundle, mode="research", method="bm25", per_slot=20):
    """Shared offline/backend boundary. Input request is already clarified."""
    retrievers = model_bundle["retrievers"]
    ranker = model_bundle.get("ranker")
    if method != "lambdamart" and method not in retrievers:
        raise ValueError(f"Model not loaded: {method}")
    ranked, fallback = {}, None
    for slot in request.slots:
        indices = [i for i, p in enumerate(catalog) if eligible(p, request, mode, slot)]
        if not indices:
            ranked[slot] = []
            continue
        # A fixed candidate generator for all downstream rerankers.
        if method == "lambdamart":
            from .candidates import candidate_pool
            pool = candidate_pool(request, catalog, retrievers, mode, max_total=60)
            indices = [i for i in pool if catalog[i]["slot"] == slot]
            try:
                if ranker is None:
                    raise RuntimeError("Trained ranker unavailable")
                scores = ranker.predict(feature_matrix(request, slot, indices, catalog, retrievers))
            except Exception as exc:
                fallback = f"ranker_error:{type(exc).__name__}"
                scores = retrievers["bm25"].score(request.slot_query(slot), indices)
        else:
            scores = retrievers[method].score(request.slot_query(slot), indices)
        ranking = sorted_indices(indices, scores, catalog)[:per_slot]
        ranked[slot] = [{**catalog[index], "score": float(score),
                         "evidence": {"source": "catalog", "text": catalog[index]["description"]}}
                        for index, score in ranking]
    result = choose_bundle(request, ranked, mode, per_slot)
    result.update(method=method, fallback_reason=fallback)
    return result
