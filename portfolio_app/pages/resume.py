"""Resume page - Inline display with download options."""

from typing import Any

import dash
import dash_mantine_components as dmc
from dash_iconify import DashIconify

dash.register_page(__name__, path="/resume", name="Resume")

# =============================================================================
# HUMAN TASK: Upload resume content via Gitea
# Replace the placeholder content below with actual resume data.
# You can upload PDF/DOCX files to portfolio_app/assets/resume/
# =============================================================================

# Resume sections - replace with actual content
RESUME_HEADER = {
    "name": "Leo Miranda",
    "title": "Data Engineer & Analytics Specialist",
    "location": "Toronto, ON, Canada",
    "email": "leobrmi@hotmail.com",
    "phone": "(416) 859-7936",
    "linkedin": "linkedin.com/in/leobmiranda",
    "github": "github.com/l3ocho",
}

RESUME_SUMMARY = (
    "Data Engineer with 8 years of experience building enterprise analytics platforms, "
    "ETL pipelines, and business intelligence solutions. Proven track record of delivering "
    "40% efficiency gains through automation and data infrastructure modernization. "
    "Expert in Python, SQL, and dimensional modeling with deep domain expertise in "
    "contact center operations and energy retail."
)

# Experience - placeholder structure
EXPERIENCE = [
    {
        "title": "Senior Data Analyst / Data Engineer",
        "company": "Summitt Energy",
        "location": "Toronto, ON",
        "period": "2019 - Present",
        "highlights": [
            "Built DataFlow platform from scratch: 21 tables, 1B+ rows, processing 5,000+ daily transactions",
            "Achieved 40% improvement in reporting efficiency through automated ETL pipelines",
            "Reduced call abandon rate by 30% via KPI framework and real-time dashboards",
            "Sole data professional supporting 150+ employees across 9 markets (Canada + US)",
        ],
    },
    {
        "title": "IT Project Coordinator",
        "company": "Petrobras",
        "location": "Rio de Janeiro, Brazil",
        "period": "2015 - 2018",
        "highlights": [
            "Coordinated IT infrastructure projects for Fortune 500 energy company",
            "Managed vendor relationships and project timelines",
            "Developed reporting automation reducing manual effort by 60%",
        ],
    },
    {
        "title": "Project Management Associate",
        "company": "Project Management Institute",
        "location": "Remote",
        "period": "2014 - 2015",
        "highlights": [
            "Supported global project management standards development",
            "CAPM and ITIL certified during this period",
        ],
    },
]

# Skills - organized by category
SKILLS = {
    "Languages": ["Python", "SQL", "R", "VBA"],
    "Data Engineering": [
        "ETL/ELT Pipelines",
        "Dimensional Modeling",
        "dbt",
        "SQLAlchemy",
        "FastAPI",
    ],
    "Databases": ["PostgreSQL", "MSSQL", "Redis"],
    "Visualization": ["Plotly/Dash", "Power BI", "Tableau"],
    "Platforms": ["Genesys Cloud", "Five9", "Zoho CRM", "Azure DevOps"],
    "Currently Learning": ["Azure DP-203", "Airflow", "Snowflake"],
}

# Education
EDUCATION = [
    {
        "degree": "Bachelor of Business Administration",
        "school": "Universidade Federal do Rio de Janeiro",
        "year": "2014",
    },
]

# Certifications
CERTIFICATIONS = [
    "CAPM (Certified Associate in Project Management)",
    "ITIL Foundation",
    "Azure DP-203 (In Progress)",
]


def create_header_section() -> dmc.Paper:
    """Create the resume header with contact info."""
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Title(RESUME_HEADER["name"], order=1, ta="center"),
                dmc.Text(RESUME_HEADER["title"], size="xl", c="dimmed", ta="center"),
                dmc.Divider(my="sm"),
                dmc.Group(
                    [
                        dmc.Group(
                            [
                                DashIconify(icon="tabler:map-pin", width=16),
                                dmc.Text(RESUME_HEADER["location"], size="sm"),
                            ],
                            gap="xs",
                        ),
                        dmc.Group(
                            [
                                DashIconify(icon="tabler:mail", width=16),
                                dmc.Text(RESUME_HEADER["email"], size="sm"),
                            ],
                            gap="xs",
                        ),
                        dmc.Group(
                            [
                                DashIconify(icon="tabler:phone", width=16),
                                dmc.Text(RESUME_HEADER["phone"], size="sm"),
                            ],
                            gap="xs",
                        ),
                    ],
                    justify="center",
                    gap="lg",
                    wrap="wrap",
                ),
                dmc.Group(
                    [
                        dmc.Anchor(
                            dmc.Group(
                                [
                                    DashIconify(icon="tabler:brand-linkedin", width=16),
                                    dmc.Text("LinkedIn", size="sm"),
                                ],
                                gap="xs",
                            ),
                            href=f"https://{RESUME_HEADER['linkedin']}",
                            target="_blank",
                        ),
                        dmc.Anchor(
                            dmc.Group(
                                [
                                    DashIconify(icon="tabler:brand-github", width=16),
                                    dmc.Text("GitHub", size="sm"),
                                ],
                                gap="xs",
                            ),
                            href=f"https://{RESUME_HEADER['github']}",
                            target="_blank",
                        ),
                    ],
                    justify="center",
                    gap="lg",
                ),
            ],
            gap="sm",
        ),
        p="xl",
        radius="md",
        withBorder=True,
    )


def create_download_section() -> dmc.Group:
    """Create download buttons for resume files."""
    # Note: Buttons disabled until files are uploaded
    return dmc.Group(
        [
            dmc.Button(
                "Download PDF",
                variant="filled",
                leftSection=DashIconify(icon="tabler:file-type-pdf", width=18),
                disabled=True,  # Enable after uploading resume.pdf to assets
            ),
            dmc.Button(
                "Download DOCX",
                variant="outline",
                leftSection=DashIconify(icon="tabler:file-type-docx", width=18),
                disabled=True,  # Enable after uploading resume.docx to assets
            ),
            dmc.Anchor(
                dmc.Button(
                    "View on LinkedIn",
                    variant="subtle",
                    leftSection=DashIconify(icon="tabler:brand-linkedin", width=18),
                ),
                href=f"https://{RESUME_HEADER['linkedin']}",
                target="_blank",
            ),
        ],
        justify="center",
        gap="md",
    )


def create_summary_section() -> dmc.Paper:
    """Create the professional summary section."""
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Title("Professional Summary", order=2, size="h4"),
                dmc.Text(RESUME_SUMMARY, size="md"),
            ],
            gap="sm",
        ),
        p="lg",
        radius="md",
        withBorder=True,
    )


def create_experience_item(exp: dict[str, Any]) -> dmc.Stack:
    """Create a single experience entry."""
    return dmc.Stack(
        [
            dmc.Group(
                [
                    dmc.Text(exp["title"], fw=600),
                    dmc.Text(exp["period"], size="sm", c="dimmed"),
                ],
                justify="space-between",
            ),
            dmc.Text(f"{exp['company']} | {exp['location']}", size="sm", c="dimmed"),
            dmc.List(
                [dmc.ListItem(dmc.Text(h, size="sm")) for h in exp["highlights"]],
                spacing="xs",
                size="sm",
            ),
        ],
        gap="xs",
    )


def create_experience_section() -> dmc.Paper:
    """Create the experience section."""
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Title("Experience", order=2, size="h4"),
                *[create_experience_item(exp) for exp in EXPERIENCE],
            ],
            gap="lg",
        ),
        p="lg",
        radius="md",
        withBorder=True,
    )


def create_skills_section() -> dmc.Paper:
    """Create the skills section with badges."""
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Title("Skills", order=2, size="h4"),
                dmc.SimpleGrid(
                    [
                        dmc.Stack(
                            [
                                dmc.Text(category, fw=600, size="sm"),
                                dmc.Group(
                                    [
                                        dmc.Badge(skill, variant="light", size="sm")
                                        for skill in skills
                                    ],
                                    gap="xs",
                                ),
                            ],
                            gap="xs",
                        )
                        for category, skills in SKILLS.items()
                    ],
                    cols={"base": 1, "sm": 2},
                    spacing="md",
                ),
            ],
            gap="md",
        ),
        p="lg",
        radius="md",
        withBorder=True,
    )


def create_education_section() -> dmc.Paper:
    """Create education and certifications section."""
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Title("Education & Certifications", order=2, size="h4"),
                dmc.Stack(
                    [
                        dmc.Stack(
                            [
                                dmc.Text(edu["degree"], fw=600),
                                dmc.Text(
                                    f"{edu['school']} | {edu['year']}",
                                    size="sm",
                                    c="dimmed",
                                ),
                            ],
                            gap=0,
                        )
                        for edu in EDUCATION
                    ],
                    gap="sm",
                ),
                dmc.Divider(my="sm"),
                dmc.Group(
                    [
                        dmc.Badge(cert, variant="outline", size="md")
                        for cert in CERTIFICATIONS
                    ],
                    gap="xs",
                ),
            ],
            gap="md",
        ),
        p="lg",
        radius="md",
        withBorder=True,
    )


layout = dmc.Container(
    dmc.Stack(
        [
            create_header_section(),
            create_download_section(),
            dmc.Alert(
                "Resume files (PDF/DOCX) will be available for download once uploaded. "
                "The inline content below is a preview.",
                title="Downloads Coming Soon",
                color="blue",
                variant="light",
            ),
            create_summary_section(),
            create_experience_section(),
            create_skills_section(),
            create_education_section(),
            dmc.Space(h=40),
        ],
        gap="lg",
    ),
    size="md",
    py="xl",
)
