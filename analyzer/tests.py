from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from services.ner_extractor import extract_educations, extract_experiences as extract_experiences_ner
from services.pipeline import analyze_text, process_resume
from services.rule_extractors import extract_contacts, extract_experiences, extract_name, extract_sections, is_date_anchor_line, parse_date_range
from services.skill_matcher import match_skills
from utils.experiance_calculate import calculate_total_experience


ATS_RESUME_TEXT = """
JANE DOE
jane.doe@example.com
+1 415-555-1234
github.com/janedoe
linkedin.com/in/janedoe

SUMMARY
Backend engineer with strong Python and Django experience.

EXPERIENCE
Software Engineer
Acme Corp
Jan 2021 - Present
Built REST APIs and worked with Django and PostgreSQL.

Junior Developer
Beta Labs
2018 - 2020
Worked on Python tooling and API development.

EDUCATION
BSc in Computer Science and Engineering
University of Asia Pacific
CGPA 3.95 / 4.00
2022

SKILLS
Python
Django
PostgreSQL
DRF
"""


class FakeSkill:
    def __init__(self, title, aliases=None):
        self.title = title
        self.aliases = aliases or []


class FakeRequirement:
    def __init__(self, skill, is_mandatory=True):
        self.skill = skill
        self.is_mandatory = is_mandatory


class FakeRequirementManager:
    def __init__(self, requirements):
        self._requirements = requirements

    def select_related(self, *args, **kwargs):
        return self

    def all(self):
        return self._requirements


class FakeJobPosting:
    def __init__(self, required_experience=2, requirements=None):
        self.required_experience = required_experience
        self.skill_requirements = FakeRequirementManager(requirements or [])


class ExtractorTests(SimpleTestCase):
    def test_extract_contacts_from_ats_resume(self):
        contacts = extract_contacts(ATS_RESUME_TEXT)

        self.assertEqual(contacts["email"], "jane.doe@example.com")
        self.assertEqual(contacts["phone"], "+1 415-555-1234")
        self.assertEqual(contacts["github"], "https://github.com/janedoe")
        self.assertEqual(contacts["linkedin"], "https://www.linkedin.com/in/janedoe")

    def test_extract_contacts_prefers_header_email_over_reference_email(self):
        template = """
        Sk. Yeasin Kabir Joy
        Backend Software Engineer
        Dhaka, Bangladesh
        yeasinjoy16@gmail.com | +8801590014090

        Reference
        Wahid Sadique Koly | Sr Software Engineer | Singularity Limited
        koly@singularitybd.com
        """

        contacts = extract_contacts(template)

        self.assertEqual(contacts["email"], "yeasinjoy16@gmail.com")

    def test_extract_sections_and_experiences(self):
        sections = extract_sections(ATS_RESUME_TEXT)
        experiences = extract_experiences(ATS_RESUME_TEXT)

        self.assertIn("experience", sections)
        self.assertIn("skills", sections)
        self.assertEqual(len(experiences), 2)
        self.assertEqual(experiences[0]["designation"], "Software Engineer")
        self.assertEqual(experiences[0]["company"], "Acme Corp")
        self.assertEqual(experiences[0]["start"], "Jan 2021")
        self.assertEqual(experiences[0]["end"], "Present")
        self.assertEqual(experiences[1]["designation"], "Junior Developer")
        self.assertEqual(experiences[1]["company"], "Beta Labs")
        self.assertEqual(experiences[1]["start"], "Jan 2018")
        self.assertEqual(experiences[1]["end"], "Jan 2020")

    def test_extracters_use_ner_first_logging(self):
        buffer = StringIO()
        with redirect_stdout(buffer):
            extract_experiences_ner(ATS_RESUME_TEXT)
            extract_educations(ATS_RESUME_TEXT)

        output = buffer.getvalue()
        self.assertIn("EXPERIENCE EXTRACTED BY: NER-FIRST", output)
        self.assertIn("EDUCATION EXTRACTED BY: NER-FIRST", output)

    def test_extract_experiences_rejects_description_as_company(self):
        text = """
        EXPERIENCE
        Python Software Engineer I
        Riseup Asia LLC.
        Jan 2023 - Mar 2024
        Conducted R&D on local AI integration, using LoRA fine-tuning and GGUF quantization to handle resource constraints.
        """

        experiences = extract_experiences(text)

        self.assertEqual(len(experiences), 1)
        self.assertEqual(experiences[0]["designation"], "Python Software Engineer I")
        self.assertEqual(experiences[0]["company"], "Riseup Asia LLC.")
        self.assertEqual(experiences[0]["start"], "Jan 2023")
        self.assertEqual(experiences[0]["end"], "Mar 2024")

    def test_extract_experiences_ner_keeps_company_clean(self):
        text = """
        EXPERIENCE
        Python Software Engineer I
        Riseup Asia LLC.
        Jan 2023 - Mar 2024
        Conducted R&D on local AI integration, using LoRA fine-tuning and GGUF quantization to handle resource constraints.
        """

        experiences = extract_experiences_ner(text)

        self.assertEqual(len(experiences), 1)
        self.assertEqual(experiences[0]["designation"], "Python Software Engineer I")
        self.assertEqual(experiences[0]["company"], "Riseup Asia LLC.")
        self.assertEqual(experiences[0]["start"], "Jan 2023")
        self.assertEqual(experiences[0]["end"], "Mar 2024")

    def test_extract_experiences_ner_keeps_single_token_company(self):
        text = """
        EXPERIENCE
        Platform Engineer
        ByteForge
        Jan 2022 - Present
        Built internal tooling and dashboards.
        """

        experiences = extract_experiences_ner(text)

        self.assertEqual(len(experiences), 1)
        self.assertEqual(experiences[0]["designation"], "Platform Engineer")
        self.assertEqual(experiences[0]["company"], "ByteForge")
        self.assertEqual(experiences[0]["start"], "Jan 2022")
        self.assertEqual(experiences[0]["end"], "Present")

    def test_extract_experiences_ner_recovers_company_from_anchor_line(self):
        text = """
        EXPERIENCE
        Python Developer
        Nimbus Labs | Jan 2022 - Present
        Built internal tooling and dashboards.
        """

        experiences = extract_experiences_ner(text)

        self.assertEqual(len(experiences), 1)
        self.assertEqual(experiences[0]["designation"], "Python Developer")
        self.assertEqual(experiences[0]["company"], "Nimbus Labs")
        self.assertEqual(experiences[0]["start"], "Jan 2022")
        self.assertEqual(experiences[0]["end"], "Present")

    def test_extract_experiences_ner_rejects_description_as_company(self):
        text = """
        EXPERIENCE
        Lead Developer
        Jan 2022 - Present
        Built internal tooling and dashboards.
        """

        experiences = extract_experiences_ner(text)

        self.assertEqual(len(experiences), 1)
        self.assertEqual(experiences[0]["designation"], "Lead Developer")
        self.assertEqual(experiences[0]["company"], "")
        self.assertEqual(experiences[0]["start"], "Jan 2022")
        self.assertEqual(experiences[0]["end"], "Present")

    def test_extract_experiences_keeps_company_empty_when_unclear(self):
        text = """
        EXPERIENCE
        Lead Developer
        Jan 2022 - Present
        Built internal tooling and dashboards.
        """

        experiences = extract_experiences(text)

        self.assertEqual(len(experiences), 1)
        self.assertEqual(experiences[0]["designation"], "Lead Developer")
        self.assertEqual(experiences[0]["company"], "")
        self.assertEqual(experiences[0]["start"], "Jan 2022")
        self.assertEqual(experiences[0]["end"], "Present")

    def test_extract_experiences_splits_mixed_title_and_company(self):
        text = """
        EXPERIENCE
        Python Developer - Nimbus Labs
        Jan 2021 - Present
        Built REST APIs and Django services.
        """

        experiences = extract_experiences(text)

        self.assertEqual(len(experiences), 1)
        self.assertEqual(experiences[0]["designation"], "Python Developer")
        self.assertEqual(experiences[0]["company"], "Nimbus Labs")
        self.assertEqual(experiences[0]["start"], "Jan 2021")
        self.assertEqual(experiences[0]["end"], "Present")

    def test_extract_educations(self):
        educations = extract_educations(ATS_RESUME_TEXT)

        self.assertTrue(educations)
        self.assertEqual(educations[0]["institution"], "University of Asia Pacific")
        self.assertIn("Computer Science", educations[0]["degree"])
        self.assertIn("3.95", educations[0]["result"])

    def test_extract_ner_records_avoid_duplicate_line_pairing(self):
        text = """
        EXPERIENCE
        Python Software Engineer I
        Eutropia IT
        Jan 2023 - Mar 2024
        Built AI tooling and automation.

        EDUCATION
        BSc in Computer Science and Engineering
        University of Asia Pacific
        CGPA 3.95 / 4.00
        2022
        """

        experiences = extract_experiences(text)
        educations = extract_educations(text)

        self.assertEqual(len(experiences), 1)
        self.assertEqual(experiences[0]["designation"], "Python Software Engineer I")
        self.assertEqual(experiences[0]["company"], "Eutropia IT")
        self.assertEqual(experiences[0]["start"], "Jan 2023")
        self.assertEqual(experiences[0]["end"], "Mar 2024")

        self.assertEqual(len(educations), 1)
        self.assertEqual(educations[0]["degree"], "BSc in Computer Science and Engineering")
        self.assertEqual(educations[0]["institution"], "University of Asia Pacific")
        self.assertIn("CGPA", educations[0]["result"])
        self.assertEqual(educations[0]["year"], "2022")

    def test_extract_ner_records_ignore_description_as_company(self):
        text = """
        EXPERIENCE
        Python Software Engineer I
        Riseup Asia LLC.
        Jan 2023 - Mar 2024
        Conducted R&D on local AI integration, using LoRA fine-tuning and GGUF quantization to handle resource constraints.

        EDUCATION
        BSc in Computer Science and Engineering
        University of Asia Pacific
        CGPA: 3.95 / 4.00
        2022
        """

        experiences = extract_experiences(text)
        educations = extract_educations(text)

        self.assertEqual(experiences[0]["company"], "Riseup Asia LLC.")
        self.assertEqual(educations[0]["institution"], "University of Asia Pacific")

    def test_extract_ner_records_handle_school_credentials(self):
        text = """
        EDUCATION
        Engineering University School and College at Higher Secondary Certificate (HSC) (CGPA: 3.95 / 4.00)
        Engineering University School and College at Secondary School Certificate (SSC) (GPA: 5.00 / 5.00)
        """

        educations = extract_educations(text)

        self.assertGreaterEqual(len(educations), 2)
        self.assertEqual(educations[0]["institution"], "Engineering University School and College")
        self.assertIn("Higher Secondary Certificate", educations[0]["degree"])
        self.assertEqual(educations[1]["institution"], "Engineering University School and College")
        self.assertIn("Secondary School Certificate", educations[1]["degree"])

    def test_extract_educations_ner_keeps_degree_and_institution_clean(self):
        text = """
        EDUCATION
        BSc in Computer Science and Engineering
        University of Asia Pacific
        CGPA 3.95 / 4.00
        2019
        """

        educations = extract_educations(text)

        self.assertEqual(len(educations), 1)
        self.assertEqual(educations[0]["degree"], "BSc in Computer Science and Engineering")
        self.assertEqual(educations[0]["institution"], "University of Asia Pacific")
        self.assertIn("CGPA", educations[0]["result"])
        self.assertEqual(educations[0]["year"], "2019")

    def test_extract_educations_rejects_result_as_degree(self):
        text = """
        EDUCATION
        GPA: 5.00 / 5.00 at St. Gregory’s High School
        Secondary School Certificate (SSC)
        """

        educations = extract_educations(text)

        self.assertTrue(educations)
        for education in educations:
            self.assertNotIn("GPA", education["degree"])

    def test_extract_educations_handles_degree_institution_result_year_line(self):
        text = """
        EDUCATION
        BSc in Computer Science and Engineering - BRAC University (CGPA 3.82 / 4.00) - 2024
        HSC - Dhaka City College (GPA 5.00 / 5.00) - 2020
        SSC - Viqarunnisa Noon School and College (GPA 5.00 / 5.00) - 2018
        """

        educations = extract_educations(text)

        self.assertGreaterEqual(len(educations), 3)
        self.assertEqual(educations[0]["degree"], "BSc in Computer Science and Engineering")
        self.assertEqual(educations[0]["institution"], "BRAC University")
        self.assertIn("CGPA", educations[0]["result"])
        self.assertEqual(educations[0]["year"], "2024")
        self.assertEqual(educations[1]["institution"], "Dhaka City College")
        self.assertEqual(educations[1]["year"], "2020")
        self.assertEqual(educations[2]["institution"], "Viqarunnisa Noon School and College")
        self.assertEqual(educations[2]["year"], "2018")

    def test_extract_educations_strips_trailing_separators(self):
        text = """
        EDUCATION
        BSc in Software Engineering
        Daffodil International University |
        CGPA 3.82 / 4.00
        2021
        """

        educations = extract_educations(text)

        self.assertEqual(len(educations), 1)
        self.assertEqual(educations[0]["institution"], "Daffodil International University")
        self.assertEqual(educations[0]["year"], "2021")

    def test_extract_experiences_supports_template_dates(self):
        template_text = """
        Work Experience
        Sep-07 - Aug-10
        Official Company Name
        City, Country
        Job title
        """

        experiences = extract_experiences(template_text)
        self.assertEqual(len(experiences), 1)
        self.assertEqual(experiences[0]["start"], "Sep 2007")
        self.assertEqual(experiences[0]["end"], "Aug 2010")

    def test_date_anchor_detection_handles_multiple_formats(self):
        self.assertTrue(is_date_anchor_line("Jan 2022 - Present"))
        self.assertTrue(is_date_anchor_line("2018 - 2020"))
        self.assertTrue(is_date_anchor_line("Sep 07 to Aug 10"))
        self.assertTrue(is_date_anchor_line("Present"))

        parsed = parse_date_range("Jan 2022 – Present")
        self.assertEqual(parsed["start"], "Jan 2022")
        self.assertEqual(parsed["end"], "Present")

    def test_extract_name_prefers_header_line(self):
        name = extract_name(ATS_RESUME_TEXT)

        self.assertEqual(name, "Jane Doe")

    def test_skill_matching_uses_aliases(self):
        mandatory_skills = [FakeSkill("Python"), FakeSkill("Django")]
        optional_skills = [FakeSkill("Django REST Framework", aliases=["drf"])]

        result = match_skills(ATS_RESUME_TEXT, mandatory_skills, optional_skills)

        self.assertEqual(result["matched_mandatory"], ["Python", "Django"])
        self.assertEqual(result["matched_optional"], ["Django REST Framework"])
        self.assertEqual(result["missing_optional"], [])
        self.assertIn("Django REST Framework", result["skills"])


class PipelineTests(SimpleTestCase):
    def test_analyze_text_returns_structured_result(self):
        requirements = [
            FakeRequirement(FakeSkill("Python"), is_mandatory=True),
            FakeRequirement(FakeSkill("Django"), is_mandatory=True),
            FakeRequirement(FakeSkill("Django REST Framework", aliases=["drf"]), is_mandatory=False),
        ]
        job_posting = FakeJobPosting(required_experience=1, requirements=requirements)

        result = analyze_text(ATS_RESUME_TEXT, job_posting)

        self.assertEqual(result["name"], "Jane Doe")
        self.assertEqual(result["email"], "jane.doe@example.com")
        self.assertEqual(result["matched_mandatory_skills"], ["Python", "Django"])
        self.assertEqual(result["matched_optional_skills"], ["Django REST Framework"])
        self.assertEqual(len(result["experiences"]), 2)
        self.assertTrue(result["educations"])
        self.assertGreater(result["text_quality_score"], 0)
        self.assertGreater(result["confidence_score"], 0)

    @patch("services.pipeline.extract_text_from_pdf", return_value="too short")
    def test_process_resume_handles_short_text(self, mocked_extract_text):
        job_posting = FakeJobPosting(requirements=[FakeRequirement(FakeSkill("Python"))])
        resume_record = SimpleNamespace(
            resume=SimpleNamespace(path="fake.pdf"),
            job_posting=job_posting,
        )

        result = process_resume(resume_record)

        self.assertEqual(result["name"], "")
        self.assertEqual(result["email"], "")
        self.assertEqual(result["skills"], [])
        self.assertEqual(result["matched_mandatory_skills"], [])
        self.assertEqual(result["matched_optional_skills"], [])
        self.assertEqual(result["verdict"], "skipped")

    def test_calculate_total_experience_tolerates_mixed_date_formats(self):
        experiences = [
            {"start": "Sep 2007", "end": "Aug 2010"},
            {"start": "2018", "end": "2020"},
            {"start": "", "end": ""},
        ]

        total_years, per_role_years = calculate_total_experience(experiences)

        self.assertGreater(total_years, 0)
        self.assertEqual(len(per_role_years), 3)


class FormatMatrixTests(SimpleTestCase):
    def test_education_format_a_multiline(self):
        text = """
        EDUCATION
        BSc in Computer Science
        University of Dhaka
        2019
        """
        edus = extract_educations(text)
        self.assertEqual(len(edus), 1)
        self.assertEqual(edus[0]["degree"], "BSc in Computer Science")
        self.assertEqual(edus[0]["institution"], "University of Dhaka")
        self.assertEqual(edus[0]["year"], "2019")

    def test_education_format_b_hyphen_separated(self):
        text = """
        EDUCATION
        BSc in Computer Science - University of Dhaka - 2019
        """
        edus = extract_educations(text)
        self.assertEqual(len(edus), 1)
        self.assertEqual(edus[0]["degree"], "BSc in Computer Science")
        self.assertEqual(edus[0]["institution"], "University of Dhaka")
        self.assertEqual(edus[0]["year"], "2019")

    def test_education_format_c_pipe_reversed(self):
        text = """
        EDUCATION
        University of Dhaka | BSc in Computer Science | 2019
        """
        edus = extract_educations(text)
        self.assertEqual(len(edus), 1)
        self.assertEqual(edus[0]["degree"], "BSc in Computer Science")
        self.assertEqual(edus[0]["institution"], "University of Dhaka")
        self.assertEqual(edus[0]["year"], "2019")

    def test_education_format_d_with_gpa(self):
        text = """
        EDUCATION
        BSc in Computer Science
        University of Dhaka
        CGPA: 3.82 / 4.00
        2019
        """
        edus = extract_educations(text)
        self.assertEqual(len(edus), 1)
        self.assertEqual(edus[0]["degree"], "BSc in Computer Science")
        self.assertEqual(edus[0]["institution"], "University of Dhaka")
        self.assertIn("3.82", edus[0]["result"])
        self.assertEqual(edus[0]["year"], "2019")

    def test_education_format_e_date_range(self):
        text = """
        EDUCATION
        University of Dhaka
        Bachelor of Science in Computer Science
        2015 - 2019
        """
        edus = extract_educations(text)
        self.assertEqual(len(edus), 1)
        self.assertEqual(edus[0]["degree"], "Bachelor of Science in Computer Science")
        self.assertEqual(edus[0]["institution"], "University of Dhaka")
        self.assertEqual(edus[0]["start"], "2015")
        self.assertEqual(edus[0]["end"], "2019")

    def test_education_format_f_parentheses(self):
        text = """
        EDUCATION
        BSc in CSE - BRAC University (2019)
        """
        edus = extract_educations(text)
        self.assertEqual(len(edus), 1)
        self.assertIn("BSc in CSE", edus[0]["degree"])
        self.assertEqual(edus[0]["institution"], "BRAC University")
        self.assertEqual(edus[0]["year"], "2019")

    def test_education_user_reported_failing_case(self):
        text = """
        EDUCATION
        BSc in Computer Science
        University of Dhaka | CGPA 3.74 / 4.00 | 2019
        """
        edus = extract_educations(text)
        self.assertEqual(len(edus), 1)
        self.assertEqual(edus[0]["degree"], "BSc in Computer Science")
        self.assertEqual(edus[0]["institution"], "University of Dhaka")
        self.assertIn("3.74", edus[0]["result"])
        self.assertEqual(edus[0]["year"], "2019")
        self.assertGreaterEqual(edus[0]["confidence"], 0.85)

    def test_education_expected_graduation(self):
        text = """
        EDUCATION
        BSc in Computer Science
        University of Dhaka
        Expected 2026
        """
        edus = extract_educations(text)
        self.assertEqual(len(edus), 1)
        self.assertEqual(edus[0]["end"], "2026")

    def test_experience_single_line_record(self):
        text = """
        EXPERIENCE
        Lead Developer - Mosaic Systems | Jan 2020 - Jan 2024 | Built automation and managed releases.
        """
        exps = extract_experiences(text)
        self.assertEqual(len(exps), 1)
        self.assertEqual(exps[0]["designation"], "Lead Developer")
        self.assertEqual(exps[0]["company"], "Mosaic Systems")
        self.assertEqual(exps[0]["start"], "Jan 2020")
        self.assertEqual(exps[0]["end"], "Jan 2024")


class DummyAtsPdfTests(SimpleTestCase):
    def test_all_dummy_ats_resumes_extract_cleanly(self):
        import glob
        from pathlib import Path
        from utils.pdf_parser import extract_text_from_pdf

        pdf_files = sorted(glob.glob("dummy_ats/*.pdf"))
        self.assertGreaterEqual(len(pdf_files), 7)

        for pdf_path in pdf_files:
            with self.subTest(pdf=pdf_path):
                text = extract_text_from_pdf(pdf_path)
                self.assertTrue(text)
                edus = extract_educations(text)
                exps = extract_experiences(text)

                self.assertGreater(len(edus), 0, f"No educations extracted from {pdf_path}")
                for edu in edus:
                    self.assertTrue(edu["degree"] or edu["institution"])
                    self.assertIn("confidence", edu)
                    self.assertIn("evidence", edu)

                filename = Path(pdf_path).name
                if filename != "dummy_ats_bad_edge_case.pdf":
                    self.assertGreater(len(exps), 0, f"No experiences extracted from {pdf_path}")
                else:
                    self.assertGreaterEqual(len(exps), 1)
