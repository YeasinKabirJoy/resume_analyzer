import re


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def normalize_for_match(value: str) -> str:
    normalized = normalize_whitespace(value).lower()
    normalized = re.sub(r"[^\w\s+#/.+-]", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def title_case_name(value: str) -> str:
    normalized = normalize_whitespace(value)
    if not normalized:
        return ""
    return " ".join(part.capitalize() for part in normalized.split())


def normalize_month_year(value: str) -> str:
    normalized = normalize_whitespace(value)
    return normalized[:1].upper() + normalized[1:] if normalized else ""

