def eligible(product, request, mode="research", slot=None):
    if mode not in ("research", "available_only"):
        raise ValueError("Unknown catalog mode")
    excluded = set(request.owned_product_ids) | set(request.excluded_product_ids)
    return (
        product["id"] not in excluded
        and 0 < product["price"] <= request.budget
        and (slot is None or product["slot"] == slot)
        and (mode == "research" or product["available"])
    )
