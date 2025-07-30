from datetime import datetime
def build_gguf_resume_prompt(resume_text: str, mandatory_skills: list, optional_skills: list) -> str:
    today_date = datetime.now().strftime("%d %b %Y")

    prompt_content = f"""
    You are an AI assistant that extracts structured data from resumes.

    Respond only with a valid JSON object. No extra text.

    Extract the following from the resume text:

    - **name**: Full name, or "" if not found.
    - **email**: Email address, or "" if not found.
    - **phone**: Phone number, or "" if not found.
    - **github**: GitHub URL or username, or "" if not found.
    - **linkedin**: LinkedIn URL or username, or "" if not found.
    - **skills**: Only skills explicitly listed in the Experience and Projects sections. Preserve original casing/spelling.
    - **experiences**: List of jobs with:
      - designation: Job title  
      - company: Company name  
      - start: "Mon YYYY"  
      - end: "Mon YYYY" or "Present"

    Skill Matching:

    - Match skills case-insensitively.
    - Use common aliases when comparing (e.g., "DRF" → "django rest framework").
    - A skill is valid only if the skill name or one of its aliases appears in the extracted `skills` list.
    - No inferred or assumed skills.
    - Skills matched as mandatory must not be counted again as optional.

    - **Mandatory Skills**: {', '.join(mandatory_skills)}
      - Add matches to `matched_mandatory`
      - Add non-matches to `missing_mandatory`

    - **Optional Skills**: {', '.join(optional_skills)}
      - Match only if not already matched as mandatory
      - Add matches to `matched_optional`
      - Add non-matches to `missing_optional`

    Output format:
    {{
      "name": "",
      "email": "",
      "phone": "",
      "github": "",
      "linkedin": "",
      "skills": [],
      "experiences": [
        {{
          "designation": "",
          "company": "",
          "start": "Jan 2024",
          "end": "Jul 2024",
        }}
      ],
      "matched_mandatory": [],
      "missing_mandatory": [],
      "matched_optional": [],
      "missing_optional": []
    }}

    Resume:
    {resume_text.strip()}
    """.strip()


    gguf_prompt = f"""<|start_header_id|>system<|end_header_id|>

Cutting Knowledge Date: December 2023
Today Date: {today_date}
<|eot_id|>

<|start_header_id|>user<|end_header_id|>

{prompt_content}
<|eot_id|>

<|start_header_id|>assistant<|end_header_id|>

"""
    return gguf_prompt
