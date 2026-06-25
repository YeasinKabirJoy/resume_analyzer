import re
from functools import lru_cache

from .normalizer import normalize_for_match, normalize_whitespace
from .rule_extractors import (
    extract_experiences as rule_extract_experiences,
    extract_sections,
    normalize_date_token,
    parse_date_range,
)

NER_MODEL_NAME = "elastic/distilbert-base-cased-finetuned-conll03-english"
TITLE_KEYWORDS = [
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
EXPERIENCE_COMPANY_HINTS = [
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
    "university",
    "institute",
]
DESCRIPTION_HINTS = [
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
    "streamline",
    "streamlined",
    "integration",
]
EDUCATION_KEYWORDS = [
    "bsc",
    "msc",
    "msc.",
    "bachelor",
    "master",
    "phd",
    "diploma",
    "degree",
    "honours",
    "honors",
    "cgpa",
    "gpa",
    "percentage",
    "university",
    "college",
    "institute",
    "school",
]
EXPLICIT_DEGREE_HINTS = [
    "bsc",
    "msc",
    "bachelor",
    "master",
    "phd",
    "diploma",
    "degree",
    "honours",
    "honors",
    "certificate",
    "higher secondary certificate",
    "secondary school certificate",
    "hsc",
    "ssc",
    "o level",
    "a level",
]


def extract_experiences(text: str) -> list[dict]:
    sections = extract_sections(text)
    experience_text = sections.get("experience") or text or ""
    records = _extract_ner_first_section_records(experience_text, mode="experience")
    records = [record for record in records if _is_valid_experience_record(record)]
    if records:
        print("EXPERIENCE EXTRACTED BY: NER-FIRST")
        return records
    print("EXPERIENCE EXTRACTED BY: RULES")
    return [record for record in rule_extract_experiences(text) if _is_valid_experience_record(record)]


def extract_educations(text: str) -> list[dict]:
    sections = extract_sections(text)
    education_text = sections.get("education") or text or ""
    records = _extract_ner_first_section_records(education_text, mode="education")
    records = [record for record in records if _is_valid_education_record(record)]
    if records:
        print("EDUCATION EXTRACTED BY: NER-FIRST")
        return records
    print("EDUCATION EXTRACTED BY: RULES")
    return [record for record in rule_extract_educations(education_text) if _is_valid_education_record(record)]


def _extract_ner_first_section_records(section_text: str, mode: str) -> list[dict]:
    lines = [normalize_whitespace(line) for line in (section_text or "").splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return []

    records = []
    date_indexes = [index for index, line in enumerate(lines) if parse_date_range(line) or _contains_year(line)]

    for index in date_indexes:
        date_info = parse_date_range(lines[index])
        window_start = max(0, index - 4)
        window_end = min(len(lines), index + 4)
        before = lines[window_start:index]
        after = lines[index + 1:window_end]

        if mode == "experience":
            record = _build_experience_record(before, after, date_info, lines[index])
        else:
            record = _build_education_record(before, after, date_info, lines[index])

        if record and record not in records:
            records.append(record)

    return records


def _build_experience_record(before: list[str], after: list[str], date_info: dict | None, anchor_line: str) -> dict:
    designation = _pick_experience_designation(before, after)
    company = _pick_experience_company(before, after, designation)
    location = _pick_location(before, after)

    mixed_designation, mixed_company = _split_mixed_experience_line(designation)
    if not designation and mixed_designation:
        designation = mixed_designation
    if not company and mixed_company:
        company = mixed_company

    designation = _clean_experience_component(designation)
    company = _clean_experience_component(company)
    location = _clean_experience_component(location)

    return {
        "designation": designation,
        "company": company,
        "location": location,
        "start": date_info["start"] if date_info else normalize_date_token(anchor_line.split("-")[0].strip()),
        "end": date_info["end"] if date_info else "",
    }


def _build_education_record(before: list[str], after: list[str], date_info: dict | None, anchor_line: str) -> dict:
    degree = _pick_degree(before, after)
    institution = _pick_institution(before, after, degree)
    result = _pick_result(before, after)

    mixed_degree, mixed_institution = _split_mixed_education_line(degree)
    if not degree and mixed_degree:
        degree = mixed_degree
    if not institution and mixed_institution:
        institution = mixed_institution

    year = ""
    if date_info:
        year = date_info["end"] if date_info["end"] and date_info["end"] != "Present" else date_info["start"]
    if not year:
        year_match = re.search(r"\b(19|20)\d{2}\b", anchor_line)
        year = year_match.group(0) if year_match else ""

    return {
        "degree": degree,
        "institution": institution,
        "result": result,
        "year": year,
    }


def infer_line_entities(text: str) -> dict:
    entities = {"company": "", "location": ""}
    spans = extract_ner_spans(text)
    for entity in spans:
        label = entity.get("label") or entity.get("entity_group") or entity.get("entity")
        value = entity.get("word") or entity.get("text") or ""
        if label in {"ORG", "COMPANY"} and not entities["company"]:
            entities["company"] = value
        elif label in {"LOC", "LOCATION"} and not entities["location"]:
            entities["location"] = value
    return entities


def _pick_experience_designation(before: list[str], after: list[str]) -> str:
    for candidate in reversed(before):
        split_designation, _ = _split_mixed_experience_line(candidate)
        if split_designation:
            return _strip_bullets(split_designation)
        if _looks_like_title(candidate) and not _looks_like_description(candidate) and not _looks_like_result(candidate):
            return _strip_bullets(candidate)
    for candidate in after:
        split_designation, _ = _split_mixed_experience_line(candidate)
        if split_designation:
            return _strip_bullets(split_designation)
        lowered = normalize_for_match(candidate)
        if any(keyword in lowered for keyword in TITLE_KEYWORDS) and not _looks_like_company(candidate) and not _looks_like_description(candidate):
            return _strip_bullets(candidate)
    return ""


def _pick_experience_company(before: list[str], after: list[str], designation: str) -> str:
    designation_normalized = normalize_for_match(designation)
    for candidate in reversed(before):
        cleaned = _strip_bullets(candidate)
        lowered = normalize_for_match(cleaned)
        if not cleaned or cleaned == designation or _looks_like_result(cleaned) or _looks_like_description(cleaned):
            continue
        split_designation, split_company = _split_mixed_experience_line(cleaned)
        if split_company and (not designation or normalize_for_match(split_designation) != designation_normalized):
            return split_company
        if any(hint in lowered for hint in EXPERIENCE_COMPANY_HINTS):
            return cleaned
        entities = infer_line_entities(cleaned)
        if entities["company"] and not _looks_like_title(cleaned):
            return cleaned
        if _looks_like_org_name(cleaned) and not _looks_like_title(cleaned):
            return cleaned
    for candidate in after:
        cleaned = _strip_bullets(candidate)
        lowered = normalize_for_match(cleaned)
        if not cleaned or cleaned == designation or _looks_like_result(cleaned) or _looks_like_description(cleaned):
            continue
        split_designation, split_company = _split_mixed_experience_line(cleaned)
        if split_company and (not designation or normalize_for_match(split_designation) != designation_normalized):
            return split_company
        if any(hint in lowered for hint in EXPERIENCE_COMPANY_HINTS):
            return cleaned
        entities = infer_line_entities(cleaned)
        if entities["company"] and not _looks_like_title(cleaned):
            return cleaned
        if _looks_like_org_name(cleaned) and not _looks_like_title(cleaned):
            return cleaned
    return ""


def _pick_location(before: list[str], after: list[str]) -> str:
    for candidate in before + after:
        entities = infer_line_entities(candidate)
        if entities["location"]:
            return _strip_bullets(candidate)
    return ""


def _pick_degree(before: list[str], after: list[str]) -> str:
    candidates = list(reversed(before)) + after
    for candidate in candidates:
        split_degree, _ = _split_mixed_education_line(candidate)
        if split_degree:
            return _strip_bullets(split_degree)
        if _looks_like_degree(candidate):
            return _strip_bullets(candidate)
    for candidate in candidates:
        lowered = normalize_for_match(candidate)
        if any(keyword in lowered for keyword in EDUCATION_KEYWORDS) and not _looks_like_institution(candidate):
            return _strip_bullets(candidate)
    return ""


def _pick_institution(before: list[str], after: list[str], degree: str) -> str:
    candidates = list(reversed(before)) + after
    degree_normalized = normalize_for_match(degree)
    for candidate in candidates:
        cleaned = _strip_bullets(candidate)
        if not cleaned:
            continue
        _, split_institution = _split_mixed_education_line(candidate)
        if split_institution:
            return _strip_bullets(split_institution)
        if cleaned == degree or _looks_like_result(cleaned) or _looks_like_description(cleaned):
            continue
        lowered = normalize_for_match(cleaned)
        if _looks_like_institution(cleaned):
            return cleaned
        entities = infer_line_entities(cleaned)
        if entities["company"] and cleaned != degree:
            return cleaned
        if _looks_like_org_name(cleaned):
            return cleaned
        if degree_normalized and degree_normalized in lowered:
            continue
    return ""


def _pick_result(before: list[str], after: list[str]) -> str:
    for candidate in before + after:
        if _looks_like_result(candidate):
            return _strip_bullets(candidate)
    return ""


def _split_mixed_experience_line(text: str) -> tuple[str, str]:
    if not text:
        return "", ""
    parts = re.split(r"\s+(?:at|@|—|-|\||/)\s+", text, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2:
        return "", ""
    left, right = (_strip_bullets(part) for part in parts)
    if _looks_like_title(left) and (right and not _looks_like_title(right)):
        return left, right
    if _looks_like_title(right) and (left and not _looks_like_title(left)):
        return right, left
    return "", ""


def _split_mixed_education_line(text: str) -> tuple[str, str]:
    if not text:
        return "", ""
    parts = re.split(r"\s+(?:at|@|—|-|\||/)\s+", text, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2:
        return "", ""
    left, right = (_strip_bullets(part) for part in parts)
    if _looks_like_institution(left) and _has_degree_keyword(right):
        return right, left
    if _looks_like_institution(right) and _has_degree_keyword(left):
        return left, right
    if _has_degree_keyword(left) and not _looks_like_institution(left) and right and _looks_like_institution(right):
        return left, right
    if _has_degree_keyword(right) and not _looks_like_institution(right) and left and _looks_like_institution(left):
        return right, left
    return "", ""


def _strip_bullets(text: str) -> str:
    return re.sub(r"^[\s\-*•·]+", "", normalize_whitespace(text or ""))


@lru_cache(maxsize=1)
def get_ner_pipeline():
    try:
        from transformers import pipeline
    except ImportError:
        return None

    try:
        return pipeline(
            task="token-classification",
            model=NER_MODEL_NAME,
            aggregation_strategy="simple",
        )
    except Exception:
        return None


def extract_ner_spans(text: str) -> list[dict]:
    ner = get_ner_pipeline()
    if ner is None or not text or not text.strip():
        return []
    try:
        return ner(text)
    except Exception:
        return []


def rule_extract_educations(text: str) -> list[dict]:
    lines = [normalize_whitespace(line) for line in (text or "").splitlines()]
    lines = [line for line in lines if line]
    records = []

    for index, line in enumerate(lines):
        split_degree, split_institution = _split_mixed_education_line(line)
        split_result, result_institution = _split_result_institution_line(line)
        is_degree_line = bool(split_degree) or _looks_like_degree(line)
        is_institution_line = bool(split_institution) or bool(result_institution) or _looks_like_institution(line)
        is_result_line = bool(split_result) or _looks_like_result(line)
        if not is_degree_line and not is_institution_line and not is_result_line:
            continue

        window = lines[max(0, index - 2) : min(len(lines), index + 3)]
        degree = split_degree or (_clean_education_component(line) if _looks_like_degree(line) else "")
        institution = split_institution or result_institution or (_clean_education_component(line) if _looks_like_institution(line) and not _looks_like_degree(line) else "")
        result = split_result or _extract_result_phrase(line) or next((candidate for candidate in window if candidate != line and _looks_like_result(candidate)), "")
        if not degree and not institution and is_result_line:
            if records and not records[-1].get("result"):
                records[-1]["result"] = result
            continue
        if not degree and not institution:
            continue
        if not degree:
            degree = next((candidate for candidate in window if candidate != line and _looks_like_degree(candidate) and not _looks_like_result(candidate)), "")
        if not institution:
            institution = next((candidate for candidate in window if candidate != line and _looks_like_institution(candidate) and not _looks_like_result(candidate)), "")
        year_match = next((re.search(r"\b(19|20)\d{2}\b", candidate) for candidate in window if re.search(r"\b(19|20)\d{2}\b", candidate)), None)
        year = year_match.group(0) if year_match else ""

        degree = _clean_education_component(degree)
        institution = _clean_education_component(institution)
        result = normalize_whitespace(result)

        record = {
            "degree": degree,
            "institution": institution,
            "result": result,
            "year": year,
        }
        if records and _can_merge_education_records(records[-1], record):
            records[-1] = _merge_education_records(records[-1], record)
        elif record not in records:
            records.append(record)

    return records


def _extract_result_phrase(text: str) -> str:
    lowered = normalize_for_match(text)
    if "cgpa" in lowered:
        match = re.search(r"CGPA\s*[:\-]?\s*[\d./]+\s*/\s*[\d./]+(?:\s*\([^)]+\))?", text, re.IGNORECASE)
        if match:
            return normalize_whitespace(match.group(0))
    if "gpa" in lowered:
        match = re.search(r"GPA\s*[:\-]?\s*[\d./]+\s*/\s*[\d./]+(?:\s*\([^)]+\))?", text, re.IGNORECASE)
        if match:
            return normalize_whitespace(match.group(0))
    if "percentage" in lowered:
        match = re.search(r"Percentage\s*[:\-]?\s*[\d.]+%?", text, re.IGNORECASE)
        if match:
            return normalize_whitespace(match.group(0))
    return ""


def _split_result_institution_line(text: str) -> tuple[str, str]:
    if not text or not _looks_like_result(text):
        return "", ""
    parts = re.split(r"\s+at\s+", text, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2:
        return "", ""
    left, right = (_strip_bullets(part) for part in parts)
    if _looks_like_result(left) and (_looks_like_institution(right) or _looks_like_org_name(right)):
        return _extract_result_phrase(left) or left, right
    return "", ""


def _clean_education_component(text: str) -> str:
    cleaned = normalize_whitespace(text or "")
    if not cleaned:
        return ""
    cleaned = re.sub(r"\s*\((?=[^)]*\b(?:cgpa|gpa|percentage)\b)[^)]*\)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*-\s*\d{4}\b", "", cleaned)
    cleaned = re.sub(r"\s+\d{4}$", "", cleaned)
    return normalize_whitespace(cleaned)


def _can_merge_education_records(existing: dict, candidate: dict) -> bool:
    if not existing:
        return False
    if not existing.get("degree") and candidate.get("degree"):
        return True
    if not existing.get("institution") and candidate.get("institution"):
        return True
    if not existing.get("result") and candidate.get("result"):
        return True
    if not existing.get("year") and candidate.get("year"):
        return True
    return False


def _merge_education_records(existing: dict, candidate: dict) -> dict:
    merged = dict(existing)
    for key in ("degree", "institution", "result", "year"):
        if not merged.get(key) and candidate.get(key):
            merged[key] = candidate[key]
    return merged


def _contains_year(text: str) -> bool:
    return bool(re.search(r"\b(19|20)\d{2}\b", text or ""))


def _looks_like_title(text: str) -> bool:
    lowered = normalize_for_match(text)
    return any(keyword in lowered for keyword in TITLE_KEYWORDS)


def _looks_like_company(text: str) -> bool:
    lowered = normalize_for_match(text)
    return any(keyword in lowered for keyword in EXPERIENCE_COMPANY_HINTS)


def _looks_like_degree(text: str) -> bool:
    if _looks_like_institution(text):
        return False
    return _has_degree_keyword(text)


def _looks_like_institution(text: str) -> bool:
    if _looks_like_result(text) or _has_degree_keyword(text):
        return False
    lowered = normalize_for_match(text)
    return any(keyword in lowered for keyword in ["university", "college", "institute", "school", "academy"])


def _looks_like_result(text: str) -> bool:
    lowered = normalize_for_match(text)
    return bool(re.search(r"\b(?:cgpa|gpa|percentage|class)\b", lowered))


def _looks_like_description(text: str) -> bool:
    lowered = normalize_for_match(text)
    if len(lowered.split()) > 10:
        return True
    return any(keyword in lowered for keyword in DESCRIPTION_HINTS)


def _clean_experience_component(text: str) -> str:
    cleaned = normalize_whitespace(text or "")
    if not cleaned:
        return ""
    cleaned = re.sub(r"\s*-\s*\d{4}\b", "", cleaned)
    cleaned = re.sub(r"\s+\d{4}$", "", cleaned)
    return normalize_whitespace(cleaned)


def _is_valid_experience_record(record: dict) -> bool:
    designation = _clean_experience_component(record.get("designation", ""))
    company = _clean_experience_component(record.get("company", ""))
    location = _clean_experience_component(record.get("location", ""))

    if designation and _looks_like_description(designation):
        return False
    if company and (_looks_like_description(company) or _looks_like_title(company)):
        return False
    if location and _looks_like_description(location):
        return False
    if not designation and not company:
        return False
    return True


def _looks_like_org_name(text: str) -> bool:
    cleaned = _strip_bullets(text)
    if not cleaned or _looks_like_result(cleaned) or _looks_like_description(cleaned):
        return False
    if parse_date_range(cleaned):
        return False
    tokens = [token for token in re.split(r"\s+", cleaned) if token]
    if not (2 <= len(tokens) <= 8):
        return False
    if any(token.islower() for token in tokens) and not any(token.isupper() for token in tokens):
        return False
    if cleaned.endswith((".", ",", ";", ":")):
        return False
    return True


def _has_degree_keyword(text: str) -> bool:
    lowered = normalize_for_match(text)
    return any(keyword in lowered for keyword in EXPLICIT_DEGREE_HINTS)


def _is_valid_education_record(record: dict) -> bool:
    degree = _clean_education_component(record.get("degree", ""))
    institution = _clean_education_component(record.get("institution", ""))
    result = normalize_whitespace(record.get("result", ""))

    if not degree or not institution:
        return False
    if _looks_like_result(degree):
        return False
    if _looks_like_result(institution):
        return False
    if degree == institution:
        return False
    if result and not _looks_like_result(result):
        return False
    return True
