"""Demographics tab for Toronto Neighbourhood Dashboard.

Displays population, income, age, and diversity metrics.
"""

import dash_mantine_components as dmc
from dash import dcc


def create_demographics_tab() -> dmc.Stack:
    """Create the Demographics tab layout.

    Layout:
    - Choropleth map (demographic metric) | KPI cards
    - Age distribution chart | Income distribution chart

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
                                            "Neighbourhood Demographics",
                                            order=4,
                                            size="h5",
                                        ),
                                        dmc.Select(
                                            id="demographics-metric-select",
                                            data=[
                                                {
                                                    "value": "population",
                                                    "label": "Population",
                                                },
                                                {
                                                    "value": "median_income",
                                                    "label": "Median Income",
                                                },
                                                {
                                                    "value": "median_age",
                                                    "label": "Median Age",
                                                },
                                                {
                                                    "value": "diversity_index",
                                                    "label": "Diversity Index",
                                                },
                                            ],
                                            value="population",
                                            size="sm",
                                            w=180,
                                        ),
                                    ],
                                    justify="space-between",
                                    mb="sm",
                                ),
                                dcc.Graph(
                                    id="demographics-choropleth",
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
                                            "City Population", size="xs", c="dimmed"
                                        ),
                                        dmc.Title(
                                            id="demographics-city-pop",
                                            children="2.79M",
                                            order=2,
                                        ),
                                        dmc.Text(
                                            id="demographics-pop-change",
                                            children="+2.3% since 2016",
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
                                            "Median Household Income",
                                            size="xs",
                                            c="dimmed",
                                        ),
                                        dmc.Title(
                                            id="demographics-city-income",
                                            children="$84,000",
                                            order=2,
                                        ),
                                        dmc.Text(
                                            "City average",
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
                                            id="demographics-selected-name",
                                            children="Click map to select",
                                            order=4,
                                            size="h5",
                                        ),
                                        dmc.Stack(
                                            id="demographics-selected-details",
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
                    # Age distribution
                    dmc.GridCol(
                        dmc.Paper(
                            [
                                dmc.Title(
                                    "Age Distribution",
                                    order=4,
                                    size="h5",
                                    mb="sm",
                                ),
                                dcc.Graph(
                                    id="demographics-age-chart",
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
                    # Income distribution
                    dmc.GridCol(
                        dmc.Paper(
                            [
                                dmc.Title(
                                    "Income Distribution",
                                    order=4,
                                    size="h5",
                                    mb="sm",
                                ),
                                dcc.Graph(
                                    id="demographics-income-chart",
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
