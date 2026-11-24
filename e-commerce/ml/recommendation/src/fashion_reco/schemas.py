from dataclasses import dataclass, field

SLOTS = {
    "men_shirts", "men_trousers", "men_tshirts", "men_blazers", "men_jeans",
    "men_polos", "men_jackets", "men_shorts", "men_suits", "men_sweaters",
    "women_dresses", "women_blouses", "women_skirts", "women_trousers",
    "women_shirts", "women_jeans", "women_blazers", "women_tshirts",
    "women_jackets", "men_shoes", "women_shoes", "men_bags", "women_bags",
    "backpacks_suitcases", "fashion_accessories",
}


@dataclass(frozen=True)
class ShoppingRequest:
    query_id: str
    family_id: str
    text: str
    slots: tuple[str, ...]
    budget: int
    owned_product_ids: tuple[str, ...] = field(default_factory=tuple)
    excluded_product_ids: tuple[str, ...] = field(default_factory=tuple)
    owned_notes: str = ""

    def __post_init__(self):
        if not self.query_id or not self.family_id or not self.text.strip():
            raise ValueError("query_id, family_id and text are required")
        if isinstance(self.budget, bool) or not isinstance(self.budget, int) or self.budget <= 0:
            raise ValueError("budget must be a positive integer in VND")
        if not 1 <= len(self.slots) <= 4 or len(set(self.slots)) != len(self.slots):
            raise ValueError("Clarify 1–4 distinct required slots before recommendation")
        if set(self.slots) - SLOTS:
            raise ValueError(f"Unknown slots: {set(self.slots) - SLOTS}")

    @classmethod
    def from_dict(cls, value):
        fields = dict(value)
        for key in ("slots", "owned_product_ids", "excluded_product_ids"):
            if key in fields:
                fields[key] = tuple(fields[key])
        return cls(**fields)

    def slot_query(self, slot):
        return f"{self.text}. Loại sản phẩm cần tìm: {SLOT_NAMES[slot]}."


SLOT_NAMES = {
    "men_shirts": "áo sơ mi nam", "men_trousers": "quần tây kaki nam",
    "men_tshirts": "áo thun nam", "men_blazers": "áo vest blazer nam",
    "men_jeans": "quần jean nam", "men_polos": "áo polo nam",
    "men_jackets": "áo khoác nam", "men_shorts": "quần short nam",
    "men_suits": "bộ vest nam", "men_sweaters": "áo len nam",
    "women_dresses": "váy đầm nữ", "women_blouses": "áo kiểu nữ",
    "women_skirts": "chân váy nữ", "women_trousers": "quần nữ",
    "women_shirts": "áo sơ mi nữ", "women_jeans": "quần jean nữ",
    "women_blazers": "áo vest blazer nữ", "women_tshirts": "áo thun nữ",
    "women_jackets": "áo khoác nữ", "men_shoes": "giày nam",
    "women_shoes": "giày nữ", "men_bags": "túi nam", "women_bags": "túi nữ",
    "backpacks_suitcases": "balo vali", "fashion_accessories": "phụ kiện thời trang",
}
