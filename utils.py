#!/usr/bin/env python3
import sys
import re
import logging
from typing import List
from pathlib import Path

"""function.py

All vCard utility function implementations (extracted from vcard.py).
"""

__version__ = "0.1.0"
_categorycounts = {}  # module-level store for last computed category counts

def count_categories(files: List[str] = None, output=None):
    """Compute (if files provided) and/or print stored category counts; return dict copy."""
    global _categorycounts

    # Compute counts if files given
    if files:
        counts = {}
        for p in files:
            p = Path(p)
            if not p.exists():
                logging.warning("%s not found, skipping", p)
                continue
            text = read_file_as_utf8(p)
            for vcard in iter_vcards(text):
                cats = [c.lower() for c in get_categories(vcard)]
                for c in cats:
                    counts[c] = counts.get(c, 0) + 1
        _categorycounts = counts

    # Default output
    if output is None:
        output = sys.stderr

    # Print stored counts
    if not _categorycounts:
        print("No category counts available", file=output)
    else:
        print("Category counts:", file=output)
        for k in sorted(_categorycounts):
            print(f"  {k}: {_categorycounts[k]}", file=output)

    return dict(_categorycounts)

def unfold(text):
    """Unfold folded vCard lines."""
    return text.replace('\r\n', '\n').replace('\r', '\n').replace('\n ', '').replace('\n\t', '\n')

def iter_vcards(text):
    """Yield individual vCard texts from a combined vCard stream."""
    text = unfold(text)
    lines = text.splitlines()
    card = []
    in_card = False
    for ln in lines:
        up = ln.strip().upper()
        if up == "BEGIN:VCARD":
            in_card = True
            card = [ln]
        elif up == "END:VCARD":
            if in_card:
                card.append(ln)
                yield "\n".join(card)
                in_card = False
                card = []
        else:
            if in_card:
                card.append(ln)

def categories_from_vcard(card_text):
    """Extract categories from a single vCard."""
    cats = []
    for ln in card_text.splitlines():
        if ln.upper().startswith("CATEGORIES:"):
            cats_part = ln.split(":", 1)[1]
            cats = [c.strip().lower() for c in cats_part.split(",") if c.strip()]
            break
    return set(cats)

def read_file_as_utf8(path: Path) -> str:
    """Read bytes from path and return a str decoded to UTF-8 (best-effort)."""
    encodings = ("utf-8", "utf-8-sig", "utf-16", "latin-1", "cp1252")
    b = path.read_bytes()
    for enc in encodings:
        try:
            text = b.decode(enc)
            return text.replace('\r\n', '\n').replace('\r', '\n')
        except (UnicodeDecodeError, LookupError):
            continue
    return b.decode("utf-8", errors="replace").replace('\r\n', '\n').replace('\r', '\n')

def read_vcards(files: List[str]) -> List[str]:
    """Read vCard blocks from files (BEGIN:VCARD ... END:VCARD)."""
    cards = []
    for path in files:
        p = Path(path)
        if not p.exists():
            logging.warning("%s not found, skipping", p)
            continue
        text = read_file_as_utf8(p)
        for vcard in iter_vcards(text):
            cards.append(vcard)
    return cards

def get_categories(card: str) -> List[str]:
    """Extract categories from a vCard block. Matches CATEGORIES: or CATEGORY: (case-insensitive)."""
    for line in card.splitlines():
        m = re.match(r'(?i)^(?:CATEGORIES|CATEGORY):\s*(.+)$', line)
        if m:
            parts = m.group(1).strip()
            items = [p.strip() for p in re.split(r'[;,]', parts) if p.strip()]
            return items
    return []

def get_name(card: str) -> str:
    """Extract a display name from a vCard block."""
    for line in card.splitlines():
        m = re.match(r'(?i)^FN:\s*(.+)$', line)
        if m:
            return m.group(1).strip()
    for line in card.splitlines():
        m = re.match(r'(?i)^N:\s*(.+)$', line)
        if m:
            parts = [p.strip() for p in m.group(1).split(';')]
            family = parts[0] if len(parts) > 0 else ""
            given = parts[1] if len(parts) > 1 else ""
            name = " ".join(p for p in (given, family) if p)
            return name
    return ""

def get_numbers(card: str) -> List[str]:
    """Extract telephone numbers (TEL properties) from a vCard block."""
    nums = []
    for line in card.splitlines():
        m = re.match(r'(?i)^TEL(?:;[^:]*)?:\s*(.+)$', line)
        if m:
            val = m.group(1).strip()
            if val:
                nums.append(val)
    return nums

def _normalize_categories(value) -> List[str]:
    if not value:
        return []
    if isinstance(value, str):
        items = [value]
    else:
        items = value
    normalized = []
    for item in items:
        for part in re.split(r'[;,]', str(item)):
            part = part.strip().lower()
            if part:
                normalized.append(part)
    return normalized

def categorycontacts(categories=None, files: List[str] = None, must_have=None, exclude=None) -> List[str]:
    """Return vCard blocks matching include categories while enforcing required/excluded ones."""
    include = _normalize_categories(categories)
    required = set(_normalize_categories(must_have))
    exclude = set(_normalize_categories(exclude))

    if files is None:
        files = []

    results = []
    for card in read_vcards(files):
        card_cats = {c.lower() for c in get_categories(card)}
        if exclude and any(cat in card_cats for cat in exclude):
            continue
        include_ok = True if not include else any(cat in card_cats for cat in include)
        required_ok = all(cat in card_cats for cat in required)
        if include_ok and required_ok:
            results.append(card)
    return results


__all__ = [
    "count_categories",
    "unfold",
    "iter_vcards",
    "categories_from_vcard",
    "read_file_as_utf8",
    "read_vcards",
    "get_categories",
    "get_name",
    "get_numbers",
    "categorycontacts",
]
