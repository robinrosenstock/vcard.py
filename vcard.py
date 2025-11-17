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
        if search_terms:
            filtered = []
            for card in matches:
                contact_name = get_name(card)
                if contact_name and any(term in contact_name.lower() for term in search_terms):
                    filtered.append(card)
            matches = filtered

        if args.name or args.number:
            lines = []
            for card in matches:
                cols = []
                if args.name:
                    cols.append(get_name(card))
                if args.number:
                    nums = get_numbers(card)
                    cols.append(";".join(nums) if nums else "")
                lines.append("\t".join(cols))
            output = ("\n".join(lines) + ("\n" if lines else ""))
        else:
            output = ("\n".join(matches) + ("\n" if matches else ""))

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


if __name__ == "__main__":
    main()
