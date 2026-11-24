"""Regenerate editable scenario templates before annotation; never generates labels."""
import json
from pathlib import Path
import random

SCENARIOS = [
    ('wedding_woman', 'Tôi đi ăn cưới buổi tối, thích vẻ thanh lịch, cần đầm và túi nhỏ.', ['women_dresses','women_bags'], [500000,1000000,2000000]),
    ('wedding_man', 'Tôi dự đám cưới trong nhà, cần áo sơ mi, quần tây và giày lịch sự.', ['men_shirts','men_trousers','men_shoes'], [700000,1500000,3000000]),
    ('wedding_accessories', 'Tôi đã có váy dự tiệc, muốn mua giày và túi nhỏ lịch sự.', ['women_shoes','women_bags'], [300000,700000,1200000]),
    ('groom_guest_suit', 'Tôi cần bộ vest và giày nam trang trọng để dự tiệc cưới.', ['men_suits','men_shoes'], [1000000,2500000,5000000]),
    ('office_woman', 'Tôi đi làm văn phòng, cần áo sơ mi và quần nữ kín đáo.', ['women_shirts','women_trousers'], [400000,800000,1500000]),
    ('office_man', 'Tôi làm công sở, muốn áo polo và quần tây nam dễ mặc.', ['men_polos','men_trousers'], [300000,700000,1400000]),
    ('office_dress', 'Tôi cần đầm công sở và giày nữ để làm việc cả ngày.', ['women_dresses','women_shoes'], [500000,1000000,2000000]),
    ('office_bag', 'Tôi đã có quần áo công sở, cần túi nam và giày nam lịch sự.', ['men_bags','men_shoes'], [500000,1200000,2500000]),
    ('interview_woman', 'Tôi phỏng vấn việc làm, cần blazer nữ và quần nữ trang nhã.', ['women_blazers','women_trousers'], [500000,1200000,2000000]),
    ('interview_man', 'Tôi phỏng vấn việc làm, cần áo sơ mi nam và giày nam lịch sự.', ['men_shirts','men_shoes'], [400000,1000000,2000000]),
    ('graduation_woman', 'Tôi dự lễ tốt nghiệp, muốn áo kiểu nữ và chân váy kín đáo.', ['women_blouses','women_skirts'], [400000,900000,1600000]),
    ('graduation_man', 'Tôi dự lễ tốt nghiệp, cần áo sơ mi nam và quần tây tối màu.', ['men_shirts','men_trousers'], [400000,900000,1800000]),
    ('date_dress', 'Tôi hẹn hò tại nhà hàng, muốn đầm nhẹ nhàng và túi nữ nhỏ.', ['women_dresses','women_bags'], [500000,1000000,1800000]),
    ('date_man', 'Tôi hẹn hò buổi tối, thích áo polo và quần jean nam.', ['men_polos','men_jeans'], [400000,900000,1800000]),
    ('cafe_woman', 'Tôi đi cà phê cuối tuần, muốn áo kiểu nữ và chân váy thoải mái.', ['women_blouses','women_skirts'], [300000,700000,1200000]),
    ('cafe_man', 'Tôi đi cà phê cuối tuần, muốn áo thun và quần jean nam đơn giản.', ['men_tshirts','men_jeans'], [300000,700000,1200000]),
    ('beach_woman', 'Tôi du lịch biển, muốn đầm maxi và túi nữ nhẹ.', ['women_dresses','women_bags'], [400000,900000,1600000]),
    ('beach_man', 'Tôi đi biển, cần áo thun và quần short nam thoáng mát.', ['men_tshirts','men_shorts'], [200000,500000,1000000]),
    ('travel_cold_woman', 'Tôi đi du lịch nơi lạnh, cần áo khoác nữ và quần jean nữ.', ['women_jackets','women_jeans'], [500000,1200000,2200000]),
    ('travel_cold_man', 'Tôi đi du lịch nơi lạnh, cần áo len nam và áo khoác nam.', ['men_sweaters','men_jackets'], [500000,1200000,2200000]),
    ('campus_woman', 'Tôi là sinh viên, cần áo thun nữ và quần jean nữ để đi học.', ['women_tshirts','women_jeans'], [250000,600000,1000000]),
    ('campus_man', 'Tôi là sinh viên, cần áo thun nam và balo để đi học.', ['men_tshirts','backpacks_suitcases'], [250000,600000,1000000]),
    ('presentation_woman', 'Tôi thuyết trình ở trường, cần áo sơ mi nữ và chân váy trang nhã.', ['women_shirts','women_skirts'], [300000,700000,1200000]),
    ('presentation_man', 'Tôi thuyết trình ở trường, muốn áo blazer nam và quần tây.', ['men_blazers','men_trousers'], [500000,1000000,2000000]),
    ('birthday_woman', 'Tôi dự sinh nhật bạn, muốn đầm nữ tươi trẻ và giày nữ.', ['women_dresses','women_shoes'], [400000,900000,1600000]),
    ('birthday_man', 'Tôi dự sinh nhật bạn, muốn áo sơ mi nam thoải mái và quần jean.', ['men_shirts','men_jeans'], [400000,800000,1500000]),
    ('family_woman', 'Tôi đi gặp gia đình, cần áo kiểu nữ và quần nữ kín đáo.', ['women_blouses','women_trousers'], [300000,700000,1400000]),
    ('family_man', 'Tôi đi gặp gia đình, muốn áo polo và quần tây nam nhã nhặn.', ['men_polos','men_trousers'], [300000,700000,1400000]),
    ('business_woman', 'Tôi gặp khách hàng, cần blazer nữ, áo sơ mi nữ và quần nữ.', ['women_blazers','women_shirts','women_trousers'], [800000,1800000,3500000]),
    ('business_man', 'Tôi gặp khách hàng, cần blazer nam, áo sơ mi và giày nam.', ['men_blazers','men_shirts','men_shoes'], [800000,1800000,3500000]),
    ('walk_woman', 'Tôi đi dạo cuối tuần, muốn áo thun nữ và giày nữ thoải mái.', ['women_tshirts','women_shoes'], [250000,600000,1200000]),
    ('walk_man', 'Tôi đi dạo cuối tuần, muốn quần short nam và giày nam thoải mái.', ['men_shorts','men_shoes'], [250000,600000,1200000]),
    ('minimal_woman', 'Tôi thích trang phục nữ tối giản, muốn áo sơ mi và quần nữ màu trung tính.', ['women_shirts','women_trousers'], [400000,900000,1800000]),
    ('minimal_man', 'Tôi thích trang phục nam tối giản, cần áo thun trơn và quần tây.', ['men_tshirts','men_trousers'], [300000,700000,1400000]),
    ('budget_wedding_woman', 'Tôi đã có đầm đi ăn cưới, ngân sách rất thấp, cần giày và túi.', ['women_shoes','women_bags'], [10000,50000,100000]),
    ('budget_formal_man', 'Tôi cần bộ vest và giày nam đi tiệc nhưng có rất ít tiền.', ['men_suits','men_shoes'], [10000,50000,100000]),
    ('evening_woman', 'Tôi đi tiệc tối ngoài trời, muốn đầm và áo khoác nữ nhẹ.', ['women_dresses','women_jackets'], [600000,1400000,2500000]),
    ('evening_man', 'Tôi đi tiệc tối ngoài trời, muốn áo sơ mi và áo khoác nam.', ['men_shirts','men_jackets'], [500000,1200000,2200000]),
    ('single_bag', 'Tôi đã có trang phục dự tiệc, chỉ cần túi nữ cầm tay nhỏ.', ['women_bags'], [100000,300000,700000]),
    ('single_shoes', 'Tôi đã có quần áo dự tiệc, chỉ cần giày nam da lịch sự.', ['men_shoes'], [150000,500000,1200000]),
]


def main():
    root = Path(__file__).resolve().parent.parent
    rows = []
    for family, text, slots, budgets in SCENARIOS:
        for index, budget in enumerate(budgets, 1):
            rows.append({'query_id': f'{family}-{index}', 'family_id': family,
                         'text': text + f' Tổng ngân sách {budget:,} đồng.',
                         'slots': slots, 'budget': budget,
                         'owned_notes': 'Chỉ mua các loại món trong slots; các món đã có được mô tả trong câu nhu cầu.'})
    families = [s[0] for s in SCENARIOS]
    random.Random(42).shuffle(families)
    splits = {name: [r['query_id'] for r in rows if r['family_id'] in group]
              for name, group in [('train',families[:24]),('validation',families[24:32]),('test',families[32:])]}
    (root/'data/queries.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    (root/'data/splits.json').write_text(json.dumps(splits,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Generated 120 UTF-8 scenario templates; existing labels not modified.')


if __name__ == '__main__':
    main()
