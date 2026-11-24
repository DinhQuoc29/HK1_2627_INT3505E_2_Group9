import csv
import hashlib
import json
from pathlib import Path

from .candidates import candidate_pool
from .data import dump_json


def query_hash(requests):
    from dataclasses import asdict
    return hashlib.sha256(json.dumps([asdict(q) for q in requests], sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def export_labeling(requests, products, retrievers, splits, catalog_manifest, directory, max_total=60):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "judgments.csv"
    if path.exists():
        raise FileExistsError("Label pool already exists. Preserve human labels; use a new output directory.")
    split_for = {qid: split for split, ids in splits.items() for qid in ids}
    rows, empty_slots = [], []
    for request in requests:
        pool = candidate_pool(request, products, retrievers, max_total=max_total)
        found = set()
        for index in sorted(pool, key=lambda i: (products[i]["slot"], products[i]["id"])):
            p = products[index]
            found.add(p["slot"])
            rows.append({"query_id": request.query_id, "family_id": request.family_id,
                         "split": split_for[request.query_id], "query": request.text,
                         "budget": request.budget, "slot": p["slot"], "product_id": p["id"],
                         "product_name": p["name"], "price": p["price"], "description": p["description"],
                         "image_url": p["image_url"], "inventory_status": p["inventory_status"],
                         "grade": "", "annotator": "", "notes": ""})
        for slot in set(request.slots) - found:
            empty_slots.append({"query_id": request.query_id, "slot": slot})
    if not rows:
        raise ValueError("No candidates to label; inspect catalog coverage")
    for name, subset in (("judgments.csv", rows),
                         ("test-rater-a.csv", [r for r in rows if r["split"] == "test"]),
                         ("test-rater-b.csv", [r for r in rows if r["split"] == "test"])):
        with (directory / name).open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(subset)
    metadata = {"catalog_sha256": catalog_manifest["sha256"], "query_sha256": query_hash(requests),
                "row_count": len(rows), "retrievers": list(retrievers), "max_candidates": max_total,
                "candidate_keys": [[r["query_id"], r["slot"], r["product_id"]] for r in rows],
                "empty_slots": empty_slots,
                "note": "Pooled candidates, not exhaustive catalog relevance. No labels generated automatically."}
    dump_json(directory / 'pool-manifest.json', metadata)
    return metadata


def load_judgments(path, requests, products, pool_manifest, catalog_manifest, required_ids):
    if pool_manifest["catalog_sha256"] != catalog_manifest["sha256"] or pool_manifest["query_sha256"] != query_hash(requests):
        raise ValueError("Catalog/queries changed after annotation pool was frozen")
    lookup = {q.query_id: q for q in requests}
    by_id = {p["id"]: p for p in products}
    expected = {tuple(key) for key in pool_manifest["candidate_keys"] if key[0] in required_ids}
    seen, judgments = set(), {}
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        for row in csv.DictReader(stream):
            if row["query_id"] not in required_ids:
                continue  # Do not require or consume held-out test grades during training.
            key = (row["query_id"], row["slot"], row["product_id"])
            if key in seen or key not in expected:
                raise ValueError(f"Duplicate or modified annotation key: {key}")
            seen.add(key)
            if row["grade"] not in ('0', '1', '2', '3') or not row.get("annotator", "").strip():
                raise ValueError(f"Missing grade 0–3 or annotator: {key}")
            if row["slot"] not in lookup[row["query_id"]].slots or by_id[row["product_id"]]["slot"] != row["slot"]:
                raise ValueError(f"Slot mismatch: {key}")
            judgments.setdefault(key[:2], {})[key[2]] = int(row["grade"])
    if seen != expected:
        raise ValueError("Annotation rows removed from the frozen pool")
    return judgments


def adjudicate_test(path_a, path_b, destination):
    """Require human resolution where raters disagree; never average by default."""
    def read(path):
        with Path(path).open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
        result = {}
        for row in rows:
            key = (row['query_id'], row['slot'], row['product_id'])
            if key in result or row['grade'] not in ('0', '1', '2', '3') or not row['annotator'].strip():
                raise ValueError('Incomplete or duplicate rater judgments')
            result[key] = row
        return result
    a, b = read(path_a), read(path_b)
    if a.keys() != b.keys() or not a:
        raise ValueError('Raters must judge the same nonempty pool')
    rows = []
    for key, row in a.items():
        other = b[key]
        if row['annotator'].strip() == other['annotator'].strip():
            raise ValueError('Test raters must be different people')
        rows.append({**row, 'grade': row['grade'] if row['grade'] == other['grade'] else '',
                     'annotator': row['annotator'] + '+' + other['annotator'],
                     'notes': f"rater_a={row['grade']}; rater_b={other['grade']}; resolve disagreements manually"})
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    with destination.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return {'count': len(rows), 'agreement': sum(bool(r['grade']) for r in rows) / len(rows)}
