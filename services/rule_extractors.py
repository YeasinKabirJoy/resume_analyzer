import re
from collections import OrderedDict
from datetime import datetime

from .normalizer import normalize_for_match, normalize_whitespace, title_case_name

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+", re.IGNORECASE)
GITHUB_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_.-]+)", re.IGNORECASE)
LINKEDIN_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub)/([A-Za-z0-9_.-]+)",
    re.IGNORECASE,
)
SECTION_HEADERS = OrderedDict(
    [
        ("summary", ["summary", "profile", "professional summary", "objective"]),
        ("experience", ["experience", "experiences", "work experience", "professional experience", "employment history"]),
        ("education", ["education", "academic background"]),
        ("skills", ["skills", "technical skills", "core skills", "core competencies", "technologies", "tools & technologies"]),
        ("projects", ["projects", "project experience"]),
        ("certifications", ["certifications", "certificates", "courses"]),
    ]
)
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
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}
DATE_RANGE_PATTERN = re.compile(
    r"(?P<start>(?:\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}\b|\b\d{4}\b))\s*"
    r"(?:-|–|—|to)\s*"
    r"(?P<end>(?:present|current|now|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}\b|\b\d{4}\b))",
    re.IGNORECASE,
)


def extract_contacts(text: str) -> dict:
    email_match = EMAIL_PATTERN.search(text or "")
    github_match = GITHUB_PATTERN.search(text or "")
    linkedin_match = LINKEDIN_PATTERN.search(text or "")

    return {
        "email": email_match.group(0) if email_match else "",
        "phone": extract_phone(text),
        "github": f"https://github.com/{github_match.group(1)}" if github_match else "",
        "linkedin": f"https://www.linkedin.com/in/{linkedin_match.group(1)}" if linkedin_match else "",
    }


def extract_phone(text: str) -> str:
    phone_pattern = re.compile(
        r"(?<!\d)(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)\d{3,4}[\s.-]?\d{4}(?!\d)"
    )
    match = phone_pattern.search(text or "")
    if not match:
        return ""
    return normalize_whitespace(match.group(0))


def extract_name(text: str, fallback_contacts: dict | None = None) -> str:
    lines = [normalize_whitespace(line) for line in (text or "").splitlines()]
    lines = [line for line in lines if line]
    excluded = {value.lower() for value in (fallback_contacts or {}).values() if value}
    blocked_words = {
        "resume",
        "cv",
        "curriculum vitae",
        "summary",
        "experience",
        "education",
        "skills",
        "developer",
        "engineer",
        "manager",
        "analyst",
        "software",
        "python",
        "java",
        "django",
        "react",
        "backend",
        "frontend",
        "full stack",
    }

    for line in lines[:12]:
        lowered = normalize_for_match(line)
        if line.lower() in excluded:
            continue
        if "@" in line or "http" in line.lower() or "www." in line.lower():
            continue
        if any(word in lowered for word in blocked_words):
            continue
        if _looks_like_name(line):
            return title_case_name(line)
    return ""


def extract_sections(text: str) -> dict:
    lines = [normalize_whitespace(line) for line in (text or "").splitlines()]
    section_hits: list[tuple[int, str]] = []

    for index, line in enumerate(lines):
        normalized = normalize_for_match(line)
        for section_name, headers in SECTION_HEADERS.items():
            if any(normalized == header for header in headers):
                section_hits.append((index, section_name))
                break

    if not section_hits:
        return {}

    section_hits = sorted(set(section_hits), key=lambda item: item[0])
    sections: dict[str, str] = {}

    for position, (start_index, section_name) in enumerate(section_hits):
        end_index = section_hits[position + 1][0] if position + 1 < len(section_hits) else len(lines)
        content = "\n".join(line for line in lines[start_index + 1 : end_index] if line)
        sections[section_name] = content.strip()

    return sections


def extract_experiences(text: str) -> list[dict]:
    sections = extract_sections(text)
    source_text = sections.get("experience") or text or ""
    lines = [normalize_whitespace(line) for line in source_text.splitlines()]
    experiences: list[dict] = []

    for index, line in enumerate(lines):
        date_range = parse_date_range(line)
        if not date_range:
            continue

        designation = ""
        company = ""

        for candidate in reversed(lines[max(0, index - 3) : index]):
            if not candidate or _looks_like_location(candidate) or parse_date_range(candidate):
                continue
            candidate_type = _classify_experience_line(candidate)
            if candidate_type == "company" and not company:
                company = candidate
                continue
            if candidate_type == "designation" and not designation:
                designation = candidate
                continue
            if not company:
                company = candidate
                continue
            if not designation:
                designation = candidate
                continue

        experiences.append(
            {
                "designation": designation,
                "company": company,
                "start": date_range["start"],
                "end": date_range["end"],
            }
        )

    return experiences


def parse_date_range(line: str) -> dict | None:
    match = DATE_RANGE_PATTERN.search(line or "")
    if not match:
        return None
    return {
        "start": normalize_date_token(match.group("start")),
        "end": normalize_date_token(match.group("end")),
    }


def normalize_date_token(value: str) -> str:
    normalized = normalize_whitespace(value)
    if not normalized:
        return ""
    if normalized.lower() in {"present", "current", "now"}:
        return "Present"
    if normalized.isdigit() and len(normalized) == 4:
        return f"Jan {normalized}"
    month_token, _, year_token = normalized.partition(" ")
    if month_token.isdigit() and not year_token:
        return f"Jan {month_token}"
    if month_token.isdigit() and year_token.isdigit():
        return f"Jan {month_token}"
    if year_token.isdigit():
        month_key = month_token.lower().rstrip(".")
        month_number = MONTH_NAMES.get(month_key)
        if month_number:
            month_name = datetime(2000, month_number, 1).strftime("%b")
            return f"{month_name} {year_token}"
    return normalized


def _looks_like_name(line: str) -> bool:
    tokens = line.split()
    if not (2 <= len(tokens) <= 4):
        return False
    if any(char.isdigit() for char in line):
        return False
    lowered = line.lower()
    blocked = {"resume", "cv", "curriculum vitae", "summary", "experience", "education", "skills"}
    if lowered in blocked:
        return False
    return all(
        token[:1].isalpha() and (token[:1].isupper() or token.isupper())
        for token in tokens
    )


def _looks_like_location(line: str) -> bool:
    lowered = normalize_for_match(line)
    return any(keyword in lowered for keyword in ["city", "state", "country", "india", "usa", "remote"])


def _classify_experience_line(line: str) -> str:
    lowered = normalize_for_match(line)
    designation_keywords = [
        "engineer",
        "developer",
        "analyst",
        "manager",
        "intern",
        "lead",
        "architect",
        "consultant",
        "specialist",
    ]
    company_keywords = [
        "inc",
        "llc",
        "ltd",
        "corp",
        "corporation",
        "company",
        "solutions",
        "systems",
        "technologies",
        "labs",
        "studio",
        "university",
        "institute",
    ]
    if any(keyword in lowered for keyword in designation_keywords):
        return "designation"
    if any(keyword in lowered for keyword in company_keywords):
        return "company"
    return "unknown"
