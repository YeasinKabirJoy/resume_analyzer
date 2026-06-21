from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from services.pipeline import analyze_text, process_resume
from services.rule_extractors import extract_contacts, extract_experiences, extract_name, extract_sections
from services.skill_matcher import match_skills


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
        self.assertGreater(result["text_quality_score"], 0)
        self.assertGreater(result["confidence_score"], 0)

    @patch("services.pipeline.extract_text_from_pdf", return_value="too short")
    def test_process_resume_rejects_short_text(self, mocked_extract_text):
        job_role = FakeJobRole(requirements=[FakeRequirement(FakeSkill("Python"))])
        resume_record = SimpleNamespace(
            resume=SimpleNamespace(path="fake.pdf"),
            job_role=job_role,
        )

        with self.assertRaises(ValueError):
            process_resume(resume_record)
