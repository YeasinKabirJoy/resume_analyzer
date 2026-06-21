from utils.final_score import calculate_final_score


def score_resume(total_experience, required_experience, matched_mandatory, missing_mandatory, matched_optional, missing_optional):
    return calculate_final_score(
        total_experience,
        required_experience,
        matched_mandatory,
        missing_mandatory,
        matched_optional,
        missing_optional,
    )

