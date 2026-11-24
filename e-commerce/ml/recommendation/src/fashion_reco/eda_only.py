"""Dependency-free EDA entrypoint for Kaggle; no pip, encoder or training."""
from bisect import bisect_right
from collections import Counter, defaultdict
import csv
import html
import json
import math
from pathlib import Path

from .data import dump_json, load_catalog, load_requests


def percentiles(values, levels=(0, 25, 50, 75, 95, 100)):
    values = sorted(values)
    result = {}
    for level in levels:
        position = (len(values)-1)*level/100
        low, high = math.floor(position), math.ceil(position)
        result[str(level)] = values[low] + (values[high]-values[low])*(position-low)
    return result


def write_csv(path, rows):
    if not rows:
        return
    with Path(path).open('w',encoding='utf-8-sig',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_eda(catalog_path, output_dir, queries_path):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    products, manifest = load_catalog(catalog_path)
    requests = load_requests(queries_path)
    grouped = defaultdict(list)
    for p in products:
        grouped[p['slot']].append(p)
    groups = [{'slot':slot,'products':len(rows),'available':sum(p['available'] for p in rows)}
              for slot,rows in sorted(grouped.items())]
    prices_by_mode = {
        mode:{slot:sorted(p['price'] for p in rows if mode=='research' or p['available'])
              for slot,rows in grouped.items()}
        for mode in ('research','available_only')}
    by_id = {p['id']:p for p in products}
    coverage = []
    for request in requests:
        for mode in ('research','available_only'):
            for slot in request.slots:
                count = bisect_right(prices_by_mode[mode].get(slot,[]),request.budget)
                for pid in set(request.owned_product_ids)|set(request.excluded_product_ids):
                    p = by_id.get(pid)
                    if p and p['slot']==slot and p['price']<=request.budget and (mode=='research' or p['available']):
                        count -= 1
                coverage.append({'query_id':request.query_id,'mode':mode,'slot':slot,'count':count})
    report = {**manifest,'price_percentiles':percentiles([p['price'] for p in products]),
              'description_lengths':percentiles([len(p['description']) for p in products]),
              'coverage':coverage,'runtime':'Python standard library; no package installation or local training'}
    dump_json(output/'eda.json',report)
    dump_json(output/'catalog-manifest.json',manifest)
    dump_json(output/'catalog.cleaned.json',products)
    write_csv(output/'eda-groups.csv',groups)
    write_csv(output/'eda-query-coverage.csv',coverage)
    # Standalone HTML table, safe even when plotting packages are absent.
    table = ''.join(f"<tr><td>{html.escape(r['slot'])}</td><td>{r['products']}</td><td>{r['available']}</td></tr>" for r in groups)
    document = ('<!doctype html><html lang="vi"><meta charset="utf-8"><title>Tiki EDA</title>'
                '<style>body{font:16px system-ui;max-width:1000px;margin:40px auto}table{border-collapse:collapse}td,th{padding:8px 16px;border:1px solid #ccc}</style>'
                f"<h1>EDA catalog Tiki</h1><p>{len(products):,} sản phẩm hợp lệ. SHA-256: {manifest['sha256']}</p>"
                '<p>Availability là snapshot nguồn. Các nhóm thu theo truy vấn cần nhóm kiểm tra thủ công.</p>'
                '<table><tr><th>Loại món</th><th>Tổng</th><th>Available</th></tr>'+table+'</table></html>')
    (output/'eda-summary.html').write_text(document,encoding='utf-8')
    print(json.dumps({'valid_count':len(products),'available':sum(p['available'] for p in products),
                      'missing_images':manifest['missing_images'],'issues':manifest['issues'],
                      'output_dir':str(output)},ensure_ascii=False),flush=True)
    return report
