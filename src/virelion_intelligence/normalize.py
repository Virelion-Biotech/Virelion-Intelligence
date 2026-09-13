from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime, timezone


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.casefold()
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def canonical_title(value: str) -> str:
    return normalize_text(value)


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value, flags=re.I)
    value = value.removeprefix("doi:").strip()
    return value.lower() or None


def normalize_pmid(value: str | int | None) -> str | None:
    if value is None:
        return None
    digits = re.sub(r"\D", "", str(value))
    return digits or None


def normalize_accession(value: str | None) -> str | None:
    if not value:
        return None
    return value.strip().upper() or None


def content_hash(*parts: str | None) -> str:
    payload = "\n".join(p or "" for p in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
