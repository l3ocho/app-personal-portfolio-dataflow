"""Safety tab for Toronto Neighbourhood Dashboard.

Displays crime statistics, trends, and safety indicators.
"""

import dash_mantine_components as dmc
from dash import dcc


def create_safety_tab() -> dmc.Stack:
    """Create the Safety tab layout.

    Layout:
    - Choropleth map (crime rate) | KPI cards
    - Crime trend line chart | Crime by type breakdown

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
                                            "Crime Rate by Neighbourhood",
                                            order=4,
                                            size="h5",
                                        ),
                                        dmc.Select(
                                            id="safety-metric-select",
                                            data=[
                                                {
                                                    "value": "total_crime_rate",
                                                    "label": "Total Crime Rate",
                                                },
                                                {
                                                    "value": "violent_crime_rate",
                                                    "label": "Violent Crime",
                                                },
                                                {
                                                    "value": "property_crime_rate",
                                                    "label": "Property Crime",
                                                },
                                                {
                                                    "value": "theft_rate",
                                                    "label": "Theft",
                                                },
                                            ],
                                            value="total_crime_rate",
                                            size="sm",
                                            w=180,
                                        ),
                                    ],
                                    justify="space-between",
                                    mb="sm",
                                ),
                                dcc.Graph(
                                    id="safety-choropleth",
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
                                            "City Crime Rate", size="xs", c="dimmed"
                                        ),
                                        dmc.Title(
                                            id="safety-city-rate",
                                            children="4,250",
                                            order=2,
                                        ),
                                        dmc.Text(
                                            id="safety-rate-change",
                                            children="-2.1% YoY",
                                            size="sm",
                                            c="green",
                                        ),
                                    ],
                                    p="md",
                                    radius="sm",
                                    withBorder=True,
                                ),
                                dmc.Paper(
                                    [
                                        dmc.Text(
                                            "Total Incidents (2023)",
                                            size="xs",
                                            c="dimmed",
                                        ),
                                        dmc.Title(
                                            id="safety-total-incidents",
                                            children="125,430",
                                            order=2,
                                        ),
                                        dmc.Text(
                                            "Per 100,000 residents",
                                            size="sm",
                                            c="dimmed",
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
                                            id="safety-selected-name",
                                            children="Click map to select",
                                            order=4,
                                            size="h5",
                                        ),
                                        dmc.Stack(
                                            id="safety-selected-details",
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
                    # Crime trend
                    dmc.GridCol(
                        dmc.Paper(
                            [
                                dmc.Title(
                                    "Crime Trends (5 Year)",
                                    order=4,
                                    size="h5",
                                    mb="sm",
                                ),
                                dcc.Graph(
                                    id="safety-trend-chart",
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
                    # Crime by type
                    dmc.GridCol(
                        dmc.Paper(
                            [
                                dmc.Title(
                                    "Crime by Category",
                                    order=4,
                                    size="h5",
                                    mb="sm",
                                ),
                                dcc.Graph(
                                    id="safety-types-chart",
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
