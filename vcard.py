#!/usr/bin/env python3
import sys
import re
import argparse
import logging
from typing import List
from pathlib import Path

"""vcard.py

Utilities for vCard (.vcf) processing.
"""

__version__ = "0.1.0"
categorycounts = {}  # module-level store for last computed category counts

def categorycounts(files: List[str] = None, output=None):
    """Compute (if files provided) and/or print stored category counts; return dict copy.

    - If files is provided, compute counts from those files and store in categorycounts.
    - Print the stored counts to `output` (defaults to sys.stderr).
    - Always return a shallow copy of the stored counts.
    """
    global categorycounts

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
        categorycounts = counts

    # Default output
    if output is None:
        output = sys.stderr

    # Print stored counts
    if not categorycounts:
        print("No category counts available", file=output)
    else:
        print("Category counts:", file=output)
        for k in sorted(categorycounts):
            print(f"  {k}: {categorycounts[k]}", file=output)

    return dict(categorycounts)

def unfold(text):
    """Unfold folded vCard lines.

    RFC 6350 line folding: a CRLF followed by a space or tab continues the previous
    line. This function normalizes line endings and removes the folding markers so
    parsing can operate on logical lines.

    Args:
        text (str): Raw file contents.

    Returns:
        str: Unfolded text with normalized newlines.
    """
    return text.replace('\r\n', '\n').replace('\r', '\n').replace('\n ', '').replace('\n\t', '\n')

def iter_vcards(text):
    """Yield individual vCard texts from a combined vCard stream.

    This generator yields each complete vCard (from BEGIN:VCARD to END:VCARD,
    inclusive) as a single string. Incomplete trailing data without END:VCARD
    is ignored.

    Args:
        text (str): Raw file contents (may contain multiple vCards).

    Yields:
        str: One vCard block per iteration.
    """
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
    # if file ended without END:VCARD, ignore incomplete

def categories_from_vcard(card_text):
    """Extract categories from a single vCard.

    Looks for the first CATEGORIES: property (case-insensitive) and returns a set
    of lowercased category names.

    Args:
        card_text (str): The full text of a single vCard.

    Returns:
        set[str]: Lowercased category names (empty set if none found).
    """
    cats = []
    for ln in card_text.splitlines():
        if ln.upper().startswith("CATEGORIES:"):
            cats_part = ln.split(":", 1)[1]
            cats = [c.strip().lower() for c in cats_part.split(",") if c.strip()]
            break
    return set(cats)

def read_file_as_utf8(path: Path) -> str:
    """Read bytes from path and return a str decoded to UTF-8 (best-effort).

    Tries a list of common encodings and falls back to latin-1 to ensure a
    Unicode string is always returned. Normalizes newlines to '\n'.
    """
    encodings = ("utf-8", "utf-8-sig", "utf-16", "latin-1", "cp1252")
    b = path.read_bytes()
    for enc in encodings:
        try:
            text = b.decode(enc)
            # normalize newlines
            return text.replace('\r\n', '\n').replace('\r', '\n')
        except (UnicodeDecodeError, LookupError):
            continue
    # last resort: decode with errors replaced
    return b.decode("utf-8", errors="replace").replace('\r\n', '\n').replace('\r', '\n')

def read_vcards(files: List[str]) -> List[str]:
    """Read vCard blocks from files (BEGIN:VCARD ... END:VCARD)."""
    cards = []
    for path in files:
        p = Path(path)
        if not p.exists():
            logging.warning("%s not found, skipping", p)
            continue
        # Use the utf8-normalized text reader and iterate vCards
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

def categorycontacts(categories, files: List[str]) -> List[str]:
    """Return vCard blocks that have any of the specified categories (case-insensitive).

    Args:
        categories: either a single category string (possibly containing ',', ';' separators)
                    or a list of category strings.
        files: list of .vcf file paths to scan

    Returns:
        list of matching vCard blocks as strings
    """
    # normalize incoming categories to a list of lowercase names
    if isinstance(categories, str):
        cats = [c.strip().lower() for c in re.split(r'[;,]', categories) if c.strip()]
    else:
        cats = [str(c).strip().lower() for c in categories if str(c).strip()]

    if not cats:
        return []

    results = []
    for card in read_vcards(files):
        card_cats = {c.lower() for c in get_categories(card)}
        # include card if it has any of the requested categories (logical OR)
        if any(cat in card_cats for cat in cats):
            results.append(card)
    return results

def get_name(card: str) -> str:
    """Extract a display name from a vCard block.

    Preference order:
      1. FN: property (full name)
      2. N: property (family;given;additional;prefix;suffix) -> "Given Family"

    Returns an empty string if no name property is present.
    """
    # Prefer FN
    for line in card.splitlines():
        m = re.match(r'(?i)^FN:\s*(.+)$', line)
        if m:
            return m.group(1).strip()

    # Fallback to N - format as "Given Family"
    for line in card.splitlines():
        m = re.match(r'(?i)^N:\s*(.+)$', line)
        if m:
            parts = [p.strip() for p in m.group(1).split(';')]
            family = parts[0] if len(parts) > 0 else ""
            given = parts[1] if len(parts) > 1 else ""
            name = " ".join(p for p in (given, family) if p)
            return name

    return ""

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
        # print(name)
        cats = [c.lower() for c in get_categories(card)]
        # cats is the list categories this vcard has
        for c in cats:
            # for all categories in this card, count occurrences
            counts_total[c] = counts_total.get(c, 0) + 1
            if cat_a == c:
                print(name)
                count_of_cat_a = count_of_cat_a + 1
            if cat_b == c:
                count_of_cat_b = count_of_cat_b + 1
        if cat_a in cats and cat_b not in cats:
            out.append(card)
    # store counts for later inspection/printing
    global categorycounts
    # print(counts_total)
    print(count_of_cat_a)
    print(count_of_cat_b)
    categorycounts = counts_total
    return out

# New: parse CLI args and return structured values
def parse_args(argv):
    """Parse command line arguments.

    Expects at least: CategoryA CategoryB file1.vcf ...
    Optional: --out out.vcf to write matches to a file.

    Args:
        argv (list[str]): sys.argv[1:].

    Returns:
        tuple: (cat_a, cat_b, files, out_path)
    """
    if len(argv) < 3:
        print("Usage: vcard.py CategoryA CategoryB file1.vcf [file2.vcf ...] [--out out.vcf]")
        sys.exit(2)

    args = list(argv)
    out_path = None
    if "--out" in args:
        i = args.index("--out")
        if i == len(args) - 1:
            print("Provide output filename after --out")
            sys.exit(2)
        out_path = args[i+1]
        args = args[:i] + args[i+2:]

    cat_a = args[0].lower()
    cat_b = args[1].lower()
    files = args[2:]
    return cat_a, cat_b, files, out_path

# New: perform the file reading and vCard matching
def find_matching_vcards(cat_a, cat_b, files):
    """Scan files and find vCards that have cat_a but lack cat_b.

    Args:
        cat_a (str): Category name that must be present (lowercase).
        cat_b (str): Category name that must be absent (lowercase).
        files (list[str]): Paths to vCard files.

    Returns:
        tuple: (matches, total_vcards, matched_count)
            matches: list of matching vCard strings
            total_vcards: total number scanned
            matched_count: number of matches found
    """
    matches = []
    total_vcards = 0
    matched_count = 0

    for p in files:
        p = Path(p)
        if not p.exists():
            logging.warning("%s not found, skipping", p)
            continue
        # read using robust utf-8 conversion helper
        text = read_file_as_utf8(p)
        for vcard in iter_vcards(text):
            total_vcards += 1
            cats = categories_from_vcard(vcard)
            if (cat_a in cats) and (cat_b not in cats):
                matches.append(vcard)
                matched_count += 1

    return matches, total_vcards, matched_count

def print_usage():
    print("Usage:")
    print("  python vcard.py categorydiff CategoryA CategoryB file1.vcf [file2.vcf ...] [--out out.vcf]")

def build_parser():
    """Construct and return the top-level argparse.ArgumentParser for this CLI."""
    parser = argparse.ArgumentParser(prog="vcard.py", description="vCard utilities")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # categorydiff subcommand
    p_diff = subparsers.add_parser("categorydiff", help="Output vCards that have CategoryA but not CategoryB")
    p_diff.add_argument("category_a")
    p_diff.add_argument("category_b")
    p_diff.add_argument("files", nargs="+", help="One or more .vcf files")
    p_diff.add_argument("--out", "-o", dest="out", help="Write matches to file (default stdout)")

    # categorycontacts subcommand
    p_contacts = subparsers.add_parser("categorycontacts", help="Output vCards that have the specified category(ies)")
    p_contacts.add_argument("category", nargs="+", help="One or more category names (comma/semicolon allowed in a single argument)")
    p_contacts.add_argument("files", nargs="+", help="One or more .vcf files")
    p_contacts.add_argument("--out", "-o", dest="out", help="Write matches to file (default stdout)")

    # categorycounts subcommand
    p_counts = subparsers.add_parser("categorycounts", help="Compute/print category occurrence counts")
    p_counts.add_argument("files", nargs="*", help="Optional .vcf files to compute counts from")
    p_counts.add_argument("--out", "-o", dest="out", help="Write counts to file (default stdout)")

    return parser

def main(argv=None):
    """Main entrypoint: parse args (via build_parser) and dispatch commands."""
    if argv is None:
        argv = sys.argv[1:]

    logging.basicConfig(format="%(levelname)s: %(message)s")

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "categorydiff":
        category_a = args.category_a
        category_b = args.category_b
        input_files = args.files
        result_cards = categorydiff(category_a, category_b, input_files)
        output = ("\n".join(result_cards) + ("\n" if result_cards else ""))
        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)

    elif args.command == "categorycontacts":
        # produce vCards that include the requested category
        matches = categorycontacts(args.category, args.files)
        output = ("\n".join(matches) + ("\n" if matches else ""))
        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)

    elif args.command == "categorycounts":
        # If files provided, compute counts
        if args.files:
            categorycounts(args.files)

        # If still no counts, print help hint to stderr
        if not categorycounts:
            logging.info("No category counts available. Provide vCard files to compute counts.")
            parser.exit(0)

        # Output counts
        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                categorycounts(output=fh)

if __name__ == "__main__":
    main()
