#!/usr/bin/env python3
import sys
import re
from typing import List
from pathlib import Path

"""vcard.py

Utilities to scan vCard (.vcf) files and extract cards that belong to one
category but not another.

Usage:
    vcard.py CategoryA CategoryB file1.vcf [file2.vcf ...] [--out out.vcf]

Behavior:
- Reads one or more vCard files, preserves vCard folding rules when parsing.
- Selects vCards that list CategoryA in their CATEGORIES: property but do not
  list CategoryB.
- Writes matching vCards to stdout by default or to --out <file> if provided.
- Prints a short summary to stderr so stdout remains a pure vCard stream.

Notes:
- Category matching is case-insensitive.
- Folded lines (a newline followed by space or tab) are unfolded before parsing.
"""

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

def read_vcards(files: List[str]) -> List[str]:
    """Read vCard blocks from files (BEGIN:VCARD ... END:VCARD)."""
    cards = []
    buf = []
    for path in files:
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.rstrip("\n")
                if line.upper().startswith("BEGIN:VCARD"):
                    buf = [line]
                elif line.upper().startswith("END:VCARD"):
                    buf.append(line)
                    cards.append("\n".join(buf))
                    buf = []
                else:
                    if buf:
                        buf.append(line)
    # In case a file ends without END:VCARD, ignore incomplete block.
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

def categorydiff(cat_a: str, cat_b: str, files: List[str]) -> List[str]:
    """Return vCard blocks that have cat_a but not cat_b."""
    cards = read_vcards(files)
    out = []
    la = cat_a.lower()
    lb = cat_b.lower()
    for card in cards:
        cats = [c.lower() for c in get_categories(card)]
        if la in cats and lb not in cats:
            out.append(card)
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
            print(f"Warning: {p} not found, skipping", file=sys.stderr)
            continue
        text = p.read_text(encoding='utf-8', errors='replace')
        for vcard in iter_vcards(text):
            total_vcards += 1
            cats = categories_from_vcard(vcard)
            if (cat_a in cats) and (cat_b not in cats):
                matches.append(vcard)
                matched_count += 1

    return matches, total_vcards, matched_count

# New: write matches to stdout or file
def write_matches(matches, out_path):
    """Output matching vCards to stdout or file.

    Args:
        matches (list[str]): Matching vCard strings.
        out_path (str|None): If provided, path to write output file.
    """
    out_text = "\n".join(matches) + ("\n" if matches else "")
    if out_path:
        Path(out_path).write_text(out_text, encoding='utf-8')
    else:
        sys.stdout.write(out_text)

def print_usage():
    print("Usage:")
    print("  python vcard.py categorydiff CategoryA CategoryB file1.vcf [file2.vcf ...] [--out out.vcf]")

def main():
    """Main entrypoint that coordinates argument parsing, matching and output.

    The function delegates all work to smaller functions so it only orchestrates
    the high-level flow.
    """
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    func = sys.argv[1].lower()
    args = sys.argv[2:]

    # Optional --out output file (can appear anywhere in args)
    out_path = None
    if "--out" in args:
        i = args.index("--out")
        if i + 1 >= len(args):
            print("Error: --out requires a filename")
            sys.exit(2)
        out_path = args[i + 1]
        # remove the option and its value
        del args[i:i+2]

    if func == "categorydiff":
        if len(args) < 3:
            print_usage()
            sys.exit(1)
        category_a = args[0]
        category_b = args[1]
        input_files = args[2:]
        result_cards = categorydiff(category_a, category_b, input_files)
        output = ("\n".join(result_cards) + ("\n" if result_cards else ""))
        if out_path:
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(output)
        else:
            sys.stdout.write(output)
    else:
        cat_a, cat_b, files, out_path = parse_args(sys.argv[1:])
        matches, total_vcards, matched_count = find_matching_vcards(cat_a, cat_b, files)
        write_matches(matches, out_path)

        # Summary printed to stderr so stdout remains the vcard stream
        print(f"Processed vcards: {total_vcards}", file=sys.stderr)
        print(f"vcards with '{cat_a}': {matched_count}", file=sys.stderr)
        print(f"Matches (has '{cat_a}', lacks '{cat_b}'): {matched_count}", file=sys.stderr)

if __name__ == "__main__":
    main()
