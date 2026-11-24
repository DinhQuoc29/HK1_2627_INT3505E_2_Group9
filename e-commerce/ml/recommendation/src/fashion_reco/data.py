from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata

from .schemas import ShoppingRequest, SLOTS

ALIASES = {
    "women_party_dresses": "women_dresses", "women_maxi_dresses": "women_dresses",
    "women_office_dresses": "women_dresses", "men_linen_shirts": "men_shirts",
    "men_khaki": "men_trousers",
}


def normalize(text):
    text = unicodedata.normalize("NFD", str(text or "").casefold().replace("đ", "d"))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return " ".join(re.findall(r"\w+", text))


def text_value(value):
    if isinstance(value, dict):
        return str(value.get("name") or "")
    return str(value or "")


def dump_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def load_catalog(path):
    path = Path(path)
    source_bytes = path.read_bytes()
    raw = json.loads(source_bytes.decode("utf-8-sig"))
    if not isinstance(raw, list):
        raise ValueError("Catalog must be a JSON array")
    products, seen, issues = [], set(), Counter()
    for row in raw:
        pid = str(row.get("productId") or "")
        price = row.get("price")
        name = text_value(row.get("name")).strip()
        if not pid or not name or isinstance(price, bool) or not isinstance(price, (int, float)) or not math.isfinite(price) or price <= 0 or int(price) != price or row.get("currency", "VND") != "VND":
            issues["invalid_id_name_price_currency"] += 1
            continue
        if pid in seen:
            issues["duplicate_id"] += 1
            continue
        seen.add(pid)
        slot = ALIASES.get(row.get("collectionGroup"), row.get("collectionGroup"))
        if slot not in SLOTS:
            issues["unknown_slot"] += 1
            continue
        description = text_value(row.get("description"))
        brand = text_value(row.get("brandName"))
        image = row.get("thumbnailUrl") or ""
        product = {
            "id": pid, "name": name, "description": description,
            "slot": slot, "source_group": row.get("collectionGroup"),
            "brand": brand, "price": int(price), "currency": "VND",
            "available": row.get("inventoryStatus") == "available",
            "inventory_status": row.get("inventoryStatus"),
            "image_url": image if isinstance(image, str) and image.startswith("https://") else "",
            "source_url": row.get("productUrl"),
            "rating": row.get("ratingAverage"), "review_count": row.get("reviewCount"),
            "source_fetched_at": row.get("detailFetchedAt"),
        }
        # Do not index raw HTML or the whole historical snapshot.
        product["text"] = ". ".join([name, name, brand, text_value(row.get("categoryName")), description])
        products.append(product)
    if not products:
        raise ValueError("No valid products remain")
    summary = {
        "source_path": str(path), "sha256": hashlib.sha256(source_bytes).hexdigest(),
        "raw_count": len(raw), "valid_count": len(products), "issues": dict(issues),
        "groups": dict(Counter(p["slot"] for p in products)),
        "inventory_statuses": dict(Counter(str(p["inventory_status"]) for p in products)),
        "missing_images": sum(not p["image_url"] for p in products),
        "missing_descriptions": sum(not p["description"].strip() for p in products),
        "unique_images": len({p["image_url"] for p in products if p["image_url"]}),
        "availability_note": "Source snapshot, not a live stock guarantee. Query groups require human semantic QA.",
    }
    return products, summary


def load_requests(path):
    requests = [ShoppingRequest.from_dict(json.loads(line)) for line in Path(path).read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if len({q.query_id for q in requests}) != len(requests):
        raise ValueError("Duplicate query IDs")
    return requests


def validate_splits(requests, splits):
    lookup = {q.query_id: q for q in requests}
    seen_ids, seen_families = set(), set()
    for name in ("train", "validation", "test"):
        ids = splits[name]
        if len(set(ids)) != len(ids) or set(ids) - lookup.keys() or seen_ids.intersection(ids):
            raise ValueError("Missing, duplicated or overlapping query split")
        families = {lookup[i].family_id for i in ids}
        if seen_families.intersection(families):
            raise ValueError("Scenario family leakage across splits")
        seen_ids.update(ids)
        seen_families.update(families)
    if seen_ids != lookup.keys():
        raise ValueError("Every query must belong to exactly one split")
