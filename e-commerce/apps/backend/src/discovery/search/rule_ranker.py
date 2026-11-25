"""Tìm ứng viên và xếp hạng kết quả catalog theo quy tắc."""
from sqlalchemy import Float, and_, case, column, func, literal_column, or_, table
from sqlalchemy.dialects.postgresql import UUID

from catalog.model import Category, Product
from catalog.text import normalize_name

# Chỉ đọc hai cột đã có trong migration của bảng thống kê phổ biến.
popularity = table("product_popularity", column("product_id", UUID()), column("score", Float()))


def _normalized(column_value):
    decomposed = func.normalize(func.lower(column_value), literal_column("NFD"))
    return func.replace(func.regexp_replace(decomposed, "[\u0300-\u036f]", "", "g"), "đ", "d")


def rank_products(stmt, query: str, parent_category):
    terms = normalize_name(query).split()
    if not terms:
        return stmt.order_by(Product.created_at.desc(), Product.id.desc())

    attributes = (Product.name_normalized, *map(_normalized, (Product.brand, Category.name, parent_category.name)))
    description = _normalized(Product.description)
    structured_matches = [
        or_(*(attribute.contains(term, autoescape=True) for attribute in attributes))
        for term in terms
    ]
    matches = [
        or_(structured, description.contains(term, autoescape=True))
        for term, structured in zip(terms, structured_matches)
    ]
    relevance = case(
        (func.regexp_replace(Product.name_normalized, "[[:space:]]+", " ", "g") == " ".join(terms), 0),
        (and_(*structured_matches), 1),
        else_=2,
    )
    return (
        stmt.outerjoin(popularity, popularity.c.product_id == Product.id)
        .where(*matches)
        .order_by(relevance, popularity.c.score.desc().nulls_last(), Product.id)
    )
