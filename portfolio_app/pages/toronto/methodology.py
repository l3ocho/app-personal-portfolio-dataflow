"""Methodology page for Toronto Housing Dashboard."""

import dash
import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify

dash.register_page(
    __name__,
    path="/toronto/methodology",
    title="Methodology | Toronto Housing Dashboard",
    description="Data sources, methodology, and limitations for the Toronto Housing Dashboard",
)


def layout() -> dmc.Container:
    """Render the methodology page layout."""
    return dmc.Container(
        size="md",
        py="xl",
        children=[
            # Back to Dashboard button
            dcc.Link(
                dmc.Button(
                    "Back to Dashboard",
                    leftSection=DashIconify(icon="tabler:arrow-left", width=18),
                    variant="subtle",
                    color="gray",
                ),
                href="/toronto",
            ),
            # Header
            dmc.Title("Methodology", order=1, mb="lg", mt="md"),
            dmc.Text(
                "This page documents the data sources, processing methodology, "
                "and known limitations of the Toronto Housing Dashboard.",
                size="lg",
                c="dimmed",
                mb="xl",
            ),
            # Data Sources Section
            dmc.Paper(
                p="lg",
                radius="md",
                withBorder=True,
                mb="lg",
                children=[
                    dmc.Title("Data Sources", order=2, mb="md"),
                    # CMHC
                    dmc.Title("Rental Data: CMHC", order=3, size="h4", mb="sm"),
                    dmc.Text(
                        [
                            "Canada Mortgage and Housing Corporation (CMHC) conducts the annual ",
                            html.Strong("Rental Market Survey"),
                            " providing rental market statistics for major urban centres.",
                        ],
                        mb="sm",
                    ),
                    dmc.List(
                        [
                            dmc.ListItem("Source: CMHC Rental Market Survey (Excel)"),
                            dmc.ListItem(
                                "Geographic granularity: ~20 CMHC Zones (Census Tract aligned)"
                            ),
                            dmc.ListItem(
                                "Temporal granularity: Annual (October survey)"
                            ),
                            dmc.ListItem("Coverage: 2021-present"),
                            dmc.ListItem(
                                [
                                    "Metrics: Average/median rent, vacancy rate, universe count, ",
                                    "turnover rate, year-over-year rent change",
                                ]
                            ),
                        ],
                        mb="md",
                    ),
                    dmc.Anchor(
                        "CMHC Housing Market Information Portal",
                        href="https://www.cmhc-schl.gc.ca/professionals/housing-markets-data-and-research/housing-data/data-tables/rental-market",
                        target="_blank",
                    ),
                ],
            ),
            # Geographic Considerations
            dmc.Paper(
                p="lg",
                radius="md",
                withBorder=True,
                mb="lg",
                children=[
                    dmc.Title("Geographic Considerations", order=2, mb="md"),
                    dmc.Text(
                        "The dashboard presents two geographic layers:",
                        mb="sm",
                    ),
                    dmc.List(
                        [
                            dmc.ListItem(
                                [
                                    html.Strong("City Neighbourhoods (158): "),
                                    "Official City of Toronto neighbourhood boundaries, "
                                    "used for neighbourhood-level analysis.",
                                ]
                            ),
                            dmc.ListItem(
                                [
                                    html.Strong("CMHC Zones (~20): "),
                                    "Used for rental data visualization. "
                                    "Zones are aligned with Census Tract boundaries.",
                                ]
                            ),
                        ],
                    ),
                ],
            ),
            # Policy Events
            dmc.Paper(
                p="lg",
                radius="md",
                withBorder=True,
                mb="lg",
                children=[
                    dmc.Title("Policy Event Annotations", order=2, mb="md"),
                    dmc.Text(
                        "The time series charts include markers for significant policy events "
                        "that may have influenced housing market conditions. These annotations are "
                        "for contextual reference only.",
                        mb="md",
                    ),
                    dmc.Alert(
                        title="No Causation Claims",
                        color="blue",
                        children=[
                            "The presence of a policy marker near a market trend change does ",
                            html.Strong("not"),
                            " imply causation. Housing markets are influenced by numerous factors "
                            "beyond policy interventions.",
                        ],
                    ),
                ],
            ),
            # Limitations
            dmc.Paper(
                p="lg",
                radius="md",
                withBorder=True,
                mb="lg",
                children=[
                    dmc.Title("Limitations", order=2, mb="md"),
                    dmc.List(
                        [
                            dmc.ListItem(
                                [
                                    html.Strong("Aggregate Data: "),
                                    "All statistics are aggregates. Individual property characteristics, "
                                    "condition, and micro-location are not reflected.",
                                ]
                            ),
                            dmc.ListItem(
                                [
                                    html.Strong("Reporting Lag: "),
                                    "CMHC rental data is annual (October survey). "
                                    "Other data sources may have different update frequencies.",
                                ]
                            ),
                            dmc.ListItem(
                                [
                                    html.Strong("Data Suppression: "),
                                    "Some cells may be suppressed for confidentiality when counts "
                                    "are below thresholds.",
                                ]
                            ),
                        ],
                    ),
                ],
            ),
            # Technical Implementation
            dmc.Paper(
                p="lg",
                radius="md",
                withBorder=True,
                children=[
                    dmc.Title("Technical Implementation", order=2, mb="md"),
                    dmc.Text("This dashboard is built with:", mb="sm"),
                    dmc.List(
                        [
                            dmc.ListItem("Python 3.11+ with Dash and Plotly"),
                            dmc.ListItem("PostgreSQL with PostGIS for geospatial data"),
                            dmc.ListItem("dbt for data transformation"),
                            dmc.ListItem("Pydantic for data validation"),
                            dmc.ListItem("SQLAlchemy 2.0 for database operations"),
                        ],
                        mb="md",
                    ),
                    dmc.Anchor(
                        "View source code on GitHub",
                        href="https://github.com/lmiranda/personal-portfolio",
                        target="_blank",
                    ),
                ],
            ),
            # Back link
            dmc.Group(
                mt="xl",
                children=[
                    dmc.Anchor(
                        "← Back to Dashboard",
                        href="/toronto",
                        size="lg",
                    ),
                ],
            ),
        ],
    )
