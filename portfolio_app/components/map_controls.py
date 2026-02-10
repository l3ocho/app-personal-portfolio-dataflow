"""Map control components for choropleth visualizations."""

from typing import Any

import dash_mantine_components as dmc
from dash import html


def create_metric_selector(
    id_prefix: str,
    options: list[dict[str, str]],
    default_value: str | None = None,
    label: str = "Select Metric",
) -> dmc.Select:
    """Create a metric selector dropdown.

    Args:
        id_prefix: Prefix for component IDs.
        options: List of options with 'label' and 'value' keys.
        default_value: Initial selected value.
        label: Label text for the selector.

    Returns:
        Mantine Select component.
    """
    return dmc.Select(
        id=f"{id_prefix}-metric-selector",
        label=label,
        data=options,
        value=default_value or (options[0]["value"] if options else None),
        w=200,
    )


def create_map_controls(
    id_prefix: str,
    metric_options: list[dict[str, str]],
    default_metric: str | None = None,
    show_layer_toggle: bool = True,
) -> dmc.Paper:
    """Create a control panel for map visualizations.

    Args:
        id_prefix: Prefix for component IDs.
        metric_options: Options for metric selector.
        default_metric: Default selected metric.
        show_layer_toggle: Whether to show layer visibility toggle.

    Returns:
        Mantine Paper component containing controls.
    """
    controls: list[Any] = [
        create_metric_selector(
            id_prefix=id_prefix,
            options=metric_options,
            default_value=default_metric,
            label="Display Metric",
        ),
    ]

    if show_layer_toggle:
        controls.append(
            dmc.Switch(
                id=f"{id_prefix}-layer-toggle",
                label="Show Boundaries",
                checked=True,
                mt="sm",
            )
        )

    return dmc.Paper(
        children=[
            dmc.Text("Map Controls", fw=500, size="sm", mb="xs"),
            html.Div(controls),
        ],
        p="md",
        radius="sm",
        withBorder=True,
    )
