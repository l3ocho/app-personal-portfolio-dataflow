"""About page - Professional narrative and background."""

import dash
import dash_mantine_components as dmc
from dash import dcc
from dash_iconify import DashIconify

dash.register_page(__name__, path="/about", name="About")

# Opening section
OPENING = """I didn't start in data. I started in project management—CAPM certified, ITIL trained, \
the whole corporate playbook. Then I realized I liked building systems more than managing timelines, \
and I was better at automating reports than attending meetings about them.

That pivot led me to where I am now: 8 years deep in data engineering, analytics, and the messy \
reality of turning raw information into something people can actually use."""

# What I Actually Do section
WHAT_I_DO_SHORT = "The short version: I build data infrastructure. Pipelines, warehouses, \
dashboards, automation—the invisible machinery that makes businesses run on data instead of gut feelings."

WHAT_I_DO_LONG = """The longer version: At Summitt Energy, I've been the sole data professional \
supporting 150+ employees across 9 markets (Canada and US). I inherited nothing—no data warehouse, \
no reporting infrastructure, no documentation. Over 5 years, I built DataFlow: an enterprise \
platform processing 1B+ rows, integrating contact center data, CRM systems, and legacy tools \
that definitely weren't designed to talk to each other.

That meant learning to be a generalist. I've done ETL pipeline development (Python, SQLAlchemy), \
dimensional modeling, dashboard design (Power BI, Plotly-Dash), API integration, and more \
stakeholder management than I'd like to admit. When you're the only data person, you learn to wear every hat."""

# How I Think About Data
DATA_PHILOSOPHY_INTRO = "I'm not interested in data for data's sake. The question I always \
start with: What decision does this help someone make?"

DATA_PHILOSOPHY_DETAIL = """Most of my work has been in operations-heavy environments—contact \
centers, energy retail, logistics. These aren't glamorous domains, but they're where data can \
have massive impact. A 30% improvement in abandon rate isn't just a metric; it's thousands of \
customers who didn't hang up frustrated. A 40% reduction in reporting time means managers can \
actually manage instead of wrestling with spreadsheets."""

DATA_PHILOSOPHY_CLOSE = "I care about outcomes, not technology stacks."

# Technical skills
TECH_SKILLS = {
    "Languages": "Python (Pandas, SQLAlchemy, FastAPI), SQL (MSSQL, PostgreSQL), R, VBA",
    "Data Engineering": "ETL/ELT pipelines, dimensional modeling (star schema), dbt patterns, batch processing, API integration, web scraping (Selenium)",
    "Visualization": "Plotly/Dash, Power BI, Tableau",
    "Platforms": "Genesys Cloud, Five9, Zoho, Azure DevOps",
    "Currently Learning": "Cloud certification (Azure DP-203), Airflow, Snowflake",
}

# Outside Work
OUTSIDE_WORK_INTRO = "I'm a Brazilian-Canadian based in Toronto. I speak Portuguese (native), \
English (fluent), and enough Spanish to survive."

OUTSIDE_WORK_ACTIVITIES = [
    "Building automation tools for small businesses through Bandit Labs (my side project)",
    "Contributing to open source (MCP servers, Claude Code plugins)",
    'Trying to explain to my kid why Daddy\'s job involves "making computers talk to each other"',
]

# What I'm Looking For
LOOKING_FOR_INTRO = "I'm currently exploring Senior Data Analyst and Data Engineer roles in \
the Toronto area (or remote). I'm most interested in:"

LOOKING_FOR_ITEMS = [
    "Companies that treat data as infrastructure, not an afterthought",
    "Teams where I can contribute to architecture decisions, not just execute tickets",
    "Operations-focused industries (energy, logistics, financial services, contact center tech)",
]

LOOKING_FOR_CLOSE = "If that sounds like your team, let's talk."


def create_section_title(title: str) -> dmc.Title:
    """Create a consistent section title."""
    return dmc.Title(title, order=2, size="h3", mb="sm")


def create_opening_section() -> dmc.Paper:
    """Create the opening/intro section."""
    paragraphs = OPENING.split("\n\n")
    return dmc.Paper(
        dmc.Stack(
            [dmc.Text(p, size="md") for p in paragraphs],
            gap="md",
        ),
        p="xl",
        radius="md",
        withBorder=True,
    )


def create_what_i_do_section() -> dmc.Paper:
    """Create the What I Actually Do section."""
    return dmc.Paper(
        dmc.Stack(
            [
                create_section_title("What I Actually Do"),
                dmc.Text(WHAT_I_DO_SHORT, size="md", fw=500),
                dmc.Text(WHAT_I_DO_LONG, size="md"),
            ],
            gap="md",
        ),
        p="xl",
        radius="md",
        withBorder=True,
    )


def create_philosophy_section() -> dmc.Paper:
    """Create the How I Think About Data section."""
    return dmc.Paper(
        dmc.Stack(
            [
                create_section_title("How I Think About Data"),
                dmc.Text(DATA_PHILOSOPHY_INTRO, size="md", fw=500),
                dmc.Text(DATA_PHILOSOPHY_DETAIL, size="md"),
                dmc.Text(DATA_PHILOSOPHY_CLOSE, size="md", fw=500, fs="italic"),
            ],
            gap="md",
        ),
        p="xl",
        radius="md",
        withBorder=True,
    )


def create_tech_section() -> dmc.Paper:
    """Create the Technical Stuff section."""
    return dmc.Paper(
        dmc.Stack(
            [
                create_section_title("The Technical Stuff"),
                dmc.Stack(
                    [
                        dmc.Group(
                            [
                                dmc.Text(category + ":", fw=600, size="sm", w=150),
                                dmc.Text(skills, size="sm", c="dimmed"),
                            ],
                            gap="sm",
                            align="flex-start",
                            wrap="nowrap",
                        )
                        for category, skills in TECH_SKILLS.items()
                    ],
                    gap="xs",
                ),
            ],
            gap="md",
        ),
        p="xl",
        radius="md",
        withBorder=True,
    )


def create_outside_work_section() -> dmc.Paper:
    """Create the Outside Work section."""
    return dmc.Paper(
        dmc.Stack(
            [
                create_section_title("Outside Work"),
                dmc.Text(OUTSIDE_WORK_INTRO, size="md"),
                dmc.Text("When I'm not staring at SQL, I'm usually:", size="md"),
                dmc.List(
                    [
                        dmc.ListItem(dmc.Text(item, size="md"))
                        for item in OUTSIDE_WORK_ACTIVITIES
                    ],
                    spacing="xs",
                ),
            ],
            gap="md",
        ),
        p="xl",
        radius="md",
        withBorder=True,
    )


def create_looking_for_section() -> dmc.Paper:
    """Create the What I'm Looking For section."""
    return dmc.Paper(
        dmc.Stack(
            [
                create_section_title("What I'm Looking For"),
                dmc.Text(LOOKING_FOR_INTRO, size="md"),
                dmc.List(
                    [
                        dmc.ListItem(dmc.Text(item, size="md"))
                        for item in LOOKING_FOR_ITEMS
                    ],
                    spacing="xs",
                ),
                dmc.Text(LOOKING_FOR_CLOSE, size="md", fw=500),
                dmc.Group(
                    [
                        dcc.Link(
                            dmc.Button(
                                "Download Resume",
                                variant="filled",
                                leftSection=DashIconify(
                                    icon="tabler:download", width=18
                                ),
                            ),
                            href="/resume",
                        ),
                        dcc.Link(
                            dmc.Button(
                                "Contact Me",
                                variant="outline",
                                leftSection=DashIconify(icon="tabler:mail", width=18),
                            ),
                            href="/contact",
                        ),
                    ],
                    gap="sm",
                    mt="md",
                ),
            ],
            gap="md",
        ),
        p="xl",
        radius="md",
        withBorder=True,
    )


layout = dmc.Container(
    dmc.Stack(
        [
            dmc.Title("About", order=1, ta="center", mb="lg"),
            create_opening_section(),
            create_what_i_do_section(),
            create_philosophy_section(),
            create_tech_section(),
            create_outside_work_section(),
            create_looking_for_section(),
            dmc.Space(h=40),
        ],
        gap="xl",
    ),
    size="md",
    py="xl",
)
