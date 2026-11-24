from itertools import product as cartesian_product
from .eligibility import eligible


def choose_bundle(request, ranked_by_slot, mode="research", per_slot=20):
    """Exact search over <=20^4 candidates, objective=sum reciprocal ranks.

    This enforces product roles and total price, not aesthetic compatibility.
    """
    if not isinstance(per_slot, int) or not 1 <= per_slot <= 20:
        raise ValueError("per_slot must be between 1 and 20")
    choices = {}
    for slot in request.slots:
        seen, valid = set(), []
        for product in ranked_by_slot.get(slot, []):
            if product["id"] not in seen and eligible(product, request, mode, slot):
                seen.add(product["id"])
                valid.append(product)
        choices[slot] = valid[:per_slot]
    missing = [slot for slot, rows in choices.items() if not rows]
    best, best_key = None, None
    if not missing:
        indexed = [list(enumerate(choices[slot], 1)) for slot in request.slots]
        for combination in cartesian_product(*indexed):
            items = [p for _, p in combination]
            total = sum(p["price"] for p in items)
            if total > request.budget or len({p["id"] for p in items}) != len(items):
                continue
            objective = sum(1.0 / rank for rank, _ in combination)
            key = (-objective, total, tuple(p["id"] for p in items))
            if best_key is None or key < best_key:
                best_key, best = key, items
    # No partial list is presented as a complete affordable bundle.
    return {
        "query_id": request.query_id, "mode": mode,
        "status": "complete" if best is not None else "no_feasible_bundle",
        "items": best or [], "total_price": sum(p["price"] for p in best) if best else 0,
        "currency": "VND", "budget": request.budget, "missing_slots": missing,
        "reason": None if best else ("missing_candidates" if missing else "budget_or_candidate_limit"),
        "alternatives_by_slot": {} if best else choices,
        "compatibility_note": "Role/budget constraints only. No learned aesthetic compatibility or size validation.",
    }
