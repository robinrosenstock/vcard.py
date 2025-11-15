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
python vcard.py CategoryA CategoryB file1.vcf [file2.vcf ...] [--out out.vcf]
```

# Run tests

```bash
pytest -q
```
