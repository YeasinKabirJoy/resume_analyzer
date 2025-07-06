from datetime import datetime
def build_gguf_resume_prompt(resume_text: str, mandatory_skills: list, optional_skills: list) -> str:
    today_date = datetime.now().strftime("%d %b %Y")

    prompt_content = f"""
You are an AI assistant that extracts structured data from resumes.

Respond only with a valid JSON object. No explanation or extra text.

Instructions:

1. Extract the following:
   - name, email, phone, github, linkedin (use "" if not found)
   - all skills listed in the resume (keep original casing and spelling)
   - experiences: include "designation", "company", "start", "end" (format: "Mon YYYY" or "Present")

2. Skill Matching:
   - Match resume skills against the provided lists (case-insensitive)
   - Consider common aliases (e.g., "DRF" → "django rest framework")
   - Do not duplicate a skill across mandatory and optional
   - Use the original skill names from the lists in the output
   - Add unmatched ones to the respective "missing_*" lists
   - Match skills only if the exact skill or its common abbreviation appears in the resume text.
   - Do not guess or infer skills that are not mentioned.

Mandatory Skills: {', '.join(mandatory_skills)}
Optional Skills: {', '.join(optional_skills)}

3. Output Format:
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
      "end": "Jul 2024"
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
