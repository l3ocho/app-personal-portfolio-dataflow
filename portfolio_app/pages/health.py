"""Health check endpoint for deployment monitoring."""

import dash
from dash import html

dash.register_page(
    __name__,
    path="/health",
    title="Health Check",
)


def layout() -> html.Div:
    """Return simple health check response."""
    return html.Div(
        [
            html.Pre("status: ok"),
        ],
        id="health-check",
    )
