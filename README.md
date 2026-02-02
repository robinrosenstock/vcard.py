# Install

```bash
python3 -m venv vcard
source vcard/bin/activate
# optional: upgrade pip
python -m pip install --upgrade pip
# Install requirements:
pip install -r requirements.txt
```

# Usage

## Get contacts

The `get-contacts` command filters contacts from one or more `.vcf` files.

- By default it prints the full matching vCard blocks.
- It always appends a summary line: `Total contacts: N`.
- Use `--has` / `--not` to include/exclude by category.
- Use `--name`, `--number`, `--category` to print selected fields instead of full vCards.

### Examples

```bash
# Print full matching vCards (plus a total line):
python vcard.py get-contacts files/all.vcf
```

```bash
# Require one or more categories (repeatable). Each value may contain comma/semicolon-separated names:
python vcard.py get-contacts files/all.vcf --has Friends --has "Work;VIP"
```

```bash
# Exclude contacts that have certain categories:
python vcard.py get-contacts files/all.vcf --not Work --not "Spam,Unknown"
```

```bash
# Combine filters and print just name + phone number (one line per contact):
python vcard.py get-contacts files/all.vcf --has Friends --name --number
```

```bash
# Also include categories in the output:
python vcard.py get-contacts files/all.vcf --has Friends --name --number --category
```

```bash
# Filter by partial name match (repeat or comma-separate fragments):
python vcard.py get-contacts files/all.vcf --searchname robin --searchname "alice,bob"
```

```bash
# Write output to a file (default is stdout):
python vcard.py get-contacts files/all.vcf --has Friends --name --number --out output/friends.txt
```

## Category diff

```bash
# stdout will contain the matching vCards unless `--out` is provided.
python vcard.py categorydiff CategoryA CategoryB file1.vcf [file2.vcf ...] [--out out.vcf]
```

## Category counts

```bash
# Print category occurrence counts (to stdout by default).
python vcard.py count-categories file1.vcf [file2.vcf ...]

# Or write counts to a file:
python vcard.py count-categories file1.vcf [file2.vcf ...] --out counts.txt
```

Note: If no files are provided, the command will print a brief usage hint describing how to supply vCard files.

# Run tests

```bash
pytest -q
```

# run as cli command vcard

Run the CLI command `vcard` from within a Python virtual environment.

1. Install package (editable during development):
   pip install -e .
2. Run:
   vcard --help

Notes
- `pip install -e .` registers the console script defined in pyproject.toml (`vcard = "vcard.vcard:main"`).
- To remove the script, run: `pip uninstall vcard` while the same venv is active.
- If you change entry points or setup, reinstall (`pip install -e .`) to update the script.
