# Analytics Portfolio

[![CI](https://gitea.hotserv.cloud/lmiranda/personal-portfolio/actions/workflows/ci.yml/badge.svg)](https://gitea.hotserv.cloud/lmiranda/personal-portfolio/actions)

**Live Demo:** [leodata.science](https://leodata.science)

A personal portfolio website showcasing data engineering and visualization capabilities, featuring an interactive Toronto Neighbourhood Dashboard.

## Live Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Bio landing page |
| `/about` | About | Background and experience |
| `/projects` | Projects | Portfolio project showcase |
| `/resume` | Resume | Professional CV |
| `/contact` | Contact | Contact form |
| `/blog` | Blog | Technical articles |
| `/blog/{slug}` | Article | Individual blog posts |
| `/toronto` | Toronto Dashboard | Neighbourhood analysis (5 tabs) |
| `/toronto/methodology` | Methodology | Dashboard data sources and methods |
| `/health` | Health | API health check endpoint |

## Toronto Neighbourhood Dashboard

An interactive choropleth dashboard analyzing Toronto's 158 official neighbourhoods across five dimensions:

- **Overview**: Composite livability scores, income vs safety scatter
- **Housing**: Affordability index, rent trends, dwelling types
- **Safety**: Crime rates, breakdowns by type, trend analysis
- **Demographics**: Income distribution, age pyramids, population density
- **Amenities**: Parks, schools, transit accessibility

**Data Sources**:
- City of Toronto Open Data Portal (neighbourhoods, census profiles, amenities)
- Toronto Police Service (crime statistics)
- CMHC Rental Market Survey (rental data by zone)

## Architecture

```mermaid
flowchart LR
    subgraph Sources
        A1[City of Toronto API]
        A2[Toronto Police API]
        A3[CMHC Data]
    end

    subgraph ETL
        B1[Parsers]
        B2[Loaders]
    end

    subgraph Database
        C1[(PostgreSQL/PostGIS)]
        C2[dbt Models]
    end

    subgraph Application
        D1[Dash App]
        D2[Plotly Figures]
    end

    A1 & A2 & A3 --> B1 --> B2 --> C1 --> C2 --> D1 --> D2
```

**Pipeline Stages:**
- **Sources**: External APIs and data files (City of Toronto, Toronto Police, CMHC)
- **ETL**: Python parsers extract and validate data; loaders persist to database
- **Database**: PostgreSQL with PostGIS for geospatial; dbt transforms raw → staging → marts
- **Application**: Dash serves interactive dashboards with Plotly visualizations

For detailed database schema, see [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md).

## Quick Start

```bash
# Clone and setup
git clone https://gitea.hotserv.cloud/lmiranda/personal-portfolio.git
cd personal-portfolio

# Install dependencies and configure environment
make setup

# Start database
make docker-up

# Initialize database schema
make db-init

# Run development server
make run
```

Visit `http://localhost:8050` to view the portfolio.

## Project Structure

```
portfolio_app/
├── app.py                 # Dash app factory
├── config.py              # Pydantic settings
├── pages/
│   ├── home.py            # Bio landing (/)
│   ├── about.py           # About page
│   ├── contact.py         # Contact form
│   ├── projects.py        # Project showcase
│   ├── resume.py          # Resume/CV
│   ├── blog/              # Blog system
│   │   ├── index.py       # Article listing
│   │   └── article.py     # Article renderer
│   └── toronto/           # Toronto dashboard
│       ├── dashboard.py   # Main layout with tabs
│       ├── methodology.py # Data documentation
│       ├── tabs/          # Tab layouts (5)
│       └── callbacks/     # Interaction logic
├── components/            # Shared UI components
├── figures/
│   └── toronto/           # Toronto figure factories
├── content/
│   └── blog/              # Markdown blog articles
├── toronto/               # Toronto data logic
│   ├── parsers/           # API data extraction
│   ├── loaders/           # Database operations
│   ├── schemas/           # Pydantic models
│   └── models/            # SQLAlchemy ORM (raw_toronto schema)
└── errors/                # Exception handling

dbt/                       # dbt project: portfolio
├── models/
│   ├── shared/            # Cross-domain dimensions
│   ├── staging/toronto/   # Toronto staging models
│   ├── intermediate/toronto/ # Toronto intermediate models
│   └── marts/toronto/     # Toronto analytical tables

notebooks/
└── toronto/               # Toronto documentation (15 notebooks)
    ├── overview/          # Overview tab visualizations
    ├── housing/           # Housing tab visualizations
    ├── safety/            # Safety tab visualizations
    ├── demographics/      # Demographics tab visualizations
    └── amenities/         # Amenities tab visualizations

docs/
├── PROJECT_REFERENCE.md   # Architecture reference
├── CONTRIBUTING.md        # Developer guide
└── project-lessons-learned/
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Database | PostgreSQL 16 + PostGIS |
| Validation | Pydantic 2.x |
| ORM | SQLAlchemy 2.x |
| Transformation | dbt-postgres |
| Data Processing | Pandas, GeoPandas |
| Visualization | Dash + Plotly |
| UI Components | dash-mantine-components |
| Testing | pytest |
| Python | 3.11+ |

## Development

```bash
make test      # Run pytest
make lint      # Run ruff linter
make format    # Format code
make ci        # Run all checks
make dbt-run   # Run dbt models
make dbt-test  # Run dbt tests
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/portfolio
POSTGRES_USER=portfolio
POSTGRES_PASSWORD=<secure>
POSTGRES_DB=portfolio
DASH_DEBUG=true
SECRET_KEY=<random>
```

## Documentation

- **For developers**: See `docs/CONTRIBUTING.md` for setup and contribution guidelines
- **For Claude Code**: See `CLAUDE.md` for AI assistant context
- **Architecture**: See `docs/PROJECT_REFERENCE.md` for technical details

## License

MIT

## Author

Leo Miranda
