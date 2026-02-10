"""Sidebar navigation callbacks for active state updates."""

from typing import Any

from dash import Input, Output, callback

from portfolio_app.components.sidebar import create_sidebar_content


@callback(  # type: ignore[misc]
    Output("floating-sidebar", "children"),
    Input("url", "pathname"),
    prevent_initial_call=False,
)
def update_sidebar_active_state(pathname: str) -> list[Any]:
    """Update sidebar to highlight the current page.

    Args:
        pathname: Current URL pathname from dcc.Location.

    Returns:
        Updated sidebar content with correct active state.
    """
    current_path = pathname or "/"
    return create_sidebar_content(current_path=current_path)
