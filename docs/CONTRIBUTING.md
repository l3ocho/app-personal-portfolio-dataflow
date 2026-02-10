# Developer Guide

Instructions for contributing to the Analytics Portfolio project.

---

## Table of Contents

1. [Development Setup](#development-setup)
2. [Adding a Blog Post](#adding-a-blog-post)
3. [Adding a New Page](#adding-a-new-page)
4. [Adding a Dashboard Tab](#adding-a-dashboard-tab)
5. [Creating Figure Factories](#creating-figure-factories)
6. [Branch Workflow](#branch-workflow)
7. [Code Standards](#code-standards)

---

## Development Setup

### Prerequisites

- Python 3.11+ (via pyenv)
- Docker and Docker Compose
- Git

### Initial Setup

```bash
# Clone repository
git clone https://gitea.hotserv.cloud/lmiranda/personal-portfolio.git
cd personal-portfolio

# Run setup (creates venv, installs deps, copies .env.example)
make setup

# Start PostgreSQL + PostGIS
make docker-up

# Initialize database
make db-init

# Start development server
make run
```

The app runs at `http://localhost:8050`.

### Useful Commands

```bash
make test       # Run tests
make test-cov   # Run tests with coverage
make lint       # Check code style
make format     # Auto-format code
make typecheck  # Run mypy type checker
make ci         # Run all checks (lint, typecheck, test)
make dbt-run    # Run dbt transformations
make dbt-test   # Run dbt tests
```

---

## Adding a Blog Post

Blog posts are Markdown files with YAML frontmatter, stored in `portfolio_app/content/blog/`.

### Step 1: Create the Markdown File

Create a new file in `portfolio_app/content/blog/`:

```bash
touch portfolio_app/content/blog/your-article-slug.md
```

The filename becomes the URL slug: `/blog/your-article-slug`

### Step 2: Add Frontmatter

Every blog post requires YAML frontmatter at the top:

```markdown
---
title: "Your Article Title"
date: "2026-01-17"
description: "A brief description for the article card (1-2 sentences)"
tags:
  - data-engineering
  - python
  - lessons-learned
status: published
---

Your article content starts here...
```

**Required fields:**

| Field | Description |
|-------|-------------|
| `title` | Article title (displayed on cards and page) |
| `date` | Publication date in `YYYY-MM-DD` format |
| `description` | Short summary for article listing cards |
| `tags` | List of tags (displayed as badges) |
| `status` | `published` or `draft` (drafts are hidden from listing) |

### Step 3: Write Content

Use standard Markdown:

```markdown
## Section Heading

Regular paragraph text.

### Subsection

- Bullet points
- Another point

```python
# Code blocks with syntax highlighting
def example():
    return "Hello"
```

**Bold text** and *italic text*.

> Blockquotes for callouts
```

### Step 4: Test Locally

```bash
make run
```

Visit `http://localhost:8050/blog` to see the article listing.
Visit `http://localhost:8050/blog/your-article-slug` for the full article.

### Example: Complete Blog Post

```markdown
---
title: "Building ETL Pipelines with Python"
date: "2026-01-17"
description: "Lessons from building production data pipelines at scale"
tags:
  - python
  - etl
  - data-engineering
status: published
---

When I started building data pipelines, I made every mistake possible...

## The Problem

Most tutorials show toy examples. Real pipelines are different.

### Error Handling

```python
def safe_transform(df: pd.DataFrame) -> pd.DataFrame:
    try:
        return df.apply(transform_row, axis=1)
    except ValueError as e:
        logger.error(f"Transform failed: {e}")
        raise
```

## Conclusion

Ship something that works, then iterate.
```

---

## Adding a New Page

Pages use Dash's automatic routing based on file location in `portfolio_app/pages/`.

### Step 1: Create the Page File

```bash
touch portfolio_app/pages/your_page.py
```

### Step 2: Register the Page

Every page must call `dash.register_page()`:

```python
"""Your page description."""

import dash
import dash_mantine_components as dmc

dash.register_page(
    __name__,
    path="/your-page",      # URL path
    name="Your Page",       # Display name (for nav)
    title="Your Page Title" # Browser tab title
)


def layout() -> dmc.Container:
    """Page layout function."""
    return dmc.Container(
        dmc.Stack(
            [
                dmc.Title("Your Page", order=1),
                dmc.Text("Page content here."),
            ],
            gap="lg",
        ),
        size="md",
        py="xl",
    )
```

### Step 3: Page with Dynamic Content

For pages with URL parameters:

```python
# pages/blog/article.py
dash.register_page(
    __name__,
    path_template="/blog/<slug>",  # Dynamic parameter
    name="Article",
)


def layout(slug: str = "") -> dmc.Container:
    """Layout receives URL parameters as arguments."""
    article = get_article(slug)
    if not article:
        return dmc.Text("Article not found")

    return dmc.Container(
        dmc.Title(article["meta"]["title"]),
        # ...
    )
```

### Step 4: Add Navigation (Optional)

To add the page to the sidebar, edit `portfolio_app/components/sidebar.py`:

```python
# For main pages (Home, About, Blog, etc.)
NAV_ITEMS_MAIN = [
    {"path": "/", "icon": "tabler:home", "label": "Home"},
    {"path": "/your-page", "icon": "tabler:star", "label": "Your Page"},
    # ...
]

# For project/dashboard pages
NAV_ITEMS_PROJECTS = [
    {"path": "/projects", "icon": "tabler:folder", "label": "Projects"},
    {"path": "/your-dashboard", "icon": "tabler:chart-bar", "label": "Your Dashboard"},
    # ...
]
```

The sidebar uses icon buttons with tooltips. Each item needs `path`, `icon` (Tabler icon name), and `label` (tooltip text).

### URL Routing Summary

| File Location | URL |
|---------------|-----|
| `pages/home.py` | `/` (if `path="/"`) |
| `pages/about.py` | `/about` |
| `pages/blog/index.py` | `/blog` |
| `pages/blog/article.py` | `/blog/<slug>` |
| `pages/toronto/dashboard.py` | `/toronto` |

---

## Adding a Dashboard Tab

Dashboard tabs are in `portfolio_app/pages/toronto/tabs/`.

### Step 1: Create Tab Layout

```python
# pages/toronto/tabs/your_tab.py
"""Your tab description."""

import dash_mantine_components as dmc

from portfolio_app.figures.toronto.choropleth import create_choropleth
from portfolio_app.toronto.demo_data import get_demo_data


def create_your_tab_layout() -> dmc.Stack:
    """Create the tab layout."""
    data = get_demo_data()

    return dmc.Stack(
        [
            dmc.Grid(
                [
                    dmc.GridCol(
                        # Map on left
                        create_choropleth(data, "your_metric"),
                        span=8,
                    ),
                    dmc.GridCol(
                        # KPI cards on right
                        create_kpi_cards(data),
                        span=4,
                    ),
                ],
            ),
            # Charts below
            create_supporting_charts(data),
        ],
        gap="lg",
    )
```

### Step 2: Register in Dashboard

Edit `pages/toronto/dashboard.py` to add the tab:

```python
from portfolio_app.pages.toronto.tabs.your_tab import create_your_tab_layout

# In the tabs list:
dmc.TabsTab("Your Tab", value="your-tab"),

# In the panels:
dmc.TabsPanel(create_your_tab_layout(), value="your-tab"),
```

---

## Creating Figure Factories

Figure factories are organized by dashboard domain under `portfolio_app/figures/{domain}/`.

### Pattern

```python
# figures/toronto/your_chart.py
"""Your chart type factory for Toronto dashboard."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def create_your_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str = "",
) -> go.Figure:
    """Create a your_chart figure.

    Args:
        df: DataFrame with data.
        x_col: Column for x-axis.
        y_col: Column for y-axis.
        title: Optional chart title.

    Returns:
        Configured Plotly figure.
    """
    fig = px.bar(df, x=x_col, y=y_col, title=title)

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=40, t=40, b=40),
    )

    return fig
```

### Export from `__init__.py`

```python
# figures/toronto/__init__.py
from .your_chart import create_your_chart

__all__ = [
    "create_your_chart",
    # ...
]
```

### Importing Figure Factories

```python
# In callbacks or tabs
from portfolio_app.figures.toronto import create_choropleth_figure
from portfolio_app.figures.toronto.bar_charts import create_ranking_bar
```

---

## Branch Workflow

```
main (production)
  ↑
staging (pre-production)
  ↑
development (integration)
  ↑
feature/XX-description (your work)
```

### Creating a Feature Branch

```bash
# Start from development
git checkout development
git pull origin development

# Create feature branch
git checkout -b feature/10-add-new-page

# Work, commit, push
git add .
git commit -m "feat: Add new page"
git push -u origin feature/10-add-new-page
```

### Merging

```bash
# Merge into development
git checkout development
git merge feature/10-add-new-page
git push origin development

# Delete feature branch
git branch -d feature/10-add-new-page
git push origin --delete feature/10-add-new-page
```

**Rules:**
- Never commit directly to `main` or `staging`
- Never delete `development`
- Feature branches are temporary

---

## Code Standards

### Type Hints

Use Python 3.10+ style:

```python
def process(items: list[str], config: dict[str, int] | None = None) -> bool:
    ...
```

### Imports

| Context | Style |
|---------|-------|
| Same directory | `from .module import X` |
| Sibling directory | `from ..schemas.model import Y` |
| External packages | `import pandas as pd` |

### Formatting

```bash
make format  # Runs ruff formatter
make lint    # Checks style
```

### Docstrings

Google style, only for non-obvious functions:

```python
def calculate_score(values: list[float], weights: list[float]) -> float:
    """Calculate weighted score.

    Args:
        values: Raw metric values.
        weights: Weight for each metric.

    Returns:
        Weighted average score.
    """
    ...
```

---

## Questions?

Check `CLAUDE.md` for AI assistant context and architectural decisions.
