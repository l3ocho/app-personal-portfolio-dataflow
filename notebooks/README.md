# Dashboard Documentation Notebooks

Documentation notebooks organized by dashboard project. Each notebook documents how data is queried, transformed, and visualized using the figure factory pattern.

## Directory Structure

```
notebooks/
├── README.md              # This file
└── toronto/               # Toronto Neighbourhood Dashboard
    ├── overview/          # Overview tab visualizations
    ├── housing/           # Housing tab visualizations
    ├── safety/            # Safety tab visualizations
    ├── demographics/      # Demographics tab visualizations
    └── amenities/         # Amenities tab visualizations
```

## Notebook Template

Each notebook follows a standard two-section structure:

### Section 1: Data Reference

Documents the data pipeline:
- **Source Tables**: List of dbt marts/tables used
- **SQL Query**: The exact query to fetch data
- **Transformation Steps**: Any pandas/python transformations
- **Sample Output**: First 10 rows of the result

### Section 2: Data Visualization

Documents the figure creation:
- **Figure Factory**: Import from `portfolio_app.figures`
- **Parameters**: Key configuration options
- **Rendered Output**: The actual visualization

## Available Figure Factories

| Factory | Module | Use Case |
|---------|--------|----------|
| `create_choropleth` | `figures.choropleth` | Map visualizations |
| `create_ranking_bar` | `figures.bar_charts` | Top/bottom N rankings |
| `create_stacked_bar` | `figures.bar_charts` | Category breakdowns |
| `create_scatter` | `figures.scatter` | Correlation plots |
| `create_radar` | `figures.radar` | Multi-metric comparisons |
| `create_age_pyramid` | `figures.demographics` | Age distributions |
| `create_time_series` | `figures.time_series` | Trend lines |

## Usage

1. Start Jupyter from project root:
   ```bash
   jupyter notebook notebooks/
   ```

2. Ensure database is running:
   ```bash
   make docker-up
   ```

3. Each notebook is self-contained - run all cells top to bottom.

## Notebook Naming Convention

`{metric}_{chart_type}.ipynb`

Examples:
- `livability_choropleth.ipynb`
- `crime_trend_line.ipynb`
- `age_pyramid.ipynb`
