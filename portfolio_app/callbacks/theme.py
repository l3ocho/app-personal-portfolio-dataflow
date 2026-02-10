"""Theme toggle callbacks using clientside JavaScript."""

from dash import Input, Output, State, clientside_callback

# Toggle theme on button click
# Stores new theme value and updates the DOM attribute
clientside_callback(
    """
    function(n_clicks, currentTheme) {
        if (n_clicks === undefined || n_clicks === null) {
            return window.dash_clientside.no_update;
        }
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-mantine-color-scheme', newTheme);
        return newTheme;
    }
    """,
    Output("theme-store", "data"),
    Input("theme-toggle", "n_clicks"),
    State("theme-store", "data"),
    prevent_initial_call=True,
)

# Initialize theme from localStorage on page load
# Uses a dummy output since we only need the side effect of setting the DOM attribute
clientside_callback(
    """
    function(theme) {
        if (theme) {
            document.documentElement.setAttribute('data-mantine-color-scheme', theme);
        }
        return theme;
    }
    """,
    Output("theme-init-dummy", "data"),
    Input("theme-store", "data"),
    prevent_initial_call=False,
)
