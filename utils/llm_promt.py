def make_promt(resume_text,mandatory_skills,optional_skills):
    promt = f"""Extract information from the following resume text and produce a JSON output based on the provided mandatory and optional skills and the specified format. 
The resume text may contain details such as name, contact information, skills, experiences, and other relevant data. 
Ensure the JSON output includes all required fields, handling missing information appropriately (e.g., empty strings for missing contact details).
Calculate the total experience in years as a float, approximating months to years (e.g., 12 months = 1.0 year, 6 months = 0.5 years). 
For skills, check if the mandatory and optional skills are present in the resume, and list them in the matched and missing fields using the exact spelling and casing provided in the mandatory and optional skills lists. 
If a skill is implied (e.g., "DRF" implies "django rest framework"), include it in the matched skills using the exact text from the mandatory or optional skills list (e.g., "django rest framework" instead of "DRF" or "Django REST Framework").



Resume Text:

{resume_text}

Mandatory Skills:{', '.join(mandatory_skills)}

Optional Skills:{', '.join(optional_skills)}

Output Format:

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
    "years": "... float"
    }},
    {{
    "designation": "",
    "company": "",
    "years": "... float"
    }}
],
"matched_mandatory": [],
"missing_mandatory": [],
"matched_optional": [],
"missing_optional": [],
"total_experience": "... float"
}}

Instructions:

Extract the name, email, phone, GitHub, and LinkedIn from the resume. If LinkedIn is not provided, use an empty string.

List all skills mentioned in the resume under the "skills" field, using the exact text as it appears in the resume.

Identify experiences, including designation, company, and duration. Convert duration to years as a float (e.g., 12 months = 1.0, 5 months = 0.42).

Calculate total experience by summing the duration of all experiences in years.

Compare resume skills with mandatory and optional skills. Include implied skills (e.g., "DRF" implies "django rest framework") in matched_mandatory or matched_optional, using the exact spelling and casing from the mandatory or optional skills lists.

Output the result as a JSON object matching the specified format, with no additional text or explanations. """
    
    return promt



