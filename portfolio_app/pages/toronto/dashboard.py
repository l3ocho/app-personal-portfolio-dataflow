"""Toronto Neighbourhood Dashboard page.

Displays neighbourhood-level data across 5 tabs: Overview, Housing, Safety,
Demographics, and Amenities. Each tab provides interactive choropleth maps,
KPI cards, and supporting charts.
"""

import dash
import dash_mantine_components as dmc
from dash import dcc
from dash_iconify import DashIconify

from portfolio_app.pages.toronto.tabs import (
    create_amenities_tab,
    create_demographics_tab,
    create_housing_tab,
    create_overview_tab,
    create_safety_tab,
)

dash.register_page(__name__, path="/toronto", name="Toronto Neighbourhoods")

# Tab configuration
TAB_CONFIG = [
    {
        "value": "overview",
        "label": "Overview",
        "icon": "tabler:chart-pie",
        "color": "blue",
    },
    {
        "value": "housing",
        "label": "Housing",
        "icon": "tabler:home",
        "color": "teal",
    },
    {
        "value": "safety",
        "label": "Safety",
        "icon": "tabler:shield-check",
        "color": "orange",
    },
    {
        "value": "demographics",
        "label": "Demographics",
        "icon": "tabler:users",
        "color": "violet",
    },
    {
        "value": "amenities",
        "label": "Amenities",
        "icon": "tabler:trees",
        "color": "green",
    },
]


def create_header() -> dmc.Group:
    """Create the dashboard header with title and controls."""
    return dmc.Group(
        [
            dmc.Stack(
                [
                    dmc.Title("Toronto Neighbourhood Dashboard", order=1),
                    dmc.Text(
                        "Explore livability across 158 Toronto neighbourhoods",
                        c="dimmed",
                    ),
                ],
                gap="xs",
            ),
            dmc.Group(
                [
                    dcc.Link(
                        dmc.Button(
                            "Methodology",
                            leftSection=DashIconify(
                                icon="tabler:info-circle", width=18
                            ),
                            variant="subtle",
                            color="gray",
                        ),
                        href="/toronto/methodology",
                    ),
                    dmc.Select(
                        id="toronto-year-select",
                        data=[
                            {"value": "2021", "label": "2021"},
                            {"value": "2022", "label": "2022"},
                            {"value": "2023", "label": "2023"},
                        ],
                        value="2021",
                        label="Census Year",
                        size="sm",
                        w=120,
                    ),
                ],
                gap="md",
            ),
        ],
        justify="space-between",
        align="flex-start",
    )


def create_neighbourhood_selector() -> dmc.Paper:
    """Create the neighbourhood search/select component."""
    return dmc.Paper(
        dmc.Group(
            [
                DashIconify(icon="tabler:search", width=20, color="gray"),
                dmc.Select(
                    id="toronto-neighbourhood-select",
                    placeholder="Search neighbourhoods...",
                    searchable=True,
                    clearable=True,
                    data=[],  # Populated by callback
                    style={"flex": 1},
                ),
                dmc.Button(
                    "Compare",
                    id="toronto-compare-btn",
                    leftSection=DashIconify(icon="tabler:git-compare", width=16),
                    variant="light",
                    disabled=True,
                ),
            ],
            gap="sm",
        ),
        p="sm",
        radius="sm",
        withBorder=True,
    )


def create_tab_navigation() -> dmc.Tabs:
    """Create the tab navigation with icons."""
    return dmc.Tabs(
        [
            dmc.TabsList(
                [
                    dmc.TabsTab(
                        dmc.Group(
                            [
                                DashIconify(icon=tab["icon"], width=18),
                                dmc.Text(tab["label"], size="sm"),
                            ],
                            gap="xs",
                        ),
                        value=tab["value"],
                    )
                    for tab in TAB_CONFIG
                ],
                grow=True,
            ),
            # Tab panels
            dmc.TabsPanel(create_overview_tab(), value="overview", pt="md"),
            dmc.TabsPanel(create_housing_tab(), value="housing", pt="md"),
            dmc.TabsPanel(create_safety_tab(), value="safety", pt="md"),
            dmc.TabsPanel(create_demographics_tab(), value="demographics", pt="md"),
            dmc.TabsPanel(create_amenities_tab(), value="amenities", pt="md"),
        ],
        id="toronto-tabs",
        value="overview",
        variant="default",
    )


def create_data_notice() -> dmc.Alert:
    """Create a notice about data sources."""
    return dmc.Alert(
        children=[
            dmc.Text(
                "Data from Toronto Open Data (Census 2021, Crime Statistics) and "
                "CMHC Rental Market Reports. Click neighbourhoods on the map for details.",
                size="sm",
            ),
        ],
        title="Data Sources",
        color="blue",
        variant="light",
        icon=DashIconify(icon="tabler:info-circle", width=20),
    )


# Store for selected neighbourhood
neighbourhood_store = dcc.Store(id="toronto-selected-neighbourhood", data=None)

# Register callbacks
from portfolio_app.pages.toronto import callbacks  # noqa: E402, F401

layout = dmc.Container(
    dmc.Stack(
        [
            neighbourhood_store,
            create_header(),
            create_data_notice(),
            create_neighbourhood_selector(),
            create_tab_navigation(),
            dmc.Space(h=40),
        ],
        gap="lg",
    ),
    size="xl",
    py="xl",
)
