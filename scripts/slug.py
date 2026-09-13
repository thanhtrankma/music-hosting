"""Chuẩn hoá tên file: bỏ dấu tiếng Việt, chữ thường, chỉ giữ a-z0-9-_."""
import re, unicodedata

_VI = str.maketrans({"đ": "d", "Đ": "d"})


def slugify(name: str) -> str:
    name = name.translate(_VI)
    name = unicodedata.normalize("NFD", name)
    name = "".join(ch for ch in name if unicodedata.category(ch) != "Mn")
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    return name.strip("-") or "track"


def slug_filename(filename: str) -> str:
    base, dot, ext = filename.rpartition(".")
    if not dot:
        return slugify(filename)
    return f"{slugify(base)}.{ext.lower()}"
