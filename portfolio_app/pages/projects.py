"""Projects overview page - Hub for all portfolio projects."""

from typing import Any

import dash
import dash_mantine_components as dmc
from dash import dcc
from dash_iconify import DashIconify

dash.register_page(__name__, path="/projects", name="Projects")

# Page intro
INTRO_TEXT = (
    "These are projects I've built—some professional (anonymized where needed), "
    "some personal. Each one taught me something. Use the sidebar to jump directly "
    "to live dashboards or explore the overviews below."
)

# Project definitions
PROJECTS: list[dict[str, Any]] = [
    {
        "title": "Toronto Housing Market Dashboard",
        "type": "Personal Project",
        "status": "live",
        "status_color": "green",
        "problem": (
            "Toronto's housing market moves fast, and most publicly available data "
            "is either outdated, behind paywalls, or scattered across dozens of sources. "
            "I wanted a single dashboard that tracked trends in real-time."
        ),
        "built": [
            "Data Pipeline: Python scraper pulling listings data, automated on schedule",
            "Transformation Layer: dbt-based SQL architecture (staging -> intermediate -> marts)",
            "Visualization: Interactive Plotly-Dash dashboard with filters by neighborhood, price range, property type",
            "Infrastructure: PostgreSQL backend, version-controlled in Git",
        ],
        "tech_stack": "Python, dbt, PostgreSQL, Plotly-Dash, GitHub Actions",
        "learned": (
            "Real estate data is messy as hell. Listings get pulled, prices change, "
            "duplicates are everywhere. Building a reliable pipeline meant implementing "
            'serious data quality checks and learning to embrace "good enough" over "perfect."'
        ),
        "dashboard_link": "/toronto",
        "repo_link": None,
    },
    {
        "title": "Leo Claude Marketplace",
        "type": "Personal Project",
        "status": "live",
        "status_color": "blue",
        "problem": (
            "A collection of Claude Code plugins that automate sprint planning, code review, deployment, "
            "and data engineering workflows via slash commands in Claude Code sessions."
        ),
        "built": [],
        "tech_stack": "",
        "learned": "",
        "dashboard_link": None,
        "repo_link": "https://gitea.hotserv.cloud/personal-projects/leo-claude-mktplace",
    },
    {
        "title": "Gitea MCP",
        "type": "Personal Project",
        "status": "live",
        "status_color": "green",
        "problem": (
            "MCP server providing 39 tools for Gitea repository operations, issue management, "
            "and pull request workflows."
        ),
        "built": [],
        "tech_stack": "",
        "learned": "",
        "dashboard_link": None,
        "repo_link": "https://gitea.hotserv.cloud/personal-projects/gitea_mcp",
    },
    {
        "title": "Football Power Shift",
        "type": "Personal Project",
        "status": "soon",
        "status_color": "yellow",
        "problem": (
            "A football dashboard analyzing the shift in global football economics across 7 leagues, "
            "anchored by Flamengo's rise as the narrative thread."
        ),
        "built": [],
        "tech_stack": "",
        "learned": "",
        "dashboard_link": None,
        "repo_link": None,
    },
]


def create_project_card(project: dict[str, Any]) -> dmc.Paper:
    """Create a simplified project card with description and action links."""
    # Map status to icon
    status_icons = {
        "live": "eos-icons:atom-electron",
        "soon": "eos-icons:installing",
        "archived": "eos-icons:application-window",
    }

    # Build action buttons
    buttons = []
    if project.get("dashboard_link"):
        buttons.append(
            dcc.Link(
                dmc.Button(
                    "View Dashboard",
                    variant="light",
                    size="sm",
                    leftSection=DashIconify(icon="tabler:chart-bar", width=16),
                ),
                href=project["dashboard_link"],
            )
        )
    if project.get("repo_link"):
        buttons.append(
            dmc.Anchor(
                dmc.Button(
                    "View Repository",
                    variant="light",
                    size="sm",
                    leftSection=DashIconify(icon="tabler:brand-github", width=16),
                ),
                href=project["repo_link"],
                target="_blank",
            )
        )
    if project.get("external_link"):
        buttons.append(
            dcc.Link(
                dmc.Button(
                    project.get("external_label", "Learn More"),
                    variant="light",
                    size="sm",
                    leftSection=DashIconify(icon="tabler:arrow-right", width=16),
                ),
                href=project["external_link"],
            )
        )

    return dmc.Paper(
        dmc.Stack(
            [
                # Header with status badge
                dmc.Group(
                    [
                        dmc.Stack(
                            [
                                dmc.Text(project["title"], fw=600, size="lg"),
                                dmc.Text(project["type"], size="sm", c="dimmed"),
                            ],
                            gap=0,
                        ),
                        dmc.Badge(
                            dmc.Group(
                                [
                                    DashIconify(
                                        icon=status_icons.get(
                                            project["status"],
                                            "eos-icons:application-window",
                                        ),
                                        width=14,
                                    ),
                                    dmc.Text(
                                        project["status"],
                                        size="sm",
                                        style={"textTransform": "lowercase"},
                                    ),
                                ],
                                gap=4,
                            ),
                            color=project["status_color"],
                            variant="light",
                            size="lg",
                        ),
                    ],
                    justify="space-between",
                    align="flex-start",
                ),
                # Description
                dmc.Text(
                    project["problem"], size="sm", c="dimmed", style={"flex": "1"}
                ),
                # Action buttons
                dmc.Group(buttons, gap="sm"),
            ],
            gap="md",
            style={"display": "flex", "flexDirection": "column", "height": "100%"},
        ),
        p="md",
        radius="md",
        shadow="sm",
        className="project-card",
        style={"height": "100%"},
    )


layout = dmc.Container(
    dmc.Stack(
        [
            dmc.Title("Projects", order=1, ta="center"),
            dmc.Text(
                INTRO_TEXT, size="md", c="dimmed", ta="center", maw=700, mx="auto"
            ),
            dmc.Divider(my="lg"),
            dmc.SimpleGrid(
                cols=2,
                spacing="lg",
                children=[create_project_card(project) for project in PROJECTS],
            ),
            dmc.Space(h=40),
        ],
        gap="xl",
    ),
    size="lg",
    py="xl",
)
