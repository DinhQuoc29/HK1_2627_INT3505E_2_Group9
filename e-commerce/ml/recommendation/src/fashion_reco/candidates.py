from .eligibility import eligible


def sorted_indices(indices, scores, products):
    return sorted(zip(indices, scores), key=lambda pair: (-float(pair[1]), products[pair[0]]["id"]))


def candidate_pool(request, products, retrievers, mode="research", max_total=60):
    """Balanced fixed pool: RRF union per slot, then deterministic round robin."""
    quota = max_total // len(request.slots)
    remaining = max_total % len(request.slots)
    selected = []
    for slot_number, slot in enumerate(request.slots):
        indices = [i for i, product in enumerate(products) if eligible(product, request, mode, slot)]
        fusion = {}
        for retriever in retrievers.values():
            ranking = sorted_indices(indices, retriever.score(request.slot_query(slot), indices), products)
            for rank, (index, _) in enumerate(ranking[:quota + 1], 1):
                fusion[index] = fusion.get(index, 0.0) + 1.0 / (60 + rank)
        ordered = sorted(fusion, key=lambda i: (-fusion[i], products[i]["id"]))
        selected.extend(ordered[:quota + int(slot_number < remaining)])
    return selected
