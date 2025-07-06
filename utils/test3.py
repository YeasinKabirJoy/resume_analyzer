import time
from llama_cpp import Llama
from datetime import datetime
import json
# === Configuration ===
MODEL_PATH = r"C:\Users\Lenovo\Downloads\mistral-7b-instruct-v0.1.Q4_K_M.gguf"  # Change as needed

def build_phi_prompt(resume_text: str, mandatory_skills: list, optional_skills: list) -> str:
   prompt = f"""<|system|>

You are an AI assistant that extracts structured data from resume.

Respond only with a valid JSON object. No explanation or extra text.

<|user|>
**Instructions**:
1. **Information Extraction**  
 Extract from the resume text, preserving exact text:  
 - **Name**: Full name. Set to "" if not found.  
 - **Email**: Email address. Set to "" if not found.  
 - **Phone**: Phone number. Set to "" if not found.  
 - **GitHub**: GitHub URL/username. Set to "" if not found.  
 - **LinkedIn**: LinkedIn URL/username. Set to "" if not found.  
 - **Skills**: All listed skills, **check only experiance and projects parts additionally**, preserving exact casing/spelling.  
 - **Experiences**: For each job:  
   - **Designation**: Job title.  
   - **Company**: Employer name.  #   - **Start Date**: Format as "Mon YYYY" (e.g., "Jan 2020").  
   - **End Date**: Format as "Mon YYYY" or "Present" if current.  

   # 2. **Skill Matching**  
Match extracted skills against provided lists using case-insensitive matching and alias mappings (e.g., "DRF" → "django rest framework").  
- **Mandatory Skills**: {', '.join(mandatory_skills)}  
  - Match each skill or alias to resume’s skill list.  
  - Add matches to **matched_mandatory** (use list name).  
  - Add unmatched to **missing_mandatory**.  
  - Prioritize mandatory if skill is in both lists.  
- **Optional Skills**: {', '.join(optional_skills)}  
  - Match each skill or alias to resume’s skill list, if not already matched as mandatory.  
  - Add matches to **matched_optional** (use list name).  
  - Add unmatched to **missing_optional**.  
- **Constraints**:  
  - Skills must be explicitly listed in resume’s skill list.  
  - No inferred skills.  
  - Use only provided aliases.  
  - Skills cannot be in both matched_mandatory and matched_optional.


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

  "summary": "",
}}

Resume:
{resume_text.strip()}
<|assistant|>"""
   
   return prompt

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
optional_skills = ["Docker,Postgres","PHP"]

gguf_prompt = build_phi_prompt(resume_text, mandatory_skills, optional_skills)
N_TOKENS = 2048
N_THREADS = 16  # Set based on your CPU (e.g. os.cpu_count())

# === Load Model ===
print("Loading model...")
start_load = time.time()

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=2048,
    n_threads=N_THREADS
)

load_time = time.time() - start_load
print(f"✅ Model loaded in {load_time:.2f} seconds")

# === Run Inference ===
print("Generating response...")
start_infer = time.time()

# <|user|>\n{PROMPT}</s>\n<|assistant|>
response = llm(
    prompt="hii",
    max_tokens=N_TOKENS,
    temperature=0,
)

infer_time = time.time() - start_infer
output_text = response["choices"][0]["text"]

# === Output ===
print("\n--- Output ---")
print(output_text.strip())
# print(json.loads(output_text.strip()))
print("\n--- Stats ---")
print(f"🧠 Prompt Tokens: {response['usage']['prompt_tokens']}")
print(f"✍️  Response Tokens: {response['usage']['completion_tokens']}")
print(f"⚡ Generation Time: {infer_time:.2f} seconds")
print(f"⚡ Tokens/sec: {response['usage']['completion_tokens'] / infer_time:.2f}")




