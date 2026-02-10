# Sprint 9-10 - Graceful Error Handling in Service Layers

## Context
Building the Toronto Neighbourhood Dashboard with a service layer that queries PostgreSQL/PostGIS dbt marts to provide data to Dash callbacks.

## Problem
Initial service layer implementation let database connection errors propagate as unhandled exceptions. When the PostGIS Docker container was unavailable (common on ARM64 systems where the x86_64 image fails), the entire dashboard would crash instead of gracefully degrading.

## Solution
Wrapped database queries in try/except blocks to return empty DataFrames/lists/dicts when the database is unavailable:

```python
def _execute_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params)
    except Exception:
        return pd.DataFrame()
```

This allows:
1. Dashboard to load and display empty states
2. Development/testing without running database
3. Graceful degradation in production

## Prevention
- **Always design service layers with graceful degradation** - assume external dependencies can fail
- **Return empty collections, not exceptions** - let UI components handle empty states
- **Test without database** - verify the app doesn't crash when DB is unavailable
- **Consider ARM64 compatibility** - PostGIS images may not support all platforms

## Tags
python, postgresql, service-layer, error-handling, dash, graceful-degradation, arm64
