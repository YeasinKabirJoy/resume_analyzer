import re
from datetime import datetime


DATE_FORMATS = [
    "%b %Y",
    "%b-%Y",
    "%b %y",
    "%b-%y",
    "%B %Y",
    "%Y",
]


def calculate_total_experience(experiences):
    total_months = 0
    experience_years = []

    for exp in experiences or []:
        start = parse_date(exp.get("start", ""))
        end_value = exp.get("end", "")
        end = datetime.now() if str(end_value).strip().lower() == "present" else parse_date(end_value)

        if not start or not end:
            experience_years.append(0.0)
            continue

        months = max((end.year - start.year) * 12 + (end.month - start.month) + 1, 0)
        experience_years.append(round(months / 12, 2))
        total_months += months

    total_years = total_months / 12
    return round(total_years, 2), experience_years


def parse_date(value: str):
    normalized = normalize_date_text(value)
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(normalized, fmt)
            if fmt == "%Y":
                return parsed.replace(month=1)
            return parsed
        except ValueError:
            continue
    return None


def normalize_date_text(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return ""
    text = text.replace(" - ", " ").replace("-", " ")
    parts = text.split()
    if len(parts) == 2 and len(parts[1]) == 2 and parts[1].isdigit():
        parts[1] = f"20{parts[1]}"
    return " ".join(parts)
