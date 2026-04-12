"""
test_vcard.py

Purpose:
    Unit tests updated to exercise the categorydiff-oriented API in vcard.py.

How to run:
    From the repository root run:
        pytest -q
"""

import importlib.util
from pathlib import Path
import sys

import pytest

# Load the module from the exact file path so tests exercise the provided file.
def load_module():
    fp = Path("./vcard.py")
    spec = importlib.util.spec_from_file_location("vcard", str(fp))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_read_vcards_and_get_categories(tmp_path):
    mod = load_module()
    # create a single file containing two vCards (one CRLF, one LF)
    f = tmp_path / "cards.vcf"
    v1 = "\r\n".join([
        "BEGIN:VCARD",
        "VERSION:3.0",
        "FN:Alice",
        "CATEGORIES:Friends,Work",
        "END:VCARD",
    ]) + "\r\n"
    v2 = "\n".join([
        "BEGIN:VCARD",
        "VERSION:3.0",
        "FN:Bob",
        "CATEGORIES:Work",
        "END:VCARD",
    ]) + "\n"
    f.write_text(v1 + v2, encoding="utf-8")

    cards = mod.read_vcards([str(f)])
    assert len(cards) == 2
    assert any("FN:Alice" in c for c in cards)
    assert any("FN:Bob" in c for c in cards)

    # get_categories may return original-case items; compare lowercased sets
    cats1 = {c.lower() for c in mod.get_categories(cards[0])}
    assert {"friends", "work"} <= cats1

    cats2 = {c.lower() for c in mod.get_categories(cards[1])}
    assert cats2 == {"work"}

def test_categorydiff_matching(tmp_path):
    mod = load_module()
    # create two files: one with both categories, one with only the first
    f1 = tmp_path / "a.vcf"
    f2 = tmp_path / "b.vcf"
    f1.write_text("\n".join([
        "BEGIN:VCARD",
        "VERSION:3.0",
        "FN:Alice",
        "CATEGORIES:Friends,Work",
        "END:VCARD",
    ]) + "\n", encoding="utf-8")
    f2.write_text("\n".join([
        "BEGIN:VCARD",
        "VERSION:3.0",
        "FN:Bob",
        "CATEGORIES:Work",
        "END:VCARD",
    ]) + "\n", encoding="utf-8")

    # Expect vCards that have 'work' but not 'friends' -> only Bob
    matches = mod.categorydiff("work", "friends", [str(f1), str(f2)])
    assert len(matches) == 1
    assert "FN:Bob" in matches[0]

def test_main_writes_output(tmp_path):
    mod = load_module()
    f1 = tmp_path / "a.vcf"
    f2 = tmp_path / "b.vcf"
    f1.write_text("\n".join([
        "BEGIN:VCARD",
        "VERSION:3.0",
        "FN:Alice",
        "CATEGORIES:Friends,Work",
        "END:VCARD",
    ]) + "\n", encoding="utf-8")
    f2.write_text("\n".join([
        "BEGIN:VCARD",
        "VERSION:3.0",
        "FN:Bob",
        "CATEGORIES:Work",
        "END:VCARD",
    ]) + "\n", encoding="utf-8")

    out_file = tmp_path / "out.vcf"
    old_argv = sys.argv[:]
    try:
        sys.argv = [str(Path("./vcard.py")), "categorydiff", "Work", "Friends", str(f1), str(f2), "--out", str(out_file)]
        # calling main should write the matching vCards to out_file
        mod.main()
    finally:
        sys.argv = old_argv

    content = out_file.read_text(encoding="utf-8")
    assert "FN:Bob" in content
    # the implementation appends a trailing newline when writing matches
    assert content.endswith("\n")
