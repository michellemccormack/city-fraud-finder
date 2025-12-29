from __future__ import annotations
import re
from difflib import SequenceMatcher
from typing import Optional

COMMON_SUFFIXES = [
    " llc", " inc", " corp", " co", " ltd", " company", " incorporated", " foundation",
    " pc", " pllc", " llp", " lp", " nonprofit", " non profit"
]

def normalize_name(name: Optional[str]) -> str:
    if not name:
        return ""
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    for suf in COMMON_SUFFIXES:
        if s.endswith(suf):
            s = s[: -len(suf)].strip()
    return s

def normalize_address(addr: Optional[str]) -> str:
    if not addr:
        return ""
    s = addr.strip().lower()
    s = re.sub(r"\bst\b", "street", s)
    s = re.sub(r"\brd\b", "road", s)
    s = re.sub(r"\bave\b", "avenue", s)
    s = re.sub(r"\bblvd\b", "boulevard", s)
    s = re.sub(r"\bdr\b", "drive", s)
    s = re.sub(r"\bapt\b", "apartment", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()

def safe_int(v) -> Optional[int]:
    if v is None:
        return None
    try:
        v2 = str(v).strip().replace(",", "")
        if v2 == "":
            return None
        return int(float(v2))
    except Exception:
        return None

def safe_float(v) -> float:
    if v is None:
        return 0.0
    try:
        return float(str(v).strip().replace(",", ""))
    except Exception:
        return 0.0

def best_effort_zip(z) -> Optional[str]:
    if not z:
        return None
    z = str(z).strip()
    m = re.match(r"^(\d{5})", z)
    return m.group(1) if m else None
