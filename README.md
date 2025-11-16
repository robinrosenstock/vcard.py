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

## Category diff

```bash
# stdout will contain the matching vCards unless `--out` is provided.
python vcard.py categorydiff CategoryA CategoryB file1.vcf [file2.vcf ...] [--out out.vcf]
```

## Category counts

```bash
# Print category occurrence counts (to stdout by default).
python vcard.py categorycounts file1.vcf [file2.vcf ...]

# Or write counts to a file:
python vcard.py categorycounts file1.vcf [file2.vcf ...] --out counts.txt
```

Note: If no files are provided, the command will print a brief usage hint describing how to supply vCard files.

# Run tests

```bash
pytest -q
```
