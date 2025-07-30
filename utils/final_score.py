
exp_bonus_threshold =5
def calculate_final_score(experience_years,required_years,matched_mandatory,missing_mandatory,matched_optional,missing_optional):
    
    if experience_years > required_years + exp_bonus_threshold:
        exp_weight = 60
        skill_weight = 40
    else:
        exp_weight = 40
        skill_weight = 60

    # --- Experience Score ---
    if experience_years >= required_years:
        experience_score = exp_weight
    else:
        experience_score = exp_weight * (experience_years / required_years)

    # --- Skill Score ---
    total_mandatory = len(matched_mandatory) + len(missing_mandatory)
    mandatory_score = 0
    if total_mandatory > 0:
        mandatory_score = (skill_weight * 2/3) * (len(matched_mandatory) / total_mandatory)

    total_optional = len(matched_optional) + len(missing_optional)
    optional_score = 0
    if total_optional > 0:
        optional_score = (skill_weight * 1/3) * (len(matched_optional) / total_optional)

    skill_score = mandatory_score + optional_score

    # --- Total Score ---
    total_score = round(experience_score + skill_score, 2)

    # --- Classification & Reason ---
    if total_score < 80:
        status = "skipped"
        if total_mandatory and (len(matched_mandatory) / total_mandatory) < 0.5:
            reason = "Low mandatory skill match"
        elif experience_years < required_years:
            reason = "Insufficient experience"
        else:
            reason = "Score below threshold"
    elif total_score <= 95:
        status = "matched"
        reason = "Meets requirements"
    else:
        status = "overqualified"
        reason = "Exceeds both experience and skills"

    return {
        "score": total_score,
        "status": status,
        "reason": reason,
    }