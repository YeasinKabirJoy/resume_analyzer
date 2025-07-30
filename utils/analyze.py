import time
from llama_cpp import Llama
from datetime import datetime
import json
from .llm_promt import build_gguf_resume_prompt
import os

# === Configuration ===
MODEL_PATH = r"models/Llama-3.2-3B-Instruct-UD-Q6_K_XL.gguf" # Change as needed

def analyze_resume(resume_text, mandatory_skills, optional_skills):
    gguf_prompt = build_gguf_resume_prompt(resume_text, mandatory_skills, optional_skills)

    N_TOKENS = 1024
    
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=2048,        
        n_threads=os.cpu_count(),       
        n_batch=64,        
        use_mlock=True,    
        use_mmap=True, 
    )

    print("Generating response...")
    start_infer = time.time()

    response = llm(
        prompt=gguf_prompt,
        max_tokens=N_TOKENS,
        temperature=0,
    )

    infer_time = time.time() - start_infer
    output_text = response["choices"][0]["text"]

    # === Output ===
    response_dict = json.loads(output_text.strip())

    print("\n--- Stats ---")
    print(f"🧠 Prompt Tokens: {response['usage']['prompt_tokens']}")
    print(f"✍️  Response Tokens: {response['usage']['completion_tokens']}")
    print(f"⚡ Generation Time: {infer_time:.2f} seconds")
    print(f"⚡ Tokens/sec: {response['usage']['completion_tokens'] / infer_time:.2f}")

    return response_dict