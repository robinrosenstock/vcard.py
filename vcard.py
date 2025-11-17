#!/usr/bin/env python3
import sys
import logging
from pathlib import Path

# Try package-style imports first (when installed or run as package),
# fall back to local imports when running from repo root as script.
try:
    from vcard.argparsing import build_parser
    from vcard.functions import (
        categorycounts,
        categorycontacts,
        categorycontacts_all,
        categorydiff,
        get_name,
        get_numbers,
    )
except Exception:
    from argparsing import build_parser
    from functions import (
        categorycounts,
        categorycontacts,
        categorycontacts_all,
        categorydiff,
        get_name,
        get_numbers,
    )

__version__ = "0.1.0"

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
        matches = categorycontacts(args.category, args.files)
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

    elif args.command == "categorycontacts_all":
        matches = categorycontacts_all(args.category, args.files)
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

    elif args.command == "categorycounts":
        counts = categorycounts(args.files if args.files else None)
        if not counts:
            logging.info("No category counts available. Provide vCard files to compute counts.")
            parser.exit(0)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                categorycounts(output=fh)

if __name__ == "__main__":
    main()
