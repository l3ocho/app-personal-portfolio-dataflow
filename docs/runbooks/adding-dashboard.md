# Runbook: Adding a New Dashboard

This runbook describes how to add a new data dashboard to the portfolio application.

## Prerequisites

- [ ] Data sources identified and accessible
- [ ] Database schema designed
- [ ] Basic Dash/Plotly familiarity

## Directory Structure

Create the following structure:

### Application Code (`portfolio_app/`)

```
portfolio_app/
├── pages/
│   └── {dashboard_name}/
│       ├── dashboard.py      # Main layout with tabs
│       ├── methodology.py    # Data sources and methods page
│       ├── tabs/
│       │   ├── __init__.py
│       │   ├── overview.py   # Overview tab layout
│       │   └── ...           # Additional tab layouts
│       └── callbacks/
│           ├── __init__.py
│           └── ...           # Callback modules
├── {dashboard_name}/         # Data logic (outside pages/)
│   ├── __init__.py
│   ├── parsers/              # API/CSV extraction
│   │   └── __init__.py
│   ├── loaders/              # Database operations
│   │   └── __init__.py
│   ├── schemas/              # Pydantic models
│   │   └── __init__.py
│   └── models/               # SQLAlchemy ORM (schema: raw_{dashboard_name})
│       └── __init__.py
└── figures/
    └── {dashboard_name}/     # Figure factories for this dashboard
        ├── __init__.py
        └── ...               # Chart modules
```

### dbt Models (`dbt/models/`)

```
dbt/models/
├── staging/
│   └── {dashboard_name}/     # Staging models
│       ├── _sources.yml      # Source definitions (schema: raw_{dashboard_name})
│       ├── _staging.yml      # Model tests/docs
│       └── stg_*.sql         # Staging models
├── intermediate/
│   └── {dashboard_name}/     # Intermediate models
│       ├── _intermediate.yml
│       └── int_*.sql
└── marts/
    └── {dashboard_name}/     # Mart tables
        ├── _marts.yml
        └── mart_*.sql
```

### Documentation (`notebooks/`)

```
notebooks/
└── {dashboard_name}/         # Domain subdirectories
    ├── overview/
    ├── ...
```

## Step-by-Step Checklist

### 1. Data Layer

- [ ] Create Pydantic schemas in `{dashboard_name}/schemas/`
- [ ] Create SQLAlchemy models in `{dashboard_name}/models/`
- [ ] Create parsers in `{dashboard_name}/parsers/`
- [ ] Create loaders in `{dashboard_name}/loaders/`
- [ ] Add database migrations if needed

### 2. Database Schema

- [ ] Define schema constant in models (e.g., `RAW_FOOTBALL_SCHEMA = "raw_football"`)
- [ ] Add `__table_args__ = {"schema": RAW_FOOTBALL_SCHEMA}` to all models
- [ ] Update `scripts/db/init_schema.py` to create the new schema

### 3. dbt Models

Create dbt models in `dbt/models/`:

- [ ] `staging/{dashboard_name}/_sources.yml` - Source definitions pointing to `raw_{dashboard_name}` schema
- [ ] `staging/{dashboard_name}/stg_{source}__{entity}.sql` - Raw data cleaning
- [ ] `intermediate/{dashboard_name}/int_{domain}__{transform}.sql` - Business logic
- [ ] `marts/{dashboard_name}/mart_{domain}.sql` - Final analytical tables

Update `dbt/dbt_project.yml` with new subdirectory config:
```yaml
models:
  portfolio:
    staging:
      {dashboard_name}:
        +materialized: view
        +schema: stg_{dashboard_name}
    intermediate:
      {dashboard_name}:
        +materialized: view
        +schema: int_{dashboard_name}
    marts:
      {dashboard_name}:
        +materialized: table
        +schema: mart_{dashboard_name}
```

Follow naming conventions:
- Staging: `stg_{source}__{entity}`
- Intermediate: `int_{domain}__{transform}`
- Marts: `mart_{domain}`

### 4. Visualization Layer

- [ ] Create figure factories in `figures/{dashboard_name}/`
- [ ] Create `figures/{dashboard_name}/__init__.py` with exports
- [ ] Follow the factory pattern: `create_{chart_type}_figure(data, **kwargs)`

Import pattern:
```python
from portfolio_app.figures.{dashboard_name} import create_choropleth_figure
```

### 4. Dashboard Pages

#### Main Dashboard (`pages/{dashboard_name}/dashboard.py`)

```python
import dash
from dash import html, dcc
import dash_mantine_components as dmc

dash.register_page(
    __name__,
    path="/{dashboard_name}",
    title="{Dashboard Title}",
    description="{Description}"
)

def layout():
    return dmc.Container([
        # Header
        dmc.Title("{Dashboard Title}", order=1),

        # Tabs
        dmc.Tabs([
            dmc.TabsList([
                dmc.TabsTab("Overview", value="overview"),
                # Add more tabs
            ]),
            dmc.TabsPanel(overview_tab(), value="overview"),
            # Add more panels
        ], value="overview"),
    ])
```

#### Tab Layouts (`pages/{dashboard_name}/tabs/`)

- [ ] Create one file per tab
- [ ] Export layout function from each

#### Callbacks (`pages/{dashboard_name}/callbacks/`)

- [ ] Create callback modules for interactivity
- [ ] Import and register in dashboard.py

### 5. Navigation

Add to sidebar in `components/sidebar.py`:

```python
dmc.NavLink(
    label="{Dashboard Name}",
    href="/{dashboard_name}",
    icon=DashIconify(icon="..."),
)
```

### 6. Documentation

- [ ] Create methodology page (`pages/{dashboard_name}/methodology.py`)
- [ ] Document data sources
- [ ] Document transformation logic
- [ ] Add notebooks to `notebooks/{dashboard_name}/` if needed

### 7. Testing

- [ ] Add unit tests for parsers
- [ ] Add unit tests for loaders
- [ ] Add integration tests for callbacks
- [ ] Run `make test`

### 8. Final Verification

- [ ] All pages render without errors
- [ ] All callbacks respond correctly
- [ ] Data loads successfully
- [ ] dbt models run cleanly (`make dbt-run`)
- [ ] Linting passes (`make lint`)
- [ ] Tests pass (`make test`)

## Example: Toronto Dashboard

Reference implementation: `portfolio_app/pages/toronto/`

Key files:
- `dashboard.py` - Main layout with 5 tabs
- `tabs/overview.py` - Livability scores, scatter plots
- `callbacks/map_callbacks.py` - Choropleth interactions
- `toronto/models/dimensions.py` - Dimension tables
- `toronto/models/facts.py` - Fact tables

## Common Patterns

### Figure Factories

```python
# figures/choropleth.py
def create_choropleth_figure(
    gdf: gpd.GeoDataFrame,
    value_column: str,
    title: str,
    **kwargs
) -> go.Figure:
    ...
```

### Callbacks

```python
# callbacks/map_callbacks.py
@callback(
    Output("neighbourhood-details", "children"),
    Input("choropleth-map", "clickData"),
)
def update_details(click_data):
    ...
```

### Data Loading

```python
# {dashboard_name}/loaders/load.py
def load_data(session: Session) -> None:
    # Parse from source
    records = parse_source_data()

    # Validate with Pydantic
    validated = [Schema(**r) for r in records]

    # Load to database
    for record in validated:
        session.add(Model(**record.model_dump()))

    session.commit()
```
