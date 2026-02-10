"""Amenities tab for Toronto Neighbourhood Dashboard.

Displays parks, schools, transit, and other amenity metrics.
"""

import dash_mantine_components as dmc
from dash import dcc


def create_amenities_tab() -> dmc.Stack:
    """Create the Amenities tab layout.

    Layout:
    - Choropleth map (amenity score) | KPI cards
    - Amenity breakdown chart | Amenity comparison radar

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
                                            "Neighbourhood Amenities",
                                            order=4,
                                            size="h5",
                                        ),
                                        dmc.Select(
                                            id="amenities-metric-select",
                                            data=[
                                                {
                                                    "value": "amenity_score",
                                                    "label": "Amenity Score",
                                                },
                                                {
                                                    "value": "parks_per_capita",
                                                    "label": "Parks per 1K",
                                                },
                                                {
                                                    "value": "schools_per_capita",
                                                    "label": "Schools per 1K",
                                                },
                                                {
                                                    "value": "transit_score",
                                                    "label": "Transit Score",
                                                },
                                            ],
                                            value="amenity_score",
                                            size="sm",
                                            w=180,
                                        ),
                                    ],
                                    justify="space-between",
                                    mb="sm",
                                ),
                                dcc.Graph(
                                    id="amenities-choropleth",
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
                                            "City Amenity Score", size="xs", c="dimmed"
                                        ),
                                        dmc.Title(
                                            id="amenities-city-score",
                                            children="68",
                                            order=2,
                                        ),
                                        dmc.Text(
                                            "Out of 100",
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
                                        dmc.Text("Total Parks", size="xs", c="dimmed"),
                                        dmc.Title(
                                            id="amenities-total-parks",
                                            children="1,500+",
                                            order=2,
                                        ),
                                        dmc.Text(
                                            id="amenities-park-area",
                                            children="8,000+ hectares",
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
                                            "Selected Neighbourhood",
                                            size="xs",
                                            c="dimmed",
                                        ),
                                        dmc.Title(
                                            id="amenities-selected-name",
                                            children="Click map to select",
                                            order=4,
                                            size="h5",
                                        ),
                                        dmc.Stack(
                                            id="amenities-selected-details",
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
                    # Amenity breakdown
                    dmc.GridCol(
                        dmc.Paper(
                            [
                                dmc.Title(
                                    "Amenity Breakdown",
                                    order=4,
                                    size="h5",
                                    mb="sm",
                                ),
                                dcc.Graph(
                                    id="amenities-breakdown-chart",
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
                    # Amenity comparison radar
                    dmc.GridCol(
                        dmc.Paper(
                            [
                                dmc.Title(
                                    "Amenity Comparison",
                                    order=4,
                                    size="h5",
                                    mb="sm",
                                ),
                                dcc.Graph(
                                    id="amenities-radar-chart",
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
