import csv
import os
import sys
import re
from datetime import date
from typing import Tuple, Optional


import phonenumbers
from dateutil import parser as dparser


# Replacements for frequent errors: 'o' → '0'
# cause sometimes users can miss when they type.
_ALNUM_MAP = str.maketrans({
    'o': '0', 'O': '0',
})

# DATE OF BIRTH

def _pivot_year(y2: int) -> int:
    # Pivot rule: Twodigit years → 00–25 → 2000–2025, otherwise → 1900–1999
    return 2000 + y2 if 0 <= y2 <= 25 else 1900 + y2

def _fmt_date(y: int, m: int, d: int) -> Tuple[Optional[str], Optional[str]]:
    try:
        return date(int(y), int(m), int(d)).isoformat(), None
    except Exception:
        return None, f'invalid date components y={y} m={m} d={d}'

# PHONE

def _sanitize_phone(raw: str) -> str:
    s = (raw or "").strip()
    s = s.replace("(0)", "")
    s = s.translate(_ALNUM_MAP)

    kept = [ch for ch in s if ch.isdigit() or ch == '+']
    s = ''.join(kept)

    # 00… → +…
    if s.startswith('00'):
        s = '+' + s[2:]

    # remove unnecessary "+", leave only a leading
    if s.count('+') > 1:
        s = '+' + s.replace('+', '')

    return s


# Parsing for phone numbers
def normalize_phone(raw: str) -> Tuple[Optional[str], Optional[str]]:
    """We normalize the phone in E.164. If dubious → miss."""
    original = raw
    s = _sanitize_phone(raw)

    def _format_if_ok(num_str: str, region: Optional[str]) -> Optional[str]:
        try:
            pn = phonenumbers.parse(num_str, region)
            if phonenumbers.is_possible_number(pn) and phonenumbers.is_valid_number(pn):
                return phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            return None
        return None

    if s.startswith('+'):
        out = _format_if_ok(s, None)
        if out:
            return out, None

    if not s.startswith('+') and s.startswith('971'):
        out = _format_if_ok('+' + s, None)
        if out:
            return out, None

    # 3) Only for UAE so how our parser focused in this area
    if not s.startswith('+'):
        # 0XXXXXXXXX → +971XXXXXXXX
        if s.startswith('0') and len(s) > 1:
            trial = '+971' + s[1:]
            out = _format_if_ok(trial, None)
            if out:
                return out, None
        # if 9 digits, starts at 5 (mobile without 0)
        if re.fullmatch(r'5\d{8}', s):
            trial = '+971' + s
            out = _format_if_ok(trial, None)
            if out:
                return out, None
        # Generas cases, but again only for UAE
        out = _format_if_ok(s, 'AE')
        if out:
            return out, None

    # 4) This is very rare but happening case: 00…
    if s.startswith('00'):
        out = _format_if_ok('+' + s[2:], None)
        if out:
            return out, None

    # Otherwise, just skip it
    return None, f'invalid phone: {original} -> {s}'


# Parsing for date of birth to YYYY-MM-DD, otherwise skip

_NUM_RE = re.compile(r'\d+')
_ONLY_8_DIGITS_RE = re.compile(r'^\d{8}$')
_HAS_ALPHA_RE = re.compile(r'[A-Za-z]')

def normalize_dob(raw: str) -> Tuple[Optional[str], Optional[str]]:
    s = (raw or "").strip()
    original = s
    if not s:
        return None, 'empty dob'

    # YYYYMMDD without separators
    if _ONLY_8_DIGITS_RE.fullmatch(s):
        y, m, d = int(s[0:4]), int(s[4:6]), int(s[6:8])
        return _fmt_date(y, m, d)

    tokens = [int(t) for t in _NUM_RE.findall(s)]
    has_alpha = _HAS_ALPHA_RE.search(s) is not None

    # Dates with text months (for example: "25 Dec 90", "March 5, 2020" and so on)
    if has_alpha:
        two_digs = list(re.finditer(r'(?<!\d)(\d{2})(?!\d)', s))
        y_override = None
        if two_digs:
            y2 = int(two_digs[-1].group(1))
            y_override = _pivot_year(y2)
        try:
            dt = dparser.parse(s, dayfirst=True, yearfirst=False, fuzzy=True)
            y = y_override if (y_override is not None and dt.year < 100) else (y_override or dt.year)
            return _fmt_date(int(y), dt.month, dt.day)
        except Exception:
            return None, f'invalid date: {original}'

    # Only numerical formats
    if len(tokens) == 3:
        a, b, c = tokens
        # YYYY-MM-DD
        if len(str(a)) == 4:
            return _fmt_date(a, b, c)
        # DD-MM-YYYY or MM-DD-YYYY
        if len(str(c)) == 4:
            y = c
            if b > 12 and a <= 12:
                m, d = a, b  # MM/DD/YYYY
            else:
                d, m = a, b  # DD/MM/YYYY
            return _fmt_date(y, m, d)
        # DD-MM-YY (Twodigit year)
        if len(str(c)) == 2:
            y = _pivot_year(c)
            if b > 12 and a <= 12:
                m, d = a, b
            else:
                d, m = a, b
            return _fmt_date(y, m, d)

    # Last attempt: General Parser
    try:
        dt = dparser.parse(s, dayfirst=True, yearfirst=False, fuzzy=True)
        return dt.date().isoformat(), None
    except Exception:
        return None, f'invalid date: {original}'


def main():
    in_path = sys.argv[1] if len(sys.argv) > 1 else "tests/input.csv"
    out_dir = os.path.dirname(in_path)
    out_path = os.path.join(out_dir, "normalized_contacts.csv")

    total = 0
    written = 0
    skipped = []

    with open(in_path, newline="", encoding="utf-8") as fin, \
         open(out_path, "w", newline="", encoding="utf-8") as fout:
        reader = csv.DictReader(fin, delimiter=";")
        writer = csv.DictWriter(fout, fieldnames=["id", "phone", "dob"], delimiter=";")
        writer.writeheader()

        for row in reader:
            total += 1
            rid = row.get("id", "").strip()

            phone, perr = normalize_phone(row.get("phone", ""))
            dob, derr = normalize_dob(row.get("dob", ""))

            if phone and dob:
                writer.writerow({"id": rid, "phone": phone, "dob": dob})
                written += 1
            else:
                reasons = []
                if perr: reasons.append(perr)
                if derr: reasons.append(derr)
                skipped.append((rid or f"#row{total}", "; ".join(reasons)))


    print("Processed:", total)
    print("Normalized:", written)
    print("Skipped:", len(skipped))
    if skipped:
        print("First issues:")
        for rid, reason in skipped[:10]:
            print(f"- {rid}: {reason}")

if __name__ == "__main__":
    main()