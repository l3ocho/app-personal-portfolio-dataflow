"""Blog index page - Article listing."""

import dash
import dash_mantine_components as dmc
from dash import dcc
from dash_iconify import DashIconify

from portfolio_app.utils.markdown_loader import Article, get_all_articles

dash.register_page(__name__, path="/blog", name="Blog")

# Page intro
INTRO_TEXT = (
    "I write occasionally about data engineering, automation, and the reality of being "
    "a one-person data team. No hot takes, no growth hacking—just things I've learned "
    "the hard way."
)


def create_article_card(article: Article) -> dmc.Paper:
    """Create an article preview card."""
    meta = article["meta"]
    return dmc.Paper(
        dcc.Link(
            dmc.Stack(
                [
                    dmc.Group(
                        [
                            dmc.Text(meta["title"], fw=600, size="lg"),
                            dmc.Text(meta["date"], size="sm", c="dimmed"),
                        ],
                        justify="space-between",
                        align="flex-start",
                        wrap="wrap",
                    ),
                    dmc.Text(meta["description"], size="md", c="dimmed", lineClamp=2),
                    dmc.Group(
                        [
                            dmc.Badge(tag, variant="light", size="sm")
                            for tag in meta.get("tags", [])[:3]
                        ],
                        gap="xs",
                    ),
                ],
                gap="sm",
            ),
            href=f"/blog/{meta['slug']}",
            style={"textDecoration": "none", "color": "inherit"},
        ),
        p="lg",
        radius="md",
        withBorder=True,
        className="article-card",
    )


def create_empty_state() -> dmc.Paper:
    """Create empty state when no articles exist."""
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.ThemeIcon(
                    DashIconify(icon="tabler:article-off", width=48),
                    size=80,
                    radius="xl",
                    variant="light",
                    color="gray",
                ),
                dmc.Title("No Articles Yet", order=3),
                dmc.Text(
                    "Articles are coming soon. Check back later!",
                    size="md",
                    c="dimmed",
                    ta="center",
                ),
            ],
            align="center",
            gap="md",
            py="xl",
        ),
        p="xl",
        radius="md",
        withBorder=True,
    )


def layout() -> dmc.Container:
    """Generate the blog index layout dynamically."""
    articles = get_all_articles(include_drafts=False)

    return dmc.Container(
        dmc.Stack(
            [
                dmc.Title("Blog", order=1, ta="center"),
                dmc.Text(
                    INTRO_TEXT, size="md", c="dimmed", ta="center", maw=600, mx="auto"
                ),
                dmc.Divider(my="lg"),
                (
                    dmc.Stack(
                        [create_article_card(article) for article in articles],
                        gap="lg",
                    )
                    if articles
                    else create_empty_state()
                ),
                dmc.Space(h=40),
            ],
            gap="lg",
        ),
        size="md",
        py="xl",
    )
