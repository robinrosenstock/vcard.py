#!/usr/bin/env python3
import sys
import logging
from pathlib import Path

# direct imports of top-level modules (installed as py_modules or present locally)
from argparsing import build_parser
from utils import (
    count_categories,
    categorycontacts,
    get_name,
    get_numbers,
    get_categories,
    delete_vcards_by_name,
)

def main(argv=None):
    """Main entrypoint: parse args (via build_parser) and dispatch commands."""
    if argv is None:
        argv = sys.argv[1:]

    logging.basicConfig(format="%(levelname)s: %(message)s")

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "get-contacts":
        matches = categorycontacts(
            categories=None,
            files=args.files,
            must_have=args.must_have,
            exclude=args.exclude,
        )
        # apply optional name filtering
        search_terms = [
            term.strip().lower()
            for raw in (args.searchname or [])
            for term in raw.split(",")
            if term.strip()
        ]
        namefile_terms = []
        if args.namefile:
            namefile_terms = [
                line.strip().lower()
                for line in Path(args.namefile).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        if namefile_terms:
            allowed = set(namefile_terms)
            filtered = []
            for card in matches:
                contact_name = get_name(card).strip().lower()
                if contact_name and contact_name in allowed:
                    filtered.append(card)
            matches = filtered
        if search_terms:
            filtered = []
            for card in matches:
                contact_name = get_name(card)
                if contact_name and any(term in contact_name.lower() for term in search_terms):
                    filtered.append(card)
            matches = filtered

        if args.name or args.number or args.show_categories:
            rows = []
            for card in matches:
                rows.append({
                    "name": get_name(card) if args.name else "",
                    "number": ";".join(get_numbers(card)) if args.number else "",
                    "category": ";".join(get_categories(card)) if args.show_categories else "",
                })
            columns = []
            if args.name:
                columns.append("name")
            if args.number:
                columns.append("number")
            if args.show_categories:
                columns.append("category")
            widths = {
                col: max((len(row[col]) for row in rows), default=0)
                for col in columns[:-1]
            }
            lines = []
            for row in rows:
                parts = []
                for idx, col in enumerate(columns):
                    val = row[col]
                    if idx < len(columns) - 1:
                        parts.append(val.ljust(widths.get(col, 0)))
                    else:
                        parts.append(val)
                lines.append("  ".join(part for part in parts if part))
            output = ("\n".join(lines) + ("\n" if lines else ""))
        else:
            output = ("\n".join(matches) + ("\n" if matches else ""))

        total_line = f"Total contacts: {len(matches)}\n"
        output = output + total_line

        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)

    elif args.command == "count-categories":
        counts = count_categories(args.files if args.files else None)
        if not counts:
            logging.info("No category counts available. Provide vCard files to compute counts.")
            parser.exit(0)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                count_categories(output=fh)

    elif args.command == "delete-contacts":
        if not args.names and not args.namefile:
            parser.error("delete-contacts requires at least one name or --namefile")
        deleted = delete_vcards_by_name(
            args.vcf_file,
            names=args.names,
            out_file=args.out,
            names_file=args.namefile,
            keep_fields=args.keep,
        )
        if args.out:
            logging.info("Deleted %d contacts; wrote updated vCards to %s", deleted, args.out)
        else:
            logging.info("Deleted %d contacts; updated %s", deleted, args.vcf_file)


if __name__ == "__main__":
    main()
