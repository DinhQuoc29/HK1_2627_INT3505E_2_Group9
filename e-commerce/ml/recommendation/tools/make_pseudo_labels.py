"""Rule-based weak labels for pipeline smoke tests, never human ground truth."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import zipfile

VERSION = 'rule_teacher_v1'
TYPE_TERMS = {
    'men_shirts':['ao so mi'], 'men_trousers':['quan tay','quan au','kaki'],
    'men_tshirts':['ao thun','ao phong','t shirt','tshirt'], 'men_blazers':['blazer','ao vest'],
    'men_jeans':['jean','jeans','denim'], 'men_polos':['polo'],
    'men_jackets':['ao khoac','jacket'], 'men_shorts':['quan short','quan lung','quan dui'],
    'men_suits':['bo vest','suit','com le'], 'men_sweaters':['ao len','sweater'],
    'women_dresses':['dam','vay lien','vay dam','dress'], 'women_blouses':['ao kieu','blouse'],
    'women_skirts':['chan vay'], 'women_trousers':['quan'], 'women_shirts':['ao so mi'],
    'women_jeans':['jean','jeans','denim'], 'women_blazers':['blazer','ao vest'],
    'women_tshirts':['ao thun','ao phong','t shirt','tshirt'], 'women_jackets':['ao khoac','jacket'],
    'men_shoes':['giay'], 'women_shoes':['giay','sandal','cao got'],
    'men_bags':['tui'], 'women_bags':['tui','clutch'],
    'backpacks_suitcases':['balo','ba lo','vali','va li'],
    'fashion_accessories':['that lung','day nit','khan','mu','non','kinh','phu kien'],
}
# The teacher sees only the request and product text/price/role, no scores or split.
CONTEXTS = {
    'formal': {
        'query':['cuoi','du tiec','lich su','trang trong','thanh lich','trang nha','van phong','phong van','tot nghiep','kin dao'],
        'item':['cong so','du tiec','thanh lich','lich su','sang trong','trang nha','vest','so mi','quan tay','quan au','giay tay','cao got','clutch'],
        'conflict':['do ngu','ao ngu','vay ngu','quan ngu','do boi','bikini','quan tap','giay da bong','dep di trong nha']},
    'sport': {
        'query':['the thao','chay bo','tap gym','van dong','di bo'],
        'item':['the thao','chay bo','gym','sneaker','thoang khi','co gian','tham hut'],
        'conflict':['cao got','giay tay','vest','du tiec']},
    'casual': {
        'query':['ca phe','cuoi tuan','dao pho','hang ngay','di hoc','don gian','thoai mai','tre trung'],
        'item':['casual','thoai mai','don gian','tre trung','cotton','ao thun','polo','jean','sneaker','balo'],
        'conflict':[]},
    'cold': {
        'query':['mua dong','troi lanh','giu am','da lat'],
        'item':['giu am','ao len','long cuu','ao khoac','sweater','ni','day dan'],
        'conflict':['do boi','bikini']},
    'travel': {
        'query':['du lich','di choi','hanh ly','chuyen di'],
        'item':['du lich','gon nhe','nhe','nhieu ngan','chong nuoc','vali','balo','de mang'],
        'conflict':[]},
}
ATTRIBUTES = ['cotton','linen','vai lanh','den','trang','toi mau','nho gon','tui nho','kin dao','co gian','chong nuoc','tay dai','tay ngan']
WRONG_COMPONENTS = ['day deo tui','day tui xach','lot giay','day giay','moc khoa','vo boc vali','tui dung giay','tui giat']


def normalize(text):
    text = unicodedata.normalize('NFD',str(text).lower().replace('đ','d'))
    text = ''.join(c for c in text if unicodedata.category(c)!='Mn')
    return ' '.join(re.findall(r'\w+',text))


def hits(text, terms):
    return [term for term in terms if ' '+term+' ' in ' '+text+' ']


def grade(query, product):
    if product['slot'] not in query['slots'] or product['price'] > query['budget'] or product['id'] in query.get('excluded_product_ids',[]) or product['id'] in query.get('owned_product_ids',[]):
        return 0, {'reason':'explicit_role_price_or_id_constraint'}
    name = normalize(product['name'])
    text = normalize(product['name']+' '+product['description'])
    request = normalize(query['text'])
    wrong = hits(name,WRONG_COMPONENTS) if product['slot']!='fashion_accessories' else []
    if wrong:
        return 0, {'reason':'component_instead_of_requested_product','evidence':wrong}
    type_match = hits(name,TYPE_TERMS[product['slot']])
    active = [name for name,c in CONTEXTS.items() if hits(request,c['query'])]
    positive = sorted({term for name in active for term in hits(text,CONTEXTS[name]['item'])})
    conflicts = sorted({term for name in active for term in hits(normalize(product['name']),CONTEXTS[name]['conflict'])})
    attrs = hits(request,ATTRIBUTES)
    attr_match = hits(text,attrs)
    value = 2 if type_match else 1
    if type_match and (positive or attr_match):
        value = 3
    if conflicts:
        value = min(value,1)
    return value, {'type_terms':type_match,'contexts':active,'positive_terms':positive,
                   'attribute_terms':attr_match,'conflicting_title_terms':conflicts,
                   'reason':'deterministic_text_rules_not_image_or_human_judgment'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def generate(results, queries_file, destination):
    results,destination=Path(results),Path(destination)
    if destination.exists():
        raise FileExistsError('Never overwrite labels. Choose a new pseudo experiment folder.')
    products=json.loads((results/'catalog.cleaned.json').read_text(encoding='utf-8'))
    products={p['id']:p for p in products}
    queries={q['query_id']:q for q in (json.loads(line) for line in Path(queries_file).read_text(encoding='utf-8').splitlines() if line.strip())}
    with (results/'labeling/judgments.csv').open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream); columns=reader.fieldnames; rows=list(reader)
    pool=json.loads((results/'labeling/pool-manifest.json').read_text(encoding='utf-8'))
    from dataclasses import asdict
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    from fashion_reco.schemas import ShoppingRequest
    # Match the exact frozen request hash before using a locally provided query file.
    query_hash=hashlib.sha256(json.dumps([asdict(ShoppingRequest.from_dict(q)) for q in queries.values()],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    if query_hash!=pool['query_sha256']:
        raise ValueError('Queries differ from frozen annotation pool')
    expected={tuple(k) for k in pool['candidate_keys']}
    seen=set(); audit=[]; counts=defaultdict(Counter); groups=defaultdict(set)
    for row in rows:
        key=(row['query_id'],row['slot'],row['product_id'])
        if key in seen or key not in expected:
            raise ValueError('Pool keys modified')
        seen.add(key)
        q,p=queries[row['query_id']],products[row['product_id']]
        if row['slot']!=p['slot'] or int(row['price'])!=p['price']:
            raise ValueError('Product fields differ from frozen catalog')
        score,evidence=grade(q,p)
        row.update(grade=str(score),annotator=VERSION,notes='PSEUDO LABEL; NOT HUMAN; '+json.dumps(evidence,ensure_ascii=False))
        counts[row['split']][score]+=1;groups[(row['split'],row['query_id'],row['slot'])].add(score)
        audit.append({'query_id':row['query_id'],'slot':row['slot'],'product_id':row['product_id'],'grade':score,**evidence})
    if seen!=expected:
        raise ValueError('Pool rows missing')
    destination.mkdir(parents=True)
    for name,subset in [('judgments.csv',[r for r in rows if r['split'] in ('train','validation')]),
                        ('test-adjudicated.csv',[r for r in rows if r['split']=='test'])]:
        with (destination/name).open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader();writer.writerows(subset)
    metadata={'label_origin':VERSION,'purpose':'pipeline_smoke_test_only',
              'catalog_sha256':pool['catalog_sha256'],'pool_sha256':sha(results/'labeling/pool-manifest.json'),
              'query_sha256':pool['query_sha256'],'teacher_code_sha256':sha(__file__),
              'row_count':len(rows),'grade_distribution':{s:dict(c) for s,c in counts.items()},
              'mixed_grade_groups':{s:sum(k[0]==s and len(v)>1 for k,v in groups.items()) for s in counts},
              'warnings':['Test labels come from the same rules as train: metrics measure agreement with this teacher, not independent recommendation quality.',
                          'No image content analyzed. Text and collection groups may be noisy. Stock is filtered separately.',
                          'No rater agreement or human adjudication performed. test-adjudicated.csv is only the legacy pipeline input filename.',
                          'Do not merge with human labels or claim a production winner.'],
              'files':{name:sha(destination/name) for name in ('judgments.csv','test-adjudicated.csv')}}
    (destination/'pseudo-label-manifest.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    (destination/'teacher-audit.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in audit),encoding='utf-8')
    (destination/'README.txt').write_text('NHÃN YẾU TỰ SINH — CHỈ KIỂM TRA PIPELINE\nKhông phải nhãn người chấm. Test và train dùng cùng bộ quy tắc.\nKhông kết luận mô hình tốt nhất cho người dùng từ các điểm này.\nKhông có phân tích nội dung hình ảnh.\n',encoding='utf-8')
    archive=destination/'pseudo-labels-rule-v1.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for name in ('judgments.csv','test-adjudicated.csv','pseudo-label-manifest.json','teacher-audit.jsonl','README.txt'):
            z.write(destination/name,name)
    print(json.dumps(metadata,ensure_ascii=False,indent=2))
    return archive


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results',required=True)
    parser.add_argument('--queries',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args();generate(args.results,args.queries,args.output)
