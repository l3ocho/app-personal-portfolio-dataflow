"""Home landing page - Portfolio entry point."""

import dash
import dash_mantine_components as dmc
from dash import dcc
from dash_iconify import DashIconify

dash.register_page(__name__, path="/", name="Home")

# Hero content from blueprint
HEADLINE = "I turn messy data into systems that actually work."
SUBHEAD = (
    "Data Engineer & Analytics Specialist. 8 years building pipelines, dashboards, "
    "and the infrastructure nobody sees but everyone depends on. Based in Toronto."
)

# Impact metrics
IMPACT_STATS = [
    {"value": "1B+", "label": "Rows processed daily across enterprise platform"},
    {"value": "40%", "label": "Efficiency gain through automation"},
    {"value": "5 Years", "label": "Building DataFlow from zero"},
]

# Featured project
FEATURED_PROJECT = {
    "title": "Toronto Housing Market Dashboard",
    "description": (
        "Real-time analytics on Toronto's housing trends. "
        "dbt-powered ETL, Python scraping, Plotly visualization."
    ),
    "status": "Live",
    "dashboard_link": "/toronto",
    "repo_link": "https://github.com/l3ocho/personal-portfolio",
}

# Brief intro
INTRO_TEXT = (
    "I'm a data engineer who's spent the last 8 years in the trenches—building the "
    "infrastructure that feeds dashboards, automates the boring stuff, and makes data "
    "actually usable. Most of my work has been in contact center operations and energy, "
    "where I've had to be scrappy: one-person data teams, legacy systems, stakeholders "
    "who need answers yesterday."
)

INTRO_CLOSING = "I like solving real problems, not theoretical ones."


def create_hero_section() -> dmc.Stack:
    """Create the hero section with headline, subhead, and CTAs."""
    return dmc.Stack(
        [
            dmc.Title(
                HEADLINE,
                order=1,
                ta="center",
                size="2.5rem",
            ),
            dmc.Text(
                SUBHEAD,
                size="lg",
                c="dimmed",
                ta="center",
                maw=700,
                mx="auto",
            ),
            dmc.Group(
                [
                    dcc.Link(
                        dmc.Button(
                            "View Projects",
                            size="lg",
                            variant="filled",
                            leftSection=DashIconify(icon="tabler:folder", width=20),
                        ),
                        href="/projects",
                    ),
                    dcc.Link(
                        dmc.Button(
                            "Get In Touch",
                            size="lg",
                            variant="outline",
                            leftSection=DashIconify(icon="tabler:mail", width=20),
                        ),
                        href="/contact",
                    ),
                ],
                justify="center",
                gap="md",
                mt="md",
            ),
        ],
        gap="md",
        py="xl",
    )


def create_impact_stat(stat: dict[str, str]) -> dmc.Stack:
    """Create a single impact stat."""
    return dmc.Stack(
        [
            dmc.Text(stat["value"], fw=700, size="2rem", ta="center"),
            dmc.Text(stat["label"], size="sm", c="dimmed", ta="center"),
        ],
        gap="xs",
        align="center",
    )


def create_impact_strip() -> dmc.Paper:
    """Create the impact statistics strip."""
    return dmc.Paper(
        dmc.SimpleGrid(
            [create_impact_stat(stat) for stat in IMPACT_STATS],
            cols={"base": 1, "sm": 3},
            spacing="xl",
        ),
        p="xl",
        radius="md",
        withBorder=True,
    )


def create_featured_project() -> dmc.Paper:
    """Create the featured project card."""
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Group(
                    [
                        dmc.Title("Featured Project", order=2, size="h3"),
                        dmc.Badge(
                            FEATURED_PROJECT["status"],
                            color="green",
                            variant="light",
                            size="lg",
                        ),
                    ],
                    justify="space-between",
                ),
                dmc.Title(
                    FEATURED_PROJECT["title"],
                    order=3,
                    size="h4",
                ),
                dmc.Text(
                    FEATURED_PROJECT["description"],
                    size="md",
                    c="dimmed",
                ),
                dmc.Group(
                    [
                        dcc.Link(
                            dmc.Button(
                                "View Dashboard",
                                variant="light",
                                leftSection=DashIconify(
                                    icon="tabler:chart-bar", width=18
                                ),
                            ),
                            href=FEATURED_PROJECT["dashboard_link"],
                        ),
                        dmc.Anchor(
                            dmc.Button(
                                "View Repository",
                                variant="subtle",
                                leftSection=DashIconify(
                                    icon="tabler:brand-github", width=18
                                ),
                            ),
                            href=FEATURED_PROJECT["repo_link"],
                            target="_blank",
                        ),
                    ],
                    gap="sm",
                ),
            ],
            gap="md",
        ),
        p="xl",
        radius="md",
        withBorder=True,
    )


def create_intro_section() -> dmc.Paper:
    """Create the brief intro section."""
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Text(INTRO_TEXT, size="md"),
                dmc.Text(INTRO_CLOSING, size="md", fw=500, fs="italic"),
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
            create_hero_section(),
            create_impact_strip(),
            create_featured_project(),
            create_intro_section(),
            dmc.Space(h=40),
        ],
        gap="xl",
    ),
    size="md",
    py="xl",
)
