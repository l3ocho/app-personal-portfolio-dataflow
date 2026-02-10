"""Markdown article loader with frontmatter support."""

from pathlib import Path
from typing import TypedDict

import frontmatter
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension

# Content directory (relative to this file's package)
CONTENT_DIR = Path(__file__).parent.parent / "content" / "blog"


class ArticleMeta(TypedDict):
    """Article metadata from frontmatter."""

    slug: str
    title: str
    date: str
    description: str
    tags: list[str]
    status: str  # "published" or "draft"


class Article(TypedDict):
    """Full article with metadata and content."""

    meta: ArticleMeta
    content: str
    html: str


def render_markdown(content: str) -> str:
    """Convert markdown to HTML with syntax highlighting.

    Args:
        content: Raw markdown string.

    Returns:
        HTML string with syntax-highlighted code blocks.
    """
    md = markdown.Markdown(
        extensions=[
            FencedCodeExtension(),
            CodeHiliteExtension(css_class="highlight", guess_lang=False),
            TableExtension(),
            TocExtension(permalink=True),
            "nl2br",
        ]
    )
    return str(md.convert(content))


def get_article(slug: str) -> Article | None:
    """Load a single article by slug.

    Args:
        slug: Article slug (filename without .md extension).

    Returns:
        Article dict or None if not found.
    """
    filepath = CONTENT_DIR / f"{slug}.md"
    if not filepath.exists():
        return None

    post = frontmatter.load(filepath)

    meta: ArticleMeta = {
        "slug": slug,
        "title": post.get("title", slug.replace("-", " ").title()),
        "date": str(post.get("date", "")),
        "description": post.get("description", ""),
        "tags": post.get("tags", []),
        "status": post.get("status", "published"),
    }

    return {
        "meta": meta,
        "content": post.content,
        "html": render_markdown(post.content),
    }


def get_all_articles(include_drafts: bool = False) -> list[Article]:
    """Load all articles from the content directory.

    Args:
        include_drafts: If True, include articles with status="draft".

    Returns:
        List of articles sorted by date (newest first).
    """
    if not CONTENT_DIR.exists():
        return []

    articles: list[Article] = []
    for filepath in CONTENT_DIR.glob("*.md"):
        slug = filepath.stem
        article = get_article(slug)
        if article and (include_drafts or article["meta"]["status"] == "published"):
            articles.append(article)

    # Sort by date descending
    articles.sort(key=lambda a: a["meta"]["date"], reverse=True)
    return articles
