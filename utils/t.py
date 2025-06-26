import time
from llama_cpp import Llama

# === Configuration ===
MODEL_PATH = r"C:\lm\TheBloke\TinyLlama-1.1B-Chat-v1.0-GGUF\tinyllama-1.1b-chat-v1.0.Q6_K.gguf"  # Change as needed

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

PROMPT = f"""
You are an AI assistant that extracts structured information from resumes.

Your task: Return only a valid JSON object in the format below — with double quotes and no extra text.

Follow these instructions:

1. Extract:
   - name, email, phone, github, linkedin (use "" if missing)
   - all skills found in the resume text (exactly as they appear)
   - experiences: each with "designation", "company", and "years" (convert months to float years)
   - total_experience: sum of all durations in "years"

2. Skill Matching:
   - Match skills case-insensitively from the following lists.
   - Include both **exact matches** and **common abbreviations** (e.g., "DRF" implies "django rest framework")
   - Use the original skill names from the lists for matched skills.
   - For any unmatched skills, add them to the "missing" lists.

Mandatory Skills: {', '.join(mandatory_skills)}
Optional Skills: {', '.join(optional_skills)}

3. Output:
Respond ONLY with a valid JSON object using the format below.

Format:
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
      "years": 0.0
    }}
  ],
  "matched_mandatory": [],
  "missing_mandatory": [],
  "matched_optional": [],
  "missing_optional": [],
  "total_experience": 0.0
}}

Resume:
{resume_text}
"""

word_count = len(PROMPT.split())
print("Word count:", word_count)
print(len(PROMPT))
N_TOKENS = 1024
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

response = llm(
    prompt=f"<|user|>\n{PROMPT}</s>\n<|assistant|>",
    max_tokens=N_TOKENS,
    temperature=0,
)

infer_time = time.time() - start_infer
output_text = response["choices"][0]["text"]

# === Output ===
print("\n--- Output ---")
print(output_text.strip())

print("\n--- Stats ---")
print(f"🧠 Prompt Tokens: {response['usage']['prompt_tokens']}")
print(f"✍️  Response Tokens: {response['usage']['completion_tokens']}")
print(f"⚡ Generation Time: {infer_time:.2f} seconds")
print(f"⚡ Tokens/sec: {response['usage']['completion_tokens'] / infer_time:.2f}")