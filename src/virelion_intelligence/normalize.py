from __future__ import annotations

import re
import unicodedata
from hashlib import sha256


def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def content_hash(*parts: str) -> str:
    material = "\x1f".join(p.strip() for p in parts)
    return sha256(material.encode("utf-8")).hexdigest()


def canonical_publication_key(title: str, doi: str | None = None, pmid: str | None = None) -> str:
    if doi:
        return f"doi:{doi.strip().lower()}"
    if pmid:
        return f"pmid:{pmid.strip()}"
    return f"title:{normalize_title(title)}"
