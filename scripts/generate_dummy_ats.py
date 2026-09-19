from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "dummy_ats"
OUTPUT_DIR.mkdir(exist_ok=True)


styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    "Title",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=20,
    leading=24,
    textColor=colors.HexColor("#111111"),
    alignment=TA_LEFT,
    spaceAfter=10,
)
section_style = ParagraphStyle(
    "Section",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=13,
    textColor=colors.HexColor("#111111"),
    spaceBefore=8,
    spaceAfter=4,
)
body_style = ParagraphStyle(
    "Body",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=9.5,
    leading=12,
    textColor=colors.HexColor("#111111"),
    spaceAfter=3,
)
small_style = ParagraphStyle(
    "Small",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=8.5,
    leading=10,
    textColor=colors.HexColor("#222222"),
    spaceAfter=2,
)


def build_doc(path: Path):
    doc = BaseDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])
    return doc


def para(text, style=body_style):
    return Paragraph(text, style)


def bullet_lines(items):
    return "<br/>".join(f"• {item}" for item in items)


def standard_story(person, contact_lines, summary, experience, education, skills):
    story = [para(person, title_style), para(contact_lines, small_style), Spacer(1, 0.08 * inch)]
    if summary:
        story.extend([para("SUMMARY", section_style), para(summary)])
    story.extend([para("EXPERIENCE", section_style)])
    for title, company, dates, details in experience:
        story.append(para(f"<b>{title}</b>", body_style))
        story.append(para(f"{company} | {dates}", small_style))
        story.append(para(details))
    story.extend([para("EDUCATION", section_style)])
    for degree, school, info in education:
        story.append(para(f"<b>{degree}</b>", body_style))
        story.append(para(f"{school} | {info}", small_style))
    story.extend([para("SKILLS", section_style), para(skills)])
    return story


def two_column_story(person, contact_lines, summary, experience, education, skills):
    left = [
        para(person, title_style),
        para("CONTACT", section_style),
        para(contact_lines, small_style),
        para("SKILLS", section_style),
        para(skills),
    ]
    right = [para("SUMMARY", section_style), para(summary), para("EXPERIENCE", section_style)]
    for title, company, dates, details in experience:
        right.append(para(f"<b>{title}</b>", body_style))
        right.append(para(f"{company} | {dates}", small_style))
        right.append(para(details))
    right.append(para("EDUCATION", section_style))
    for degree, school, info in education:
        right.append(para(f"<b>{degree}</b>", body_style))
        right.append(para(f"{school} | {info}", small_style))
    table = Table([[left, right]], colWidths=[2.45 * inch, 3.7 * inch])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dddddd")),
    ]))
    return [table]


def messy_story(person, contact_lines, summary, experience, education, skills):
    story = [para(person, title_style), para(contact_lines, small_style)]
    story.append(Spacer(1, 0.12 * inch))
    story.append(para("Experience", section_style))
    for item in experience:
        story.append(para(item))
    story.append(para("Education", section_style))
    for item in education:
        story.append(para(item))
    story.append(para("Skills", section_style))
    story.append(para(skills))
    return story


def create_pdf(filename, story_builder):
    doc = build_doc(OUTPUT_DIR / filename)
    story = story_builder()
    doc.build(story)


def main():
    create_pdf(
        "dummy_ats_resume_1.pdf",
        lambda: standard_story(
            "Amina Rahman",
            "Dhaka, Bangladesh",
            "Backend engineer with strong Python and Django experience building REST APIs and internal tools.",
            [
                ("Python Developer", "Nimbus Labs", "Jan 2022 - Present", "Built Django services, REST APIs, and internal automation."),
                ("Software Engineer", "BluePeak Solutions", "Jun 2019 - Dec 2021", "Worked on backend systems, PostgreSQL, and integrations."),
            ],
            [
                ("BSc in Computer Science", "University of Dhaka", "CGPA 3.74 / 4.00 | 2019"),
            ],
            "Python, Django, Django REST Framework, Docker, SQL, PostgreSQL",
        ),
    )

    create_pdf(
        "dummy_ats_missing_contact.pdf",
        lambda: standard_story(
            "Mahir Rahman",
            "Remote | LinkedIn: linkedin.com/in/mahirrahman | GitHub: github.com/mahirrahman",
            "Platform engineer focused on automation, cloud workflows, and backend delivery.",
            [
                ("Platform Engineer", "ByteForge", "Jan 2022 - Present", "Built deployment tooling and resume automation services."),
                ("Software Engineer", "CloudMinds", "Jun 2019 - Dec 2021", "Maintained backend workflows and reporting jobs."),
            ],
            [
                ("BSc in Computer Science", "North South University", "CGPA 3.72 / 4.00 | 2019"),
            ],
            "Python, Django, Docker, SQL, PostgreSQL",
        ),
    )

    create_pdf(
        "dummy_ats_contacts_full.pdf",
        lambda: standard_story(
            "Arif Hossain",
            "Email: arif.hossain@example.com | Phone: +8801712345678 | GitHub: github.com/arifhossain | LinkedIn: linkedin.com/in/arifhossain",
            "Backend engineer with product and platform experience in Django and API delivery.",
            [
                ("Backend Engineer", "Northstar Labs", "Jan 2022 - Present", "Built scalable APIs and maintained production services."),
                ("Software Engineer", "Delta Systems", "Jun 2019 - Dec 2021", "Implemented backend features and internal dashboards."),
            ],
            [
                ("BSc in Computer Science and Engineering", "University of Asia Pacific", "CGPA 3.82 / 4.00 | 2019"),
            ],
            "Python, Django, Django REST Framework, Docker, SQL, PostgreSQL",
        ),
    )

    create_pdf(
        "dummy_ats_education_heavy.pdf",
        lambda: standard_story(
            "Moumita Sultana",
            "Dhaka, Bangladesh",
            "Recent graduate with strong academic background and internship experience in Python and data work.",
            [
                ("Intern", "EduSoft", "Jan 2024 - Jun 2024", "Supported small automation tasks and documentation."),
            ],
            [
                ("BSc in Computer Science and Engineering", "BRAC University", "CGPA 3.82 / 4.00 | 2024"),
                ("HSC", "Dhaka City College", "GPA 5.00 / 5.00 | 2020"),
                ("SSC", "Viqarunnisa Noon School and College", "GPA 5.00 / 5.00 | 2018"),
            ],
            "Python, SQL, Excel, Communication",
        ),
    )

    create_pdf(
        "dummy_ats_experience_heavy.pdf",
        lambda: standard_story(
            "Rafiul Islam",
            "Dhaka, Bangladesh",
            "Senior backend engineer with long-running experience across product and platform teams.",
            [
                ("Software Engineer", "Gamma Labs", "Jan 2023 - Present", "Owned backend services and API reliability."),
                ("Software Engineer", "Gamma Labs", "Jan 2021 - Jan 2023", "Expanded Django applications and internal tooling."),
                ("Junior Developer", "Gamma Labs", "Jan 2019 - Jan 2021", "Supported backend maintenance and bug fixes."),
            ],
            [
                ("BSc in Software Engineering", "East West University", "CGPA 3.45 / 4.00 | 2019"),
            ],
            "Python, Django, Django REST Framework, Docker, SQL, Celery",
        ),
    )

    create_pdf(
        "dummy_ats_resume_4_two_column_ats.pdf",
        lambda: two_column_story(
            "Nusrat Jahan",
            "Email: nusrat@example.com\nPhone: +8801812345678\nGitHub: github.com/nusratjahan\nLinkedIn: linkedin.com/in/nusratjahan",
            "Full stack engineer with experience shipping internal tools and customer-facing web apps.",
            [
                ("Full Stack Developer", "NextWave", "Feb 2022 - Present", "Delivered features across frontend and backend systems."),
                ("Software Engineer", "OrbitSoft", "Aug 2019 - Jan 2022", "Worked on APIs, dashboards, and release support."),
            ],
            [
                ("BSc in Software Engineering", "Daffodil International University", "2021"),
            ],
            bullet_lines(["Python", "Django", "DRF", "Docker", "SQL", "React"]),
        ),
    )

    create_pdf(
        "dummy_ats_bad_edge_case.pdf",
        lambda: messy_story(
            "Farzana Islam",
            "farzana@example.com | +8801700000000",
            "Mixed formatting and noisy content to simulate a poor ATS export.",
            [
                "Lead Developer - Mosaic Systems | Jan 2020 - Jan 2024 | Built automation and managed releases.",
            ],
            [
                "BSc in CSE - Example University - 2020",
                "HSC - Example College - 2016",
                "SSC - Example School - 2014",
            ],
            "Python / Django / SQL / Docker",
        ),
    )


if __name__ == "__main__":
    main()
