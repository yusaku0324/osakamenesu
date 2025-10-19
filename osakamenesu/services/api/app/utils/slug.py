from __future__ import annotations

import re
import unicodedata


def slugify(value: str) -> str:
    """
    Generate a URL-safe slug from an arbitrary string.
    """
    normalized = unicodedata.normalize("NFKC", value or "").strip()
    if not normalized:
        return ""

    slug = re.sub(r"[^\w\-]+", "-", normalized.lower())
    slug = re.sub(r"-{2,}", "-", slug).strip("-_")
    return slug
