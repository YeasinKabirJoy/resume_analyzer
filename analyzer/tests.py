from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from services.ner_extractor import extract_educations, extract_experiences as extract_experiences_ner
from services.pipeline import analyze_text, process_resume
from services.rule_extractors import extract_contacts, extract_experiences, extract_name, extract_sections
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


class FakeJobRole:
    def __init__(self, minimum_experience=2, requirements=None):
        self.minimum_experience = minimum_experience
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
        job_role = FakeJobRole(minimum_experience=1, requirements=requirements)

        result = analyze_text(ATS_RESUME_TEXT, job_role)

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
        job_role = FakeJobRole(requirements=[FakeRequirement(FakeSkill("Python"))])
        resume_record = SimpleNamespace(
            resume=SimpleNamespace(path="fake.pdf"),
            job_role=job_role,
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
