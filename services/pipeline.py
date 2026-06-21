from services.rule_extractors import extract_contacts, extract_experiences, extract_name, extract_sections
from services.scorer import score_resume
from services.skill_matcher import match_skills
from utils.experiance_calculate import calculate_total_experience
from utils.pdf_parser import extract_text_from_pdf


def process_resume(resume_record):
    text = extract_text_from_pdf(resume_record.resume.path)
    if not text or len(text.strip()) < 200:
        raise ValueError("Extracted resume text is too short for ATS analysis.")

    return analyze_text(text, resume_record.job_role)


def analyze_text(resume_text, job_role):
    sections = extract_sections(resume_text)
    contacts = extract_contacts(resume_text)
    experiences = extract_experiences(resume_text)
    name = extract_name(resume_text, contacts)

    skill_requirements = list(job_role.skill_requirements.select_related("skill").all())
    mandatory_skills = [item.skill for item in skill_requirements if item.is_mandatory]
    optional_skills = [item.skill for item in skill_requirements if not item.is_mandatory]
    skill_match = match_skills(resume_text, mandatory_skills, optional_skills)

    total_experience, experience_breakdown = calculate_total_experience(experiences)
    final_score = score_resume(
        total_experience,
        job_role.minimum_experience,
        skill_match["matched_mandatory"],
        skill_match["missing_mandatory"],
        skill_match["matched_optional"],
        skill_match["missing_optional"],
    )

    text_quality_score = calculate_text_quality_score(resume_text, sections, contacts, experiences)
    confidence_score = calculate_confidence_score(text_quality_score, skill_match, experiences)

    return {
        "name": name,
        "email": contacts["email"],
        "phone": contacts["phone"],
        "github": contacts["github"],
        "linkedin": contacts["linkedin"],
        "skills": skill_match["skills"],
        "experiences": _attach_durations(experiences, experience_breakdown),
        "total_experience": total_experience,
        "matched_mandatory_skills": skill_match["matched_mandatory"],
        "missed_mandatory_skills": skill_match["missing_mandatory"],
        "matched_optional_skills": skill_match["matched_optional"],
        "missed_optional_skills": skill_match["missing_optional"],
        "score": int(round(final_score["score"])),
        "verdict": final_score["status"],
        "reason": final_score["reason"],
        "confidence_score": confidence_score,
        "text_quality_score": text_quality_score,
    }


def calculate_text_quality_score(resume_text, sections, contacts, experiences):
    text = (resume_text or "").strip()
    length_score = min(len(text) / 5000, 1.0) * 40
    section_score = min(len(sections) / 5, 1.0) * 30
    contact_score = sum(1 for value in contacts.values() if value) / 4 * 15
    experience_score = min(len(experiences) / 3, 1.0) * 15
    return round(length_score + section_score + contact_score + experience_score, 2)


def calculate_confidence_score(text_quality_score, skill_match, experiences):
    skill_coverage = 0
    mandatory_total = len(skill_match["matched_mandatory"]) + len(skill_match["missing_mandatory"])
    if mandatory_total:
        skill_coverage += len(skill_match["matched_mandatory"]) / mandatory_total * 55
    optional_total = len(skill_match["matched_optional"]) + len(skill_match["missing_optional"])
    if optional_total:
        skill_coverage += len(skill_match["matched_optional"]) / optional_total * 25
    if experiences:
        skill_coverage += min(len(experiences) / 3, 1.0) * 20
    return round((text_quality_score * 0.6) + (skill_coverage * 0.4), 2)


def _attach_durations(experiences, experience_breakdown):
    combined = []
    for index, experience in enumerate(experiences):
        item = dict(experience)
        if index < len(experience_breakdown):
            item["duration"] = experience_breakdown[index]
        combined.append(item)
    return combined
