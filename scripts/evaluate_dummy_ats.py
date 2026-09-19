import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "resume_analyzer.settings")

import django
django.setup()

from utils.pdf_parser import extract_text_from_pdf
from services.ner_extractor import extract_educations, extract_experiences
from services.rule_extractors import extract_name

GROUND_TRUTH = {
    "dummy_ats_resume_1.pdf": {
        "name": "Amina Rahman",
        "educations": [
            {"institution": "University of Dhaka", "degree": "BSc in Computer Science", "year": "2019"}
        ],
        "experiences": [
            {"company": "Nimbus Labs", "designation": "Python Developer"},
            {"company": "BluePeak Solutions", "designation": "Software Engineer"},
        ],
    },
    "dummy_ats_missing_contact.pdf": {
        "name": "Mahir Rahman",
        "educations": [
            {"institution": "North South University", "degree": "BSc in Computer Science", "year": "2019"}
        ],
        "experiences": [
            {"company": "ByteForge", "designation": "Platform Engineer"},
            {"company": "CloudMinds", "designation": "Software Engineer"},
        ],
    },
    "dummy_ats_contacts_full.pdf": {
        "name": "Arif Hossain",
        "email": "arif.hossain@example.com",
        "phone": "+8801712345678",
        "educations": [
            {"institution": "University of Asia Pacific", "degree": "BSc in Computer Science and Engineering", "year": "2019"}
        ],
        "experiences": [
            {"company": "Northstar Labs", "designation": "Backend Engineer"},
            {"company": "Delta Systems", "designation": "Software Engineer"},
        ],
    },
    "dummy_ats_education_heavy.pdf": {
        "name": "Moumita Sultana",
        "educations": [
            {"institution": "BRAC University", "degree": "BSc in Computer Science and Engineering", "year": "2024"},
            {"institution": "Dhaka City College", "degree": "HSC", "year": "2020"},
            {"institution": "Viqarunnisa Noon School and College", "degree": "SSC", "year": "2018"},
        ],
        "experiences": [
            {"company": "EduSoft", "designation": "Intern"},
        ],
    },
    "dummy_ats_experience_heavy.pdf": {
        "name": "Rafiul Islam",
        "educations": [
            {"institution": "East West University", "degree": "BSc in Software Engineering", "year": "2019"}
        ],
        "experiences": [
            {"company": "Gamma Labs", "designation": "Software Engineer"},
            {"company": "Gamma Labs", "designation": "Software Engineer"},
            {"company": "Gamma Labs", "designation": "Junior Developer"},
        ],
    },
    "dummy_ats_resume_4_two_column_ats.pdf": {
        "name": "Nusrat Jahan",
        "email": "nusrat@example.com",
        "phone": "+8801812345678",
        "educations": [
            {"institution": "Daffodil International University", "degree": "BSc in Software Engineering", "year": "2021"}
        ],
        "experiences": [
            {"company": "NextWave", "designation": "Full Stack Developer"},
            {"company": "OrbitSoft", "designation": "Software Engineer"},
        ],
    },
    "dummy_ats_bad_edge_case.pdf": {
        "name": "Farzana Islam",
        "email": "farzana@example.com",
        "phone": "+8801700000000",
        "educations": [
            {"institution": "Example University", "degree": "BSc in CSE", "year": "2020"},
            {"institution": "Example College", "degree": "HSC", "year": "2016"},
            {"institution": "Example School", "degree": "SSC", "year": "2014"},
        ],
        "experiences": [
            {"company": "Mosaic Systems", "designation": "Lead Developer"},
        ],
    },
}

def fuzzy_match(expected: str, actual: str) -> bool:
    if not expected or not actual:
        return False
    e = expected.lower().strip()
    a = actual.lower().strip()
    return e in a or a in e

def evaluate():
    ats_dir = ROOT / "dummy_ats"
    if not ats_dir.exists():
        print(f"Directory {ats_dir} does not exist.")
        return

    edu_tp, edu_fp, edu_fn = 0, 0, 0
    exp_tp, exp_fp, exp_fn = 0, 0, 0
    name_correct = 0
    total_resumes = len(GROUND_TRUTH)

    print("=" * 80)
    print("                      DUMMY ATS BENCHMARK EVALUATION")
    print("=" * 80)

    for pdf_name, truth in GROUND_TRUTH.items():
        pdf_path = ats_dir / pdf_name
        if not pdf_path.exists():
            print(f"Skipping {pdf_name}: file not found")
            continue

        text = extract_text_from_pdf(str(pdf_path))
        extracted_name = extract_name(text)
        extracted_edus = extract_educations(text)
        extracted_exps = extract_experiences(text)

        name_match = fuzzy_match(truth["name"], extracted_name)
        if name_match:
            name_correct += 1

        matched_truth_edu = set()
        for ext in extracted_edus:
            ext_inst = ext.get("institution", "")
            ext_deg = ext.get("degree", "")
            match_found = False
            for idx, gt in enumerate(truth["educations"]):
                if idx not in matched_truth_edu:
                    if fuzzy_match(gt["institution"], ext_inst) or (gt.get("degree") and fuzzy_match(gt["degree"], ext_deg)):
                        matched_truth_edu.add(idx)
                        match_found = True
                        edu_tp += 1
                        break
            if not match_found:
                edu_fp += 1
        edu_fn += len(truth["educations"]) - len(matched_truth_edu)

        matched_truth_exp = set()
        for ext in extracted_exps:
            ext_comp = ext.get("company", "")
            ext_desig = ext.get("designation", "")
            match_found = False
            for idx, gt in enumerate(truth["experiences"]):
                if idx not in matched_truth_exp:
                    if fuzzy_match(gt["company"], ext_comp) or fuzzy_match(gt["designation"], ext_desig):
                        matched_truth_exp.add(idx)
                        match_found = True
                        exp_tp += 1
                        break
            if not match_found:
                exp_fp += 1
        exp_fn += len(truth["experiences"]) - len(matched_truth_exp)

        status_name = "OK" if name_match else "MISMATCH"
        print(f"\n[+] {pdf_name}")
        print(f"    Name:        {status_name} (\"{extracted_name}\" vs \"{truth['name']}\")")
        print(f"    Educations:  Found {len(extracted_edus)} (Expected {len(truth['educations'])})")
        for e in extracted_edus:
            res_str = f" [Result: {e.get('result')}]" if e.get('result') else ""
            date_str = f" [{e.get('start', '')} - {e.get('end', e.get('year', ''))}]"
            print(f"       - {e.get('degree')} @ {e.get('institution')}{date_str}{res_str}")
        print(f"    Experiences: Found {len(extracted_exps)} (Expected {len(truth['experiences'])})")
        for x in extracted_exps:
            print(f"       - {x.get('designation')} @ {x.get('company')} [{x.get('start')} - {x.get('end')}]")

    def calc_metrics(tp, fp, fn):
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        return prec, rec, f1

    edu_p, edu_r, edu_f1 = calc_metrics(edu_tp, edu_fp, edu_fn)
    exp_p, exp_r, exp_f1 = calc_metrics(exp_tp, exp_fp, exp_fn)

    print("\n" + "=" * 80)
    print("                            EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Candidate Name Accuracy: {name_correct}/{total_resumes} ({name_correct/total_resumes*100:.1f}%)")
    print(f"Education Extraction:   Precision: {edu_p*100:5.1f}% | Recall: {edu_r*100:5.1f}% | F1: {edu_f1*100:5.1f}%  (TP={edu_tp}, FP={edu_fp}, FN={edu_fn})")
    print(f"Experience Extraction:  Precision: {exp_p*100:5.1f}% | Recall: {exp_r*100:5.1f}% | F1: {exp_f1*100:5.1f}%  (TP={exp_tp}, FP={exp_fp}, FN={exp_fn})")
    print("=" * 80)

if __name__ == "__main__":
    evaluate()
