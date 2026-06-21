import re

from .normalizer import normalize_for_match


def match_skills(resume_text: str, mandatory_skills, optional_skills) -> dict:
    normalized_text = normalize_for_match(resume_text)
    matched_mandatory = []
    missing_mandatory = []
    matched_optional = []
    missing_optional = []

    for skill in mandatory_skills:
        if skill_matches_text(normalized_text, skill.title, getattr(skill, "aliases", None)):
            matched_mandatory.append(skill.title)
        else:
            missing_mandatory.append(skill.title)

    for skill in optional_skills:
        if skill.title in matched_mandatory:
            continue
        if skill_matches_text(normalized_text, skill.title, getattr(skill, "aliases", None)):
            matched_optional.append(skill.title)
        else:
            missing_optional.append(skill.title)

    return {
        "matched_mandatory": matched_mandatory,
        "missing_mandatory": missing_mandatory,
        "matched_optional": matched_optional,
        "missing_optional": missing_optional,
        "skills": sorted(set(matched_mandatory + matched_optional)),
    }


def skill_matches_text(normalized_text: str, title: str, aliases) -> bool:
    candidates = [title, *(aliases or [])]
    for candidate in candidates:
        normalized_candidate = normalize_for_match(candidate)
        if not normalized_candidate:
            continue
        if _contains_phrase(normalized_text, normalized_candidate):
            return True
    return False


def _contains_phrase(text: str, phrase: str) -> bool:
    escaped = re.escape(phrase)
    escaped = escaped.replace(r"\ ", r"\s+")
    pattern = rf"(?<!\w){escaped}(?!\w)"
    return re.search(pattern, text, re.IGNORECASE) is not None

