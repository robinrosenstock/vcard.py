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

def categorycounts(files: List[str] = None, output=None):
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

def categorycontacts(categories, files: List[str]) -> List[str]:
    """Return vCard blocks that have any of the specified categories (case-insensitive)."""
    if isinstance(categories, str):
        cats = [c.strip().lower() for c in re.split(r'[;,]', categories) if c.strip()]
    else:
        cats = [str(c).strip().lower() for c in categories if str(c).strip()]

    if not cats:
        return []

    results = []
    for card in read_vcards(files):
        card_cats = {c.lower() for c in get_categories(card)}
        if any(cat in card_cats for cat in cats):
            results.append(card)
    return results

def categorycontacts_all(categories, files: List[str]) -> List[str]:
    """Return vCard blocks that have all of the specified categories (case-insensitive)."""
    if isinstance(categories, str):
        cats = [c.strip().lower() for c in re.split(r'[;,]', categories) if c.strip()]
    else:
        cats = [str(c).strip().lower() for c in categories if str(c).strip()]

    if not cats:
        return []

    results = []
    for card in read_vcards(files):
        card_cats = {c.lower() for c in get_categories(card)}
        if all(cat in card_cats for cat in cats):
            results.append(card)
    return results

def categorydiff(cat_a: str, cat_b: str, files: List[str]) -> List[str]:
    """Return vCard blocks that have cat_a but not cat_b and record category counts."""
    cards = read_vcards(files)
    out = []
    counts_total = {}
    cat_a = cat_a.lower()
    count_of_cat_a = 0
    cat_b = cat_b.lower()
    count_of_cat_b = 0
    for card in cards:
        name = get_name(card)
        cats = [c.lower() for c in get_categories(card)]
        for c in cats:
            counts_total[c] = counts_total.get(c, 0) + 1
            if cat_a == c:
                print(name)
                count_of_cat_a += 1
            if cat_b == c:
                count_of_cat_b += 1
        if cat_a in cats and cat_b not in cats:
            out.append(card)
    global _categorycounts
    print(count_of_cat_a)
    print(count_of_cat_b)
    _categorycounts = counts_total
    return out


__all__ = [
    "categorycounts",
    "unfold",
    "iter_vcards",
    "categories_from_vcard",
    "read_file_as_utf8",
    "read_vcards",
    "get_categories",
    "get_name",
    "get_numbers",
    "categorycontacts",
    "categorycontacts_all",
    "categorydiff",
]
