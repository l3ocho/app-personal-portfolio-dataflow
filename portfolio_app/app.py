"""Dash application factory with Pages routing."""

import dash
import dash_mantine_components as dmc
from dash import dcc, html

from .components import create_sidebar
from .config import get_settings


def create_app() -> dash.Dash:
    """Create and configure the Dash application."""
    app = dash.Dash(
        __name__,
        use_pages=True,
        suppress_callback_exceptions=True,
        title="Analytics Portfolio",
        external_stylesheets=dmc.styles.ALL,
    )

    app.layout = dmc.MantineProvider(
        id="mantine-provider",
        children=[
            dcc.Location(id="url", refresh=False),
            dcc.Store(id="theme-store", storage_type="local", data="dark"),
            dcc.Store(id="theme-init-dummy"),  # Dummy store for theme init callback
            html.Div(
                [
                    create_sidebar(),
                    html.Div(
                        dash.page_container,
                        className="page-content-wrapper",
                    ),
                ],
            ),
        ],
        theme={
            "primaryColor": "blue",
            "fontFamily": "'Inter', sans-serif",
        },
        defaultColorScheme="dark",
    )

    # Import callbacks to register them
    from . import callbacks  # noqa: F401

    return app


def main() -> None:
    """Run the development server."""
    settings = get_settings()
    app = create_app()
    app.run(debug=settings.dash_debug, host="0.0.0.0", port=8050)


if __name__ == "__main__":
    main()
