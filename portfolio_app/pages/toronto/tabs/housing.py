"""Housing tab for Toronto Neighbourhood Dashboard.

Displays affordability metrics, rent trends, and housing indicators.
"""

import dash_mantine_components as dmc
from dash import dcc


def create_housing_tab() -> dmc.Stack:
    """Create the Housing tab layout.

    Layout:
    - Choropleth map (affordability index) | KPI cards
    - Rent trend line chart | Dwelling types breakdown

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
                                            "Housing Affordability",
                                            order=4,
                                            size="h5",
                                        ),
                                        dmc.Select(
                                            id="housing-metric-select",
                                            data=[
                                                {
                                                    "value": "affordability_index",
                                                    "label": "Affordability Index",
                                                },
                                                {
                                                    "value": "avg_rent_2bed",
                                                    "label": "Avg Rent (2BR)",
                                                },
                                                {
                                                    "value": "rent_to_income_pct",
                                                    "label": "Rent-to-Income %",
                                                },
                                                {
                                                    "value": "vacancy_rate",
                                                    "label": "Vacancy Rate",
                                                },
                                            ],
                                            value="affordability_index",
                                            size="sm",
                                            w=180,
                                        ),
                                    ],
                                    justify="space-between",
                                    mb="sm",
                                ),
                                dcc.Graph(
                                    id="housing-choropleth",
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
                                        dmc.Text(
                                            "City Avg 2BR Rent", size="xs", c="dimmed"
                                        ),
                                        dmc.Title(
                                            id="housing-city-rent",
                                            children="$2,450",
                                            order=2,
                                        ),
                                        dmc.Text(
                                            id="housing-rent-change",
                                            children="+4.2% YoY",
                                            size="sm",
                                            c="red",
                                        ),
                                    ],
                                    p="md",
                                    radius="sm",
                                    withBorder=True,
                                ),
                                dmc.Paper(
                                    [
                                        dmc.Text(
                                            "City Avg Vacancy", size="xs", c="dimmed"
                                        ),
                                        dmc.Title(
                                            id="housing-city-vacancy",
                                            children="1.8%",
                                            order=2,
                                        ),
                                        dmc.Text(
                                            "Below healthy rate (3%)",
                                            size="sm",
                                            c="orange",
                                        ),
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
                                            id="housing-selected-name",
                                            children="Click map to select",
                                            order=4,
                                            size="h5",
                                        ),
                                        dmc.Stack(
                                            id="housing-selected-details",
                                            children=[
                                                dmc.Text("—", c="dimmed"),
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
                    # Rent trend
                    dmc.GridCol(
                        dmc.Paper(
                            [
                                dmc.Title(
                                    "Rent Trends (5 Year)",
                                    order=4,
                                    size="h5",
                                    mb="sm",
                                ),
                                dcc.Graph(
                                    id="housing-trend-chart",
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
                    # Dwelling types
                    dmc.GridCol(
                        dmc.Paper(
                            [
                                dmc.Title(
                                    "Dwelling Types",
                                    order=4,
                                    size="h5",
                                    mb="sm",
                                ),
                                dcc.Graph(
                                    id="housing-types-chart",
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
