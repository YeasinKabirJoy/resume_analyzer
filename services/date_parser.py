import re
from datetime import datetime

from .normalizer import normalize_whitespace

MONTH_NAMES = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "september": 9,
    "sept": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

MONTH_REGEX_STR = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*"

NAMED_MONTH_YEAR_PATTERN = re.compile(
    rf"\b(?P<month>{MONTH_REGEX_STR})[-\s]+(?P<year>\d{{2,4}})\b",
    re.IGNORECASE,
)
NUMERIC_SLASH_PATTERN = re.compile(
    r"\b(?:(?P<m1>0?[1-9]|1[0-2])[/-](?P<y1>\d{4})|(?P<y2>\d{4})[/-](?P<m2>0?[1-9]|1[0-2]))\b"
)
YEAR_PATTERN = re.compile(r"\b(?P<year>(?:19|20)\d{2})\b")
PRESENT_PATTERN = re.compile(r"\b(?P<present>present|current|now)\b", re.IGNORECASE)

DATE_TOKEN_PATTERN = re.compile(
    rf"\b(?:"
    rf"{MONTH_REGEX_STR}[-\s]+\d{{2,4}}"
    r"|"
    r"(?:0?[1-9]|1[0-2])[/-]\d{4}|\d{4}[/-](?:0?[1-9]|1[0-2])"
    r"|"
    r"(?:19|20)\d{2}"
    r"|"
    r"present|current|now"
    r")\b",
    re.IGNORECASE,
)

SEPARATOR_PATTERN = r"(?:\s*(?:-|–|—|\bto\b|\buntil\b|\bthrough\b)\s*)"

DATE_RANGE_PATTERN = re.compile(
    rf"(?P<start>"
    rf"\b{MONTH_REGEX_STR}[-\s]+\d{{2,4}}\b"
    r"|"
    r"\b(?:0?[1-9]|1[0-2])[/-]\d{4}\b|\b\d{4}[/-](?:0?[1-9]|1[0-2])\b"
    r"|"
    r"\b(?:19|20)\d{2}\b"
    rf")"
    rf"{SEPARATOR_PATTERN}"
    rf"(?P<end>"
    r"\b(?:present|current|now)\b"
    r"|"
    rf"\b{MONTH_REGEX_STR}[-\s]+\d{{2,4}}\b"
    r"|"
    r"\b(?:0?[1-9]|1[0-2])[/-]\d{4}\b|\b\d{4}[/-](?:0?[1-9]|1[0-2])\b"
    r"|"
    r"\b(?:19|20)\d{2}\b"
    rf")",
    re.IGNORECASE,
)

GRADUATION_PREFIX_PATTERN = re.compile(
    r"\b(?:expected(?:\s+graduation)?|graduating|graduated|class\s+of)\s*[:\-]?\s*",
    re.IGNORECASE,
)


def parse_date_token(value: str, default_month: str | None = None) -> tuple[str, str]:
    if not value:
        return "", ""
    cleaned = normalize_whitespace(value).strip("(),[]{}")
    if not cleaned:
        return "", ""

    if PRESENT_PATTERN.search(cleaned):
        return "Present", "present"

    num_match = NUMERIC_SLASH_PATTERN.search(cleaned)
    if num_match:
        m = num_match.group("m1") or num_match.group("m2")
        y = num_match.group("y1") or num_match.group("y2")
        month_name = datetime(2000, int(m), 1).strftime("%b")
        return f"{month_name} {y}", "month"

    named_match = NAMED_MONTH_YEAR_PATTERN.search(cleaned)
    if named_match:
        month_key = named_match.group("month").lower()
        year_str = named_match.group("year")
        if len(year_str) == 2:
            year_str = f"20{year_str}"
        month_number = MONTH_NAMES.get(month_key)
        if month_number:
            month_name = datetime(2000, month_number, 1).strftime("%b")
            return f"{month_name} {year_str}", "month"

    year_match = YEAR_PATTERN.search(cleaned)
    if year_match:
        year_str = year_match.group("year")
        if default_month:
            return f"{default_month} {year_str}", "year"
        return year_str, "year"

    return cleaned, "unknown"


def normalize_date_token(value: str) -> str:
    formatted, _ = parse_date_token(value, default_month="Jan")
    return formatted


def parse_date_range(line: str) -> dict | None:
    parsed = parse_date_expression(line, default_month="Jan")
    if not parsed or not parsed.get("start") or not parsed.get("end"):
        return None
    return {
        "start": parsed["start"],
        "end": parsed["end"],
    }


def parse_date_expression(line: str, default_month: str | None = None) -> dict | None:
    normalized = _normalize_date_line(line)
    if not normalized:
        return None

    range_match = DATE_RANGE_PATTERN.search(normalized)
    if range_match:
        start_str, start_prec = parse_date_token(range_match.group("start"), default_month=default_month)
        end_str, end_prec = parse_date_token(range_match.group("end"), default_month=default_month)
        precision = "month" if (start_prec == "month" or end_prec == "month") else "year"
        return {
            "start": start_str,
            "end": end_str,
            "raw": range_match.group(0),
            "precision": precision,
            "is_current": end_str.lower() == "present",
            "is_range": True,
        }

    prefix_match = GRADUATION_PREFIX_PATTERN.search(normalized)
    if prefix_match:
        after_prefix = normalized[prefix_match.end():].strip()
        date_str, prec = parse_date_token(after_prefix, default_month=default_month)
        if date_str:
            return {
                "start": None,
                "end": date_str,
                "raw": normalized[prefix_match.start():],
                "precision": prec,
                "is_current": False,
                "is_range": False,
                "is_expected": "expected" in prefix_match.group(0).lower(),
            }

    single_match = DATE_TOKEN_PATTERN.search(normalized)
    if single_match:
        date_str, prec = parse_date_token(single_match.group(0), default_month=default_month)
        if date_str:
            return {
                "start": None,
                "end": date_str,
                "raw": single_match.group(0),
                "precision": prec,
                "is_current": date_str.lower() == "present",
                "is_range": False,
            }

    return None


def is_date_anchor_line(line: str) -> bool:
    normalized = _normalize_date_line(line)
    if not normalized:
        return False
    if DATE_RANGE_PATTERN.search(normalized):
        return True
    if DATE_TOKEN_PATTERN.search(normalized):
        return True
    return bool(PRESENT_PATTERN.search(normalized))


def _normalize_date_line(value: str) -> str:
    text = normalize_whitespace(value)
    if not text:
        return ""
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text).strip()
    return text

