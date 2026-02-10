"""Time selection components for temporal data filtering."""

from datetime import date

import dash_mantine_components as dmc


def create_year_selector(
    id_prefix: str,
    min_year: int = 2020,
    max_year: int | None = None,
    default_year: int | None = None,
    label: str = "Select Year",
) -> dmc.Select:
    """Create a year selector dropdown.

    Args:
        id_prefix: Prefix for component IDs.
        min_year: Minimum year option.
        max_year: Maximum year option (defaults to current year).
        default_year: Initial selected year.
        label: Label text for the selector.

    Returns:
        Mantine Select component.
    """
    if max_year is None:
        max_year = date.today().year

    if default_year is None:
        default_year = max_year

    years = list(range(max_year, min_year - 1, -1))
    options = [{"label": str(year), "value": str(year)} for year in years]

    return dmc.Select(
        id=f"{id_prefix}-year-selector",
        label=label,
        data=options,
        value=str(default_year),
        w=120,
    )


def create_time_slider(
    id_prefix: str,
    min_year: int = 2020,
    max_year: int | None = None,
    default_range: tuple[int, int] | None = None,
    label: str = "Time Range",
) -> dmc.Paper:
    """Create a time range slider component.

    Args:
        id_prefix: Prefix for component IDs.
        min_year: Minimum year for the slider.
        max_year: Maximum year for the slider.
        default_range: Default (start, end) year range.
        label: Label text for the slider.

    Returns:
        Mantine Paper component containing the slider.
    """
    if max_year is None:
        max_year = date.today().year

    if default_range is None:
        default_range = (min_year, max_year)

    # Create marks for every year
    marks = [
        {"value": year, "label": str(year)} for year in range(min_year, max_year + 1)
    ]

    return dmc.Paper(
        children=[
            dmc.Text(label, fw=500, size="sm", mb="xs"),
            dmc.RangeSlider(
                id=f"{id_prefix}-time-slider",
                min=min_year,
                max=max_year,
                value=list(default_range),
                marks=marks,
                step=1,
                minRange=1,
                mt="md",
                mb="sm",
            ),
        ],
        p="md",
        radius="sm",
        withBorder=True,
    )


def create_month_selector(
    id_prefix: str,
    default_month: int | None = None,
    label: str = "Select Month",
) -> dmc.Select:
    """Create a month selector dropdown.

    Args:
        id_prefix: Prefix for component IDs.
        default_month: Initial selected month (1-12).
        label: Label text for the selector.

    Returns:
        Mantine Select component.
    """
    months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    options = [{"label": month, "value": str(i + 1)} for i, month in enumerate(months)]

    if default_month is None:
        default_month = date.today().month

    return dmc.Select(
        id=f"{id_prefix}-month-selector",
        label=label,
        data=options,
        value=str(default_month),
        w=140,
    )
