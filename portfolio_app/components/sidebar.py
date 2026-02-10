"""Floating sidebar navigation component."""

import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify

# Navigation items configuration - main pages
NAV_ITEMS_MAIN = [
    {"path": "/", "icon": "tabler:home", "label": "Home"},
    {"path": "/about", "icon": "tabler:user", "label": "About"},
    {"path": "/blog", "icon": "tabler:article", "label": "Blog"},
    {"path": "/resume", "icon": "tabler:file-text", "label": "Resume"},
    {"path": "/contact", "icon": "tabler:mail", "label": "Contact"},
]

# Navigation items configuration - projects/dashboards (separated)
NAV_ITEMS_PROJECTS = [
    {"path": "/projects", "icon": "tabler:folder", "label": "Projects"},
    {"path": "/toronto", "icon": "tabler:map-2", "label": "Toronto Housing"},
]

# External links configuration
EXTERNAL_LINKS = [
    {
        "url": "https://github.com/l3ocho",
        "icon": "tabler:brand-github",
        "label": "GitHub",
    },
    {
        "url": "https://www.linkedin.com/in/leobmiranda/",
        "icon": "tabler:brand-linkedin",
        "label": "LinkedIn",
    },
]


def create_brand_logo() -> html.Div:
    """Create the brand initials logo."""
    return html.Div(
        dcc.Link(
            "LM",
            href="/",
            className="sidebar-brand-link",
        ),
        className="sidebar-brand",
    )


def create_nav_icon(
    icon: str,
    label: str,
    path: str,
    current_path: str,
) -> dmc.Tooltip:
    """Create a navigation icon with tooltip.

    Args:
        icon: Iconify icon string.
        label: Tooltip label.
        path: Navigation path.
        current_path: Current page path for active state.

    Returns:
        Tooltip-wrapped navigation icon.
    """
    is_active = current_path == path or (path != "/" and current_path.startswith(path))

    return dmc.Tooltip(
        dcc.Link(
            dmc.ActionIcon(
                DashIconify(icon=icon, width=20),
                variant="subtle" if not is_active else "filled",
                size="lg",
                radius="xl",
                color="blue" if is_active else "gray",
                className="nav-icon-active" if is_active else "",
            ),
            href=path,
        ),
        label=label,
        position="right",
        withArrow=True,
    )


def create_theme_toggle(current_theme: str = "dark") -> dmc.Tooltip:
    """Create the theme toggle button.

    Args:
        current_theme: Current theme ('dark' or 'light').

    Returns:
        Tooltip-wrapped theme toggle icon.
    """
    icon = "tabler:sun" if current_theme == "dark" else "tabler:moon"
    label = "Switch to light mode" if current_theme == "dark" else "Switch to dark mode"

    return dmc.Tooltip(
        dmc.ActionIcon(
            DashIconify(icon=icon, width=20, id="theme-toggle-icon"),
            id="theme-toggle",
            variant="subtle",
            size="lg",
            radius="xl",
            color="gray",
        ),
        label=label,
        position="right",
        withArrow=True,
    )


def create_external_link(url: str, icon: str, label: str) -> dmc.Tooltip:
    """Create an external link icon with tooltip.

    Args:
        url: External URL.
        icon: Iconify icon string.
        label: Tooltip label.

    Returns:
        Tooltip-wrapped external link icon.
    """
    return dmc.Tooltip(
        dmc.Anchor(
            dmc.ActionIcon(
                DashIconify(icon=icon, width=20),
                variant="subtle",
                size="lg",
                radius="xl",
                color="gray",
            ),
            href=url,
            target="_blank",
        ),
        label=label,
        position="right",
        withArrow=True,
    )


def create_sidebar_divider() -> html.Div:
    """Create a horizontal divider for the sidebar."""
    return html.Div(className="sidebar-divider")


def create_sidebar_content(
    current_path: str = "/", current_theme: str = "dark"
) -> list[dmc.Tooltip | html.Div]:
    """Create the sidebar content list.

    Args:
        current_path: Current page path for active state highlighting.
        current_theme: Current theme for toggle icon state.

    Returns:
        List of sidebar components.
    """
    return [
        # Brand logo
        create_brand_logo(),
        create_sidebar_divider(),
        # Main navigation icons
        *[
            create_nav_icon(
                icon=item["icon"],
                label=item["label"],
                path=item["path"],
                current_path=current_path,
            )
            for item in NAV_ITEMS_MAIN
        ],
        create_sidebar_divider(),
        # Dashboard/Project links
        *[
            create_nav_icon(
                icon=item["icon"],
                label=item["label"],
                path=item["path"],
                current_path=current_path,
            )
            for item in NAV_ITEMS_PROJECTS
        ],
        create_sidebar_divider(),
        # Theme toggle
        create_theme_toggle(current_theme),
        create_sidebar_divider(),
        # External links
        *[
            create_external_link(
                url=link["url"],
                icon=link["icon"],
                label=link["label"],
            )
            for link in EXTERNAL_LINKS
        ],
    ]


def create_sidebar(current_path: str = "/", current_theme: str = "dark") -> html.Div:
    """Create the floating sidebar navigation.

    Args:
        current_path: Current page path for active state highlighting.
        current_theme: Current theme for toggle icon state.

    Returns:
        Complete sidebar component.
    """
    return html.Div(
        id="floating-sidebar",
        className="floating-sidebar",
        children=create_sidebar_content(current_path, current_theme),
    )
