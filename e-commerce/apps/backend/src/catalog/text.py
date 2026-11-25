"""Chuẩn hóa tên sản phẩm theo cách dùng trong products.name_normalized."""
import unicodedata


def normalize_name(text: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
        if unicodedata.category(char) != "Mn"
    )
