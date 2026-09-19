import re
from collections import OrderedDict
from datetime import datetime

from .date_parser import is_date_anchor_line, normalize_date_token, parse_date_expression, parse_date_range
from .normalizer import normalize_for_match, normalize_whitespace, title_case_name

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+", re.IGNORECASE)
GITHUB_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_.-]+)", re.IGNORECASE)
LINKEDIN_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub)/([A-Za-z0-9_.-]+)", re.IGNORECASE)
SECTION_HEADERS = OrderedDict(
    [
        ("summary", ["summary", "profile", "professional summary", "objective"]),
        ("experience", ["experience", "experiences", "work experience", "professional experience", "employment history"]),
        ("education", ["education", "academic background", "educational background"]),
        ("skills", ["skills", "technical skills", "core skills", "core competencies", "technologies", "tools & technologies"]),
        ("projects", ["projects", "project experience"]),
        ("certifications", ["certifications", "certificates", "courses"]),
    ]
)

DEGREE_KEYWORDS = [
    "bsc",
    "b.sc",
    "bachelor",
    "bachelors",
    "msc",
    "m.sc",
    "master",
    "masters",
    "phd",
    "ph.d",
    "doctorate",
    "diploma",
    "hsc",
    "ssc",
    "higher secondary certificate",
    "secondary school certificate",
    "o level",
    "a level",
    "bba",
    "mba",
    "btech",
    "b.tech",
    "mtech",
    "m.tech",
    "b.e.",
    "m.e.",
    "bcom",
    "b.com",
    "ba",
    "b.a.",
    "ma",
    "m.a.",
    "undergraduate",
    "postgraduate",
    "post graduate",
    "associate degree",
    "certificate",
]

INSTITUTION_KEYWORDS = [
    "university",
    "college",
    "school",
    "academy",
    "institute",
    "polytechnic",
    "campus",
    "faculty",
    "vidyalaya",
    "madrasah",
]

DESIGNATION_KEYWORDS = [
    "engineer",
    "developer",
    "analyst",
    "manager",
    "intern",
    "lead",
    "architect",
    "consultant",
    "specialist",
    "programmer",
    "administrator",
    "designer",
    "officer",
    "director",
]

COMPANY_KEYWORDS = [
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
    "group",
    "consulting",
    "services",
]

DESCRIPTION_START_VERBS = {
    "conducted",
    "engineered",
    "built",
    "developed",
    "worked",
    "led",
    "using",
    "handled",
    "designed",
    "implemented",
    "created",
    "managed",
    "delivered",
    "maintained",
    "supported",
    "improved",
    "optimized",
    "streamlined",
    "collaborated",
    "owned",
    "expanded",
}


def extract_contacts(text: str) -> dict:
    lines = [normalize_whitespace(line) for line in (text or "").splitlines()]
    email_match = select_best_email(lines)
    github_match = GITHUB_PATTERN.search(text or "")
    linkedin_match = LINKEDIN_PATTERN.search(text or "")

    return {
        "email": email_match or "",
        "phone": extract_phone(text),
        "github": f"https://github.com/{github_match.group(1)}" if github_match else "",
        "linkedin": f"https://www.linkedin.com/in/{linkedin_match.group(1)}" if linkedin_match else "",
    }


def extract_phone(text: str) -> str:
    phone_pattern = re.compile(r"(?<!\d)(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)\d{3,4}[\s.-]?\d{4}(?!\d)")
    match = phone_pattern.search(text or "")
    if not match:
        return ""
    return normalize_whitespace(match.group(0))


def select_best_email(lines: list[str]) -> str:
    candidates = []
    in_reference_block = False

    for index, line in enumerate(lines):
        lowered = normalize_for_match(line)
        if lowered in {"reference", "references"}:
            in_reference_block = True
            continue
        for match in EMAIL_PATTERN.finditer(line):
            score = 1000 - index
            if index <= 8:
                score += 200
            if in_reference_block:
                score -= 500
            if any(keyword in lowered for keyword in ["summary", "experience", "education", "skills"]):
                score -= 25
            candidates.append((score, index, match.group(0)))

    if not candidates:
        fallback = EMAIL_PATTERN.search("\n".join(lines))
        return fallback.group(0) if fallback else ""

    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][2]


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


# ==============================================================================
# EDUCATION EXTRACTION (Block-Based & Segment-Based)
# ==============================================================================

def extract_educations(text: str) -> list[dict]:
    sections = extract_sections(text)
    education_text = sections.get("education") or text or ""
    raw_lines = [normalize_whitespace(line) for line in education_text.splitlines()]
    lines = [line for line in raw_lines if line and not _is_section_header(line)]

    if not lines:
        return []

    records: list[dict] = []
    current_record: dict | None = None

    for line in lines:
        parsed_segments = _parse_education_line(line)

        # Determine if this line starts a new record
        has_degree = bool(parsed_segments.get("degree"))
        has_institution = bool(parsed_segments.get("institution"))
        is_standalone = has_degree and has_institution

        start_new = False
        if is_standalone:
            start_new = True
        elif current_record:
            if has_degree and current_record.get("degree"):
                start_new = True
            elif has_institution and current_record.get("institution") and not current_record.get("degree") and not has_degree:
                start_new = True

        if start_new and current_record:
            if _is_valid_education_record(current_record):
                records.append(_finalize_education_record(current_record))
            current_record = None

        if current_record is None:
            current_record = {
                "degree": parsed_segments.get("degree", ""),
                "institution": parsed_segments.get("institution", ""),
                "result": parsed_segments.get("result", ""),
                "start": parsed_segments.get("start"),
                "end": parsed_segments.get("end"),
                "raw_date": parsed_segments.get("raw_date", ""),
            }
        else:
            for key in ("degree", "institution", "result", "start", "end", "raw_date"):
                if not current_record.get(key) and parsed_segments.get(key):
                    current_record[key] = parsed_segments[key]

    if current_record and _is_valid_education_record(current_record):
        records.append(_finalize_education_record(current_record))

    return records


def _parse_education_line(line: str) -> dict:
    """
    Parses a single line into degree, institution, result, and date tokens.
    Handles delimiters (| - / • at @) and parenthesized substrings.
    """
    res = {
        "degree": "",
        "institution": "",
        "result": "",
        "start": None,
        "end": None,
        "raw_date": "",
    }

    working_line = line

    # 1. Extract parenthesized result or degree if present
    for paren in re.findall(r"\(([^)]+)\)", working_line):
        paren_clean = normalize_whitespace(paren)
        if _looks_like_result(paren_clean):
            if not res["result"]:
                res["result"] = _extract_result_phrase(paren_clean) or paren_clean
        else:
            date_info = parse_date_expression(paren_clean, default_month=None)
            if date_info and (date_info.get("start") or date_info.get("end")):
                res["start"] = date_info.get("start")
                res["end"] = date_info.get("end")
                res["raw_date"] = date_info.get("raw", "")
                working_line = working_line.replace(f"({paren})", " ")

    # 2. Extract result phrase if still unextracted
    if not res["result"]:
        result_phrase = _extract_result_phrase(working_line)
        if result_phrase:
            res["result"] = result_phrase
            working_line = re.sub(re.escape(result_phrase), " ", working_line, flags=re.IGNORECASE)

    # 3. Extract date range if present in line before splitting by hyphen/dash
    date_expr = parse_date_expression(working_line, default_month=None)
    if date_expr and date_expr.get("is_range"):
        if not res["start"] and not res["end"]:
            res["start"] = date_expr.get("start")
            res["end"] = date_expr.get("end")
            res["raw_date"] = date_expr.get("raw", "")
        raw_val = date_expr.get("raw", "")
        if raw_val:
            working_line = re.sub(re.escape(raw_val), " ", working_line, flags=re.IGNORECASE)

    # 4. Check for 'at' or '@' separator (e.g. "School at Degree" or "Degree at School")
    at_parts = re.split(r"\s+(?:at|@)\s+", working_line, flags=re.IGNORECASE)
    if len(at_parts) >= 2:
        for part in at_parts:
            _classify_and_assign_education_fragment(part, res)
        return res

    # 5. Split by primary separators: | , • or hyphen/dash surrounded by spaces
    fragments = [normalize_whitespace(f) for f in re.split(r"\s*\|\s*|\s*[—–]\s*|\s+-\s+|\s*•\s*", working_line) if normalize_whitespace(f)]
    for frag in fragments:
        _classify_and_assign_education_fragment(frag, res)

    return res


def _classify_and_assign_education_fragment(fragment: str, res: dict):
    clean_frag = _clean_education_component(fragment)
    if not clean_frag:
        return

    # Check for date
    date_info = parse_date_expression(clean_frag, default_month=None)
    if date_info and (date_info.get("start") or date_info.get("end")):
        if not res["end"] and not res["start"]:
            res["start"] = date_info.get("start")
            res["end"] = date_info.get("end")
            res["raw_date"] = date_info.get("raw", "")
        return

    # Check for result
    if _looks_like_result(clean_frag):
        if not res["result"]:
            res["result"] = _extract_result_phrase(clean_frag) or clean_frag
        return

    # Check for degree vs institution
    has_deg = _has_degree_keyword(clean_frag)
    has_inst = _looks_like_institution(clean_frag)

    if has_deg and not has_inst:
        if not res["degree"]:
            res["degree"] = clean_frag
        return
    if has_inst and not has_deg:
        if not res["institution"]:
            res["institution"] = clean_frag
        return

    if has_deg and has_inst:
        # Mixed fragment: try splitting e.g. "BSc - Dhaka University"
        subparts = re.split(r"\s+(?:at|@|—|-|\||/)\s+", clean_frag, maxsplit=1)
        if len(subparts) == 2:
            left, right = subparts[0].strip(), subparts[1].strip()
            if _has_degree_keyword(left) and not res["degree"]:
                res["degree"] = left
            if _looks_like_institution(right) and not res["institution"]:
                res["institution"] = right
            elif _has_degree_keyword(right) and not res["degree"]:
                res["degree"] = right
            elif _looks_like_institution(left) and not res["institution"]:
                res["institution"] = left
        elif not res["degree"]:
            res["degree"] = clean_frag
        return

    # Fallback: if not degree and looks like an institution/org name
    if not res["institution"] and _looks_like_org_name(clean_frag):
        res["institution"] = clean_frag
    elif not res["degree"] and len(clean_frag.split()) <= 6:
        res["degree"] = clean_frag


def _finalize_education_record(record: dict) -> dict:
    degree = _clean_education_component(record.get("degree", ""))
    institution = _clean_education_component(record.get("institution", ""))
    result = normalize_whitespace(record.get("result", ""))
    start = record.get("start")
    end = record.get("end")

    # Compatibility year: prefer end date, fallback to start
    year = end or start or ""

    # Confidence calculation
    conf = 0.5
    if degree and institution:
        conf = 0.95 if (start or end or result) else 0.85
    elif degree or institution:
        conf = 0.60

    date_str = f"{start} - {end}" if (start and end) else (end or start or "")
    evidence = {
        "degree": degree,
        "institution": institution,
        "date": date_str,
        "result": result,
    }

    return {
        "degree": degree,
        "institution": institution,
        "start": start,
        "end": end,
        "result": result,
        "year": year,
        "confidence": round(conf, 2),
        "evidence": evidence,
    }


# ==============================================================================
# EXPERIENCE EXTRACTION (Date Anchored & Record Grouping)
# ==============================================================================

def extract_experiences(text: str) -> list[dict]:
    sections = extract_sections(text)
    source_text = sections.get("experience") or text or ""
    lines = [normalize_whitespace(line) for line in source_text.splitlines()]
    lines = [line for line in lines if line and not _is_section_header(line)]
    experiences: list[dict] = []

    date_indices = [idx for idx, line in enumerate(lines) if is_date_anchor_line(line)]

    for idx in date_indices:
        anchor_line = lines[idx]
        date_expr = parse_date_expression(anchor_line, default_month="Jan")
        if not date_expr or not (date_expr.get("start") or date_expr.get("end")):
            continue

        start_val = date_expr.get("start") or ""
        end_val = date_expr.get("end") or ""

        # Check if anchor line has company or title embedded
        anchor_title, anchor_comp, anchor_desc = _split_anchor_experience_content(anchor_line, date_expr)

        designation = anchor_title
        company = anchor_comp
        location = ""

        # Look in preceding lines (up to 3 lines before)
        preceding = lines[max(0, idx - 3) : idx]
        for candidate in reversed(preceding):
            if is_date_anchor_line(candidate) or _looks_like_description(candidate):
                continue
            if _looks_like_location(candidate) and not location:
                location = candidate
                continue

            split_title, split_comp = _split_mixed_experience_line(candidate)
            if split_title and split_comp:
                if not designation:
                    designation = split_title
                if not company:
                    company = split_comp
                continue

            cand_type = _classify_experience_line(candidate)
            if cand_type == "designation" and not designation:
                designation = candidate
            elif cand_type == "company" and not company:
                company = candidate
            elif _looks_like_title(candidate) and not designation:
                designation = candidate
            elif _looks_like_org_name(candidate) and not company:
                company = candidate
            elif not designation and not _looks_like_description(candidate):
                designation = candidate
            elif not company and not _looks_like_description(candidate):
                company = candidate

        # Look in succeeding lines (up to 2 lines after, if date came first)
        succeeding = lines[idx + 1 : min(len(lines), idx + 4)]
        for candidate in succeeding:
            if is_date_anchor_line(candidate) or _looks_like_description(candidate):
                continue
            if _looks_like_location(candidate) and not location:
                location = candidate
                continue

            cand_type = _classify_experience_line(candidate)
            if cand_type == "company" and not company:
                company = candidate
            elif cand_type == "designation" and not designation:
                designation = candidate
            elif not designation and _looks_like_title(candidate):
                designation = candidate
            elif not company and _looks_like_org_name(candidate):
                company = candidate

        # Clean components
        designation = _strip_bullets(designation)
        company = _strip_bullets(company)

        # Fallback split if designation and company are fused
        if designation and not company:
            s_title, s_comp = _split_mixed_experience_line(designation)
            if s_title and s_comp:
                designation, company = s_title, s_comp

        if not designation and not company:
            continue

        conf = 0.5
        if designation and company:
            conf = 0.95
        elif designation:
            conf = 0.70

        date_str = f"{start_val} - {end_val}" if (start_val and end_val) else (end_val or start_val or "")
        experiences.append({
            "designation": designation,
            "company": company,
            "start": start_val,
            "end": end_val,
            "location": location,
            "confidence": round(conf, 2),
            "evidence": {
                "designation": designation,
                "company": company,
                "date": date_str,
            }
        })

    return experiences


def _split_anchor_experience_content(anchor_line: str, date_expr: dict) -> tuple[str, str, str]:
    """
    Removes the date portion from an anchor line and extracts title, company, description.
    e.g. 'Lead Developer - Mosaic Systems | Jan 2020 - Jan 2024 | Built automation...'
    """
    raw_date = date_expr.get("raw", "")
    line_without_date = anchor_line
    if raw_date:
        line_without_date = re.sub(re.escape(raw_date), " ", line_without_date, flags=re.IGNORECASE)

    parts = [normalize_whitespace(p) for p in re.split(r"\s*\|\s*", line_without_date) if normalize_whitespace(p)]
    title = ""
    company = ""
    desc = ""

    for part in parts:
        if _looks_like_description(part):
            desc = part
            continue
        s_title, s_comp = _split_mixed_experience_line(part)
        if s_title and s_comp:
            if not title:
                title = s_title
            if not company:
                company = s_comp
            continue
        c_type = _classify_experience_line(part)
        if c_type == "designation" and not title:
            title = part
        elif c_type == "company" and not company:
            company = part
        elif _looks_like_title(part) and not title:
            title = part
        elif not company and _looks_like_org_name(part):
            company = part

    return title, company, desc


# ==============================================================================
# CLASSIFIERS & HELPERS
# ==============================================================================

def _is_section_header(line: str) -> bool:
    norm = normalize_for_match(line)
    for headers in SECTION_HEADERS.values():
        if norm in headers:
            return True
    return False


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
    return all(token[:1].isalpha() and (token[:1].isupper() or token.isupper()) for token in tokens)


def _looks_like_location(line: str) -> bool:
    lowered = normalize_for_match(line)
    return any(keyword in lowered for keyword in ["city", "state", "country", "india", "usa", "remote", "bangladesh", "dhaka"])


def _classify_experience_line(line: str) -> str:
    lowered = normalize_for_match(line)
    if any(keyword in lowered for keyword in DESIGNATION_KEYWORDS):
        return "designation"
    if any(keyword in lowered for keyword in COMPANY_KEYWORDS):
        return "company"
    return "unknown"


def _split_mixed_experience_line(text: str) -> tuple[str, str]:
    cleaned = normalize_whitespace(text)
    if not cleaned:
        return "", ""
    parts = re.split(r"\s*(?:\bat\b|@|[–—-]|\|)\s*", cleaned, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2:
        return "", ""
    left = normalize_whitespace(parts[0])
    right = normalize_whitespace(parts[1])
    if not left or not right:
        return "", ""
    left_is_designation = any(keyword in normalize_for_match(left) for keyword in DESIGNATION_KEYWORDS)
    right_is_designation = any(keyword in normalize_for_match(right) for keyword in DESIGNATION_KEYWORDS)
    if left_is_designation and not right_is_designation:
        return left, right
    if right_is_designation and not left_is_designation:
        return right, left
    if _looks_like_org_name(right) and not _looks_like_org_name(left):
        return left, right
    if _looks_like_org_name(left) and not _looks_like_org_name(right):
        return right, left
    return "", ""


def _looks_like_title(text: str) -> bool:
    lowered = normalize_for_match(text)
    return any(keyword in lowered for keyword in DESIGNATION_KEYWORDS)


def _has_degree_keyword(text: str) -> bool:
    lowered = normalize_for_match(text)
    return any(re.search(rf"\b{re.escape(k)}\b", lowered) for k in DEGREE_KEYWORDS)


def _looks_like_institution(text: str) -> bool:
    lowered = normalize_for_match(text)
    return any(k in lowered for k in INSTITUTION_KEYWORDS)


def _looks_like_result(text: str) -> bool:
    lowered = normalize_for_match(text)
    if any(k in lowered for k in ["cgpa", "gpa", "percentage", "class", "grade"]):
        return True
    return bool(re.search(r"\b\d(?:\.\d+)?\s*/\s*\d(?:\.\d+)?\b", text))


def _extract_result_phrase(text: str) -> str:
    match = re.search(r"\b(?:CGPA|GPA)\s*[:\-]?\s*[\d.]+\s*(?:/\s*[\d.]+)?(?:\s*\([^)]+\))?", text, re.IGNORECASE)
    if match:
        return normalize_whitespace(match.group(0))
    match = re.search(r"\bPercentage\s*[:\-]?\s*[\d.]+%?", text, re.IGNORECASE)
    if match:
        return normalize_whitespace(match.group(0))
    match = re.search(r"\b(?:first|second)\s+class\b", text, re.IGNORECASE)
    if match:
        return normalize_whitespace(match.group(0))
    match = re.search(r"\b\d\.\d{2}\s*/\s*\d\.\d{2}\b", text)
    if match:
        return normalize_whitespace(match.group(0))
    return ""


def _looks_like_description(text: str) -> bool:
    lowered = normalize_for_match(text)
    tokens = lowered.split()
    if len(tokens) > 10:
        return True
    if len(tokens) >= 6 and text.rstrip().endswith((".", ";", ":")):
        return True
    if tokens and tokens[0] in DESCRIPTION_START_VERBS:
        return True
    return False


def _looks_like_org_name(text: str) -> bool:
    cleaned = _strip_bullets(text)
    if not cleaned or _looks_like_result(cleaned) or _looks_like_description(cleaned) or _looks_like_title(cleaned):
        return False
    tokens = [t for t in re.split(r"\s+", cleaned) if t]
    if not tokens or len(tokens) > 8:
        return False
    if any(t.islower() for t in tokens) and not any(t.isupper() for t in tokens):
        return False
    return True


def _clean_education_component(text: str) -> str:
    cleaned = normalize_whitespace(text or "")
    if not cleaned:
        return ""
    cleaned = re.sub(r"\s*\((?=[^)]*\b(?:cgpa|gpa|percentage)\b)[^)]*\)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*(?:\||/|[-–—])\s*$", "", cleaned)
    return normalize_whitespace(cleaned)


def _strip_bullets(text: str) -> str:
    return re.sub(r"^[\s\-*•·]+", "", normalize_whitespace(text or ""))


def _is_valid_education_record(record: dict) -> bool:
    degree = normalize_whitespace(record.get("degree", ""))
    institution = normalize_whitespace(record.get("institution", ""))
    if not degree and not institution:
        return False
    if degree and _looks_like_result(degree):
        return False
    if institution and _looks_like_result(institution):
        return False
    return True

