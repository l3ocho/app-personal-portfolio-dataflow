"""Overview tab for Toronto Neighbourhood Dashboard.

Displays composite livability score with safety, affordability, and amenity components.
"""

import dash_mantine_components as dmc
from dash import dcc, html


def create_overview_tab() -> dmc.Stack:
    """Create the Overview tab layout.

    Layout:
    - Choropleth map (livability score) | KPI cards
    - Top/Bottom 10 bar chart | Income vs Crime scatter

    Returns:
        Tab content as a Mantine Stack component.
    """
    return dmc.Stack(
        [
            # Main content: Map + KPIs
            dmc.Grid(
                [
                    # Choropleth map
                    dmc.GridCol(
                        dmc.Paper(
                            [
                                dmc.Group(
                                    [
                                        dmc.Title(
                                            "Neighbourhood Livability",
                                            order=4,
                                            size="h5",
                                        ),
                                        dmc.Select(
                                            id="overview-metric-select",
                                            data=[
                                                {
                                                    "value": "livability_score",
                                                    "label": "Livability Score",
                                                },
                                                {
                                                    "value": "safety_score",
                                                    "label": "Safety Score",
                                                },
                                                {
                                                    "value": "affordability_score",
                                                    "label": "Affordability Score",
                                                },
                                                {
                                                    "value": "amenity_score",
                                                    "label": "Amenity Score",
                                                },
                                            ],
                                            value="livability_score",
                                            size="sm",
                                            w=180,
                                        ),
                                    ],
                                    justify="space-between",
                                    mb="sm",
                                ),
                                dcc.Graph(
                                    id="overview-choropleth",
                                    config={
                                        "scrollZoom": True,
                                        "displayModeBar": False,
                                    },
                                    style={"height": "450px"},
                                ),
                            ],
                            p="md",
                            radius="sm",
                            withBorder=True,
                        ),
                        span={"base": 12, "lg": 8},
                    ),
                    # KPI cards
                    dmc.GridCol(
                        dmc.Stack(
                            [
                                dmc.Paper(
                                    [
                                        dmc.Text("City Average", size="xs", c="dimmed"),
                                        dmc.Title(
                                            id="overview-city-avg",
                                            children="72",
                                            order=2,
                                        ),
                                        dmc.Text("Livability Score", size="sm", fw=500),
                                    ],
                                    p="md",
                                    radius="sm",
                                    withBorder=True,
                                ),
                                dmc.Paper(
                                    [
                                        dmc.Text(
                                            "Selected Neighbourhood",
                                            size="xs",
                                            c="dimmed",
                                        ),
                                        dmc.Title(
                                            id="overview-selected-name",
                                            children="Click map to select",
                                            order=4,
                                            size="h5",
                                        ),
                                        html.Div(
                                            id="overview-selected-scores",
                                            children=[
                                                dmc.Text("—", c="dimmed"),
                                            ],
                                        ),
                                    ],
                                    p="md",
                                    radius="sm",
                                    withBorder=True,
                                ),
                                dmc.Paper(
                                    [
                                        dmc.Text(
                                            "Score Components", size="xs", c="dimmed"
                                        ),
                                        dmc.Stack(
                                            [
                                                dmc.Group(
                                                    [
                                                        dmc.Text("Safety", size="sm"),
                                                        dmc.Text(
                                                            "30%",
                                                            size="sm",
                                                            c="dimmed",
                                                        ),
                                                    ],
                                                    justify="space-between",
                                                ),
                                                dmc.Group(
                                                    [
                                                        dmc.Text(
                                                            "Affordability", size="sm"
                                                        ),
                                                        dmc.Text(
                                                            "40%",
                                                            size="sm",
                                                            c="dimmed",
                                                        ),
                                                    ],
                                                    justify="space-between",
                                                ),
                                                dmc.Group(
                                                    [
                                                        dmc.Text(
                                                            "Amenities", size="sm"
                                                        ),
                                                        dmc.Text(
                                                            "30%",
                                                            size="sm",
                                                            c="dimmed",
                                                        ),
                                                    ],
                                                    justify="space-between",
                                                ),
                                            ],
                                            gap="xs",
                                        ),
                                    ],
                                    p="md",
                                    radius="sm",
                                    withBorder=True,
                                ),
                            ],
                            gap="md",
                        ),
                        span={"base": 12, "lg": 4},
                    ),
                ],
                gutter="md",
            ),
            # Supporting charts
            dmc.Grid(
                [
                    # Top/Bottom rankings
                    dmc.GridCol(
                        dmc.Paper(
                            [
                                dmc.Title(
                                    "Top & Bottom Neighbourhoods",
                                    order=4,
                                    size="h5",
                                    mb="sm",
                                ),
                                dcc.Graph(
                                    id="overview-rankings-chart",
                                    config={"displayModeBar": False},
                                    style={"height": "300px"},
                                ),
                            ],
                            p="md",
                            radius="sm",
                            withBorder=True,
                        ),
                        span={"base": 12, "md": 6},
                    ),
                    # Scatter plot
                    dmc.GridCol(
                        dmc.Paper(
                            [
                                dmc.Title(
                                    "Income vs Safety",
                                    order=4,
                                    size="h5",
                                    mb="sm",
                                ),
                                dcc.Graph(
                                    id="overview-scatter-chart",
                                    config={"displayModeBar": False},
                                    style={"height": "300px"},
                                ),
                            ],
                            p="md",
                            radius="sm",
                            withBorder=True,
                        ),
                        span={"base": 12, "md": 6},
                    ),
                ],
                gutter="md",
            ),
        ],
        gap="md",
    )
