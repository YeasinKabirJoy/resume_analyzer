import ollama
import json
import re

# Resume text and skills
resume_text = """Sk. Yeasin Kabir Joy
Shuvadda Purba Para, Keraniganj, Dhaka-1310
+8801775328131
YeasinKabirJoy
yeasinjoy16@gmail.com
yeasinkabirjoy
Career Objective
A highly organized and hard-working individual seeking an opportunity to gain practical experience and contribute effectively to your development team.
Skills
• Python
• Django
• React
Other Skills
• VAPT (Information Security Assessment and Penetration Testing Certification from MIST)
Achievements
• VC Gold Medalist
• Bronze Medal International Blockchain Olympiad 2022
Experiences
1. Software Engineer
December 2024 - April 2025
Altersense Ltd.
RPA Solution
• Developed and optimized RPA solutions using Python, Django, and Selenium to automate tasks and improve efficiency in the garments’ commercial department.
2. Software Engineer
April 2023 - March 2024
Eutropia IT
SaaS Application
• Developed secure APIs with authentication for web scraping, enhancing security and access control.
• Utilized Python, Django (DRF), and BeautifulSoup for efficient data extraction. Tested API functionality with Postman, ensuring compliance and performance.
Education
2018-2022 Bsc in Computer Science & Engineering
University of Asia Pacific
CGPA: 3.95
2017 HSC
Engineering University School & College
2015 SSC
St. Gregory’s High School
Projects
Chat Application
• Developed a real-time chat app with Django, Channels, HTMX, and JavaScript, supporting messaging, group chat, and user online status.
• Used WebSockets for instant communication and scalable backend with Django Channels.
E-CHECKUP
• A real-time video conferencing feature using third-party APIs (Agora), enabling secure and direct communication between doctors and patients.
• Developed using Django, Js, Bootstrap, HTML, CSS.
References
Dr. Aloke Kumar Saha
Professor, Dept of CSE
University of Asia Pacific
aloke@uap-bd.edu
+8801711465641
Dr. A S M Touhidul Hasan
Assistant Teaching Professor
Division of Computing, Analytics and Mathematics
University of Missouri-Kansas City, USA.
ahrzd@umkc.edu
"""

mandatory_skills = ["python", "django", "django rest framework"]
optional_skills = ["docker", "postgres"]

# Your prompt
prompt = f"""Extract information from the following resume text and produce a JSON output based on the provided mandatory and optional skills and the specified format. 
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
Output the result as a JSON object matching the specified format, with no additional text or explanations.
"""

# Generate JSON output with LLaMA 3.2 3B
response = ollama.generate(
    model="deepseek-r1",
    prompt=prompt,
    options={"temperature": 0, "format": "json"}  # Enforce JSON mode
)["response"]

# Extract JSON from response
try:
    # Find JSON block
    json_match = re.search(r"```json\n([\s\S]*?)\n```", response) or re.search(r"{[\s\S]*}", response)
    if json_match:
        json_str = json_match.group(1) if json_match.group(1) else json_match.group(0)
        output = json.loads(json_str)
        print(json.dumps(output, indent=2))
    else:
        print("No JSON found in response:", response)
except json.JSONDecodeError:
    print("Invalid JSON in response:", response)