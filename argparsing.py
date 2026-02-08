#!/usr/bin/env python3
import argparse

__version__ = "0.1.0"

def parse_args(argv):
    """Legacy simple parser helper (keeps older behavior)."""
    if len(argv) < 3:
        print("Usage: vcard.py CategoryA CategoryB file1.vcf [file2.vcf ...] [--out out.vcf]")
        raise SystemExit(2)

    args = list(argv)
    out_path = None
    if "--out" in args:
        i = args.index("--out")
        if i == len(args) - 1:
            print("Provide output filename after --out")
            raise SystemExit(2)
        out_path = args[i+1]
        args = args[:i] + args[i+2:]

    cat_a = args[0].lower()
    cat_b = args[1].lower()
    files = args[2:]
    return cat_a, cat_b, files, out_path

def build_parser():
    """Construct and return the top-level argparse.ArgumentParser for this CLI."""
    parser = argparse.ArgumentParser(prog="vcard.py", description="vCard utilities")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_contacts = subparsers.add_parser("get-contacts", help="Output vCards that match the specified category(ies)")
    p_contacts.add_argument("files", nargs="+", help="One or more .vcf files")
    p_contacts.add_argument("--has", dest="must_have", action="append", default=[], help="Require contacts to have these category names (comma/semicolon allowed per value)")
    p_contacts.add_argument("--not", dest="exclude", action="append", default=[], help="Exclude contacts containing these category names (comma/semicolon allowed per value)")
    p_contacts.add_argument("--name", action="store_true", dest="name", help="Output only the contact name(s) instead of full vCard")
    p_contacts.add_argument("--number", action="store_true", dest="number", help="Output only telephone number(s) instead of full vCard")
    p_contacts.add_argument("--category", action="store_true", dest="show_categories", help="Output the contact categories")
    p_contacts.add_argument("--searchname", action="append", dest="searchname", default=[], help="Filter contacts whose name contains these fragments (repeat or comma-separate)")
    p_contacts.add_argument("--out", "-o", dest="out", help="Write matches to file (default stdout)")

    p_counts = subparsers.add_parser("count-categories", help="Compute/print category occurrence counts")
    p_counts.add_argument("files", nargs="*", help="Optional .vcf files to compute counts from")
    p_counts.add_argument("--out", "-o", dest="out", help="Write counts to file (default stdout)")

    p_delete = subparsers.add_parser("delete-contacts", help="Delete vCards whose names appear in a file or args")
    p_delete.add_argument("vcf_file", help="Input .vcf file to update")
    p_delete.add_argument("names", nargs="*", help="Contact name(s) to delete")
    p_delete.add_argument("--namefile", dest="namefile", help="Text file with one contact name per line")
    p_delete.add_argument("--keep", dest="keep", action="append", default=[],
                          choices=["name", "number", "photo", "category"],
                          help="For matching names, keep only the specified fields")
    p_delete.add_argument("--out", "-o", dest="out", help="Write updated vCards to file (default overwrites input)")

    return parser
