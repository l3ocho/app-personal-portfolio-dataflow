"""Blog article page - Dynamic routing for individual articles."""

import dash
import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify

from portfolio_app.utils.markdown_loader import get_article

dash.register_page(
    __name__,
    path_template="/blog/<slug>",
    name="Article",
)


def create_not_found() -> dmc.Container:
    """Create 404 state for missing articles."""
    return dmc.Container(
        dmc.Stack(
            [
                dmc.ThemeIcon(
                    DashIconify(icon="tabler:file-unknown", width=48),
                    size=80,
                    radius="xl",
                    variant="light",
                    color="red",
                ),
                dmc.Title("Article Not Found", order=2),
                dmc.Text(
                    "The article you're looking for doesn't exist or has been moved.",
                    size="md",
                    c="dimmed",
                    ta="center",
                ),
                dcc.Link(
                    dmc.Button(
                        "Back to Blog",
                        variant="light",
                        leftSection=DashIconify(icon="tabler:arrow-left", width=18),
                    ),
                    href="/blog",
                ),
            ],
            align="center",
            gap="md",
            py="xl",
        ),
        size="md",
        py="xl",
    )


def layout(slug: str = "") -> dmc.Container:
    """Generate the article layout dynamically.

    Args:
        slug: Article slug from URL path.
    """
    if not slug:
        return create_not_found()

    article = get_article(slug)
    if not article:
        return create_not_found()

    meta = article["meta"]

    return dmc.Container(
        dmc.Stack(
            [
                # Back link
                dcc.Link(
                    dmc.Group(
                        [
                            DashIconify(icon="tabler:arrow-left", width=16),
                            dmc.Text("Back to Blog", size="sm"),
                        ],
                        gap="xs",
                    ),
                    href="/blog",
                    style={"textDecoration": "none"},
                ),
                # Article header
                dmc.Paper(
                    dmc.Stack(
                        [
                            dmc.Title(meta["title"], order=1),
                            dmc.Group(
                                [
                                    dmc.Group(
                                        [
                                            DashIconify(
                                                icon="tabler:calendar", width=16
                                            ),
                                            dmc.Text(
                                                meta["date"], size="sm", c="dimmed"
                                            ),
                                        ],
                                        gap="xs",
                                    ),
                                    dmc.Group(
                                        [
                                            dmc.Badge(tag, variant="light", size="sm")
                                            for tag in meta.get("tags", [])
                                        ],
                                        gap="xs",
                                    ),
                                ],
                                justify="space-between",
                                wrap="wrap",
                            ),
                            (
                                dmc.Text(meta["description"], size="lg", c="dimmed")
                                if meta.get("description")
                                else None
                            ),
                        ],
                        gap="sm",
                    ),
                    p="xl",
                    radius="md",
                    withBorder=True,
                ),
                # Article content
                dmc.Paper(
                    html.Div(
                        # Render HTML content from markdown
                        # Using dangerously_allow_html via dcc.Markdown or html.Div
                        dcc.Markdown(
                            article["content"],
                            className="article-content",
                            dangerously_allow_html=True,
                        ),
                    ),
                    p="xl",
                    radius="md",
                    withBorder=True,
                    className="article-body",
                ),
                dmc.Space(h=40),
            ],
            gap="lg",
        ),
        size="md",
        py="xl",
    )
