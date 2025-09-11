# CSV Contacts Normalizer

Python utility to normalize contact data stored in CSV files.

## Features

* Input CSV format: `id;phone;dob`
* Normalization:
  * **Phone numbers** → strict E.164 (`+971501234567`)
    * minimal autocorrections: replace obvious typos like `o → 0`
    * UAE-specific heuristics supported (e.g. local numbers without country code)
  * **Dates of birth** → ISO 8601 (`YYYY-MM-DD`)
    * two-digit years interpreted with **pivot 25**: `00–25 → 2000–2025`, `26–99 → 1900–1999`
    * ambiguous numeric dates → **day-first**, unless the middle token > 12 (then month-first)
* Invalid rows are **skipped**, reasons printed in the summary  
  *(design choice: better skip than distort)*
* Streaming (row-by-row) processing → low memory usage, scalable for large files
* Docker support for reproducible runs
* Local run supported via `requirements.txt`

## Installation

### Local (without Docker)
```bash
  pip3 install -r requirements.txt
  python3 normalize_contacts.py tests/input.csv
```
Output will be written to `tests/normalized_contacts.csv`.

### Docker
Build image:
```bash
  docker build -t csv-contacts-normalizer .
```
Run (explicit input path):
```bash
  docker run --rm -v "$PWD":/data csv-contacts-normalizer /data/tests/input.csv
```
Output will be written to `tests/normalized_contacts.csv`.

## Example

Input (`tests/input.csv`):
```csv
id;phone;dob
U001;058_510_8603;Apr-05-2004
U002;0380 67 123 45 67;2001-09-09
```

Output (`tests/normalized_contacts.csv`):
```csv
id;phone;dob
U001;+971585108603;2004-04-05
```

Console summary:
```
Processed: 2
Normalized: 1
Skipped: 1
First issues:
- U002: invalid phone: 0380 67 123 45 67 -> 0380671234567
```

## Notes
* Two-digit years use **pivot 25**: `00–25 → 2000–2025`, otherwise → `1900–1999`.
* Ambiguous numeric dates (like `01/02/1990`) are treated as **day-first**, unless the month token > 12.
* Impossible dates (e.g. `29 Feb 1929`) are skipped, not corrected.
* Phone normalization uses [phonenumbers](https://github.com/daviddrysdale/python-phonenumbers) for strict validation.
* Policy: skip invalid or dubious rows instead of guessing aggressively