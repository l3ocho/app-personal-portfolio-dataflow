# Prompt: UI Dashboard Adjust

**Track:** consumer
**Target Repo:** personal-portfolio
**Plugins Required:** viz-platform, data-platform, git-flow
**Version Bump:** none

---

## Context

Interactive UI refinement workflow for **dashboard pages** — pages backed by database queries, dbt models, Plotly figures, and callbacks with data logic. Currently this means the Toronto Neighbourhood Dashboard (`/toronto/*`) and any future data-driven pages.

You will iterate on layout, styling, component adjustments, figure tweaks, callback logic, and query modifications in a live Dash debug session. The user navigates the app in their browser, identifies components via dev tools, and describes changes. You execute them. The app auto-reloads on save.

This prompt loads **data-platform** skills in addition to viz-platform. If the user is working on non-dashboard pages (home, about, contact, projects, resume, blog) and no data context is needed, advise switching to the lighter `ui-layout-adjust` prompt to save tokens.

### Data Context

**Database schemas:** `raw_toronto` → `stg_toronto` → `int_toronto` → `mart_toronto`
**dbt project:** `dbt/` with models mirroring the schema layers
**Figure factories:** `portfolio_app/figures/toronto/`
**Callbacks:** `portfolio_app/pages/toronto/callbacks/`
**Tab layouts:** `portfolio_app/pages/toronto/tabs/`

**Available data-platform MCP tools:**
- PostgreSQL: `pg_query`, `pg_tables`, `pg_columns`, `pg_schemas`
- PostGIS: `st_tables`, `st_geometry_type`, `st_srid`, `st_extent`
- dbt: `dbt_parse`, `dbt_run`, `dbt_test`, `dbt_compile`, `dbt_lineage`, `dbt_ls`
- pandas: `describe`, `head`, `filter`, `select`, `groupby`

Use these tools to understand data shapes before modifying figures or callbacks. Don't guess column names — verify with `pg_columns` or `dbt_compile`.

---

## Setup (Task 1 — Branch & Server)

1. **Create a feature branch using git-flow:**

```
/gitflow branch-start ui-dashboard-<YYYYMMDD>
```

This handles checkout from development, pull, and branch creation. If a branch with today's date exists, append a sequence number.

2. **Start the Dash dev server in the background:**

```bash
nohup python -m portfolio_app.app > /tmp/dash-server.log 2>&1 &
echo $! > /tmp/dash-server.pid
```

3. **Display access links:**

```bash
# Get network IP for remote access (Raspberry Pi SSH scenarios)
NETWORK_IP=$(hostname -I | awk '{print $1}')
echo ""
echo "========================================="
echo "  Dash server running in debug mode"
echo "  Local:   http://localhost:8050"
echo "  Network: http://${NETWORK_IP}:8050"
echo "========================================="
echo ""
```

4. **Confirm ready** — tell the user both links and wait for their first adjustment request.

---

## Iteration Loop (Task 2 — Repeat Until User Says Done)

For each adjustment the user requests:

### 2a. Identify Target

The user provides one or more of:
- Dash component ID (e.g., `id="choropleth-map"`)
- CSS class or selector (e.g., `.tab-content-wrapper`)
- File path and approximate location (e.g., `figures/toronto/overview.py line 85`)
- Callback reference (e.g., "the callback that updates the scatter plot")
- Visual description (e.g., "the bar chart in the housing tab")

If the description is ambiguous, ask ONE clarifying question before proceeding. Prefer asking for the component ID from browser dev tools.

### 2b. Assess Data Impact

Before editing, classify the change:

| Change Type | Data Impact | Action Before Edit |
|-------------|-------------|--------------------|
| Layout / spacing / colors | None | Edit directly |
| Chart title, labels, legend | None | Edit directly |
| Axis range, format, hover template | Low | Verify column names with `pg_columns` or `describe` |
| Filter options, dropdown values | Medium | Query actual distinct values with `pg_query` |
| Callback data logic, aggregations | High | Verify schema with `pg_columns`, check lineage with `dbt_lineage` |
| New data source or column reference | High | Run `dbt_compile` to validate SQL, verify column exists |

For **medium/high** impact changes, run the appropriate data-platform tool BEFORE making the edit. Don't assume column names or data shapes.

### 2c. Locate & Edit

1. Find the target file(s) using `grep` or direct file navigation
2. For figure changes: check `portfolio_app/figures/toronto/` first
3. For callback changes: check `portfolio_app/pages/toronto/callbacks/` first
4. For layout changes: check `portfolio_app/pages/toronto/tabs/` first
5. Make the requested change — keep edits surgical and minimal
6. **Save the file** — Dash debug mode auto-reloads on save, no restart needed

### 2d. Confirm

Tell the user:
- What file was changed
- What specifically was modified (one sentence)
- If data-related: what was verified before editing (e.g., "confirmed column `median_income` exists in `mart_toronto.dim_neighbourhood`")
- Ask them to refresh/check the browser

### 2e. User Response Routing

| User Says | Action |
|-----------|--------|
| Looks good, next change | Loop back to 2a |
| Not quite right / adjust further | Revise the same component (loop 2c) |
| Undo that | Revert the last change with `git checkout -- <file>` |
| Done | Proceed to Task 3 |

---

## Quality Gate (Between Iterations — Lightweight)

After every **3rd change**, run a quick lint check:

```bash
ruff check --select E,W --quiet portfolio_app/
```

Report any issues introduced by recent edits. Fix if trivial, flag if not.

---

## Pre-Commit Gates (Task 2.5 — Before Commit)

Run both domain gates before proceeding to commit:

### Design System Gate

If viz-platform MCP is available:

```
/viz design-gate ./portfolio_app/
```

- **PASS** → proceed to data gate
- **FAIL** → show violations, fix them, re-run gate

### Data Integrity Gate

If data-platform MCP is available:

```
/data gate ./portfolio_app/ ./dbt/
```

- **PASS** → proceed to commit
- **FAIL** → show violations, fix them, re-run gate

If either MCP is not available, skip that gate and note it was skipped.

---

## Commit & Merge (Task 3 — When User Says Done)

1. **Stop the dev server:**

```bash
kill $(cat /tmp/dash-server.pid) 2>/dev/null
rm -f /tmp/dash-server.pid /tmp/dash-server.log
```

2. **Review all changes:**

```bash
git diff --stat
```

Show the user a summary of all files changed.

3. **Commit and merge using git-flow:**

```
/gitflow commit --merge
```

This handles staging, conventional commit message, merge to development, push, and branch cleanup. When prompted for the commit message, use the appropriate type prefix based on changes made:
- `style(dashboard):` for purely visual changes
- `feat(dashboard):` for new functionality or data features
- `fix(dashboard):` for bug fixes in figures or callbacks

Ask the user for a brief description, or suggest one based on the changes made.

4. **Summary** — list all changes made in the session, grouped by type (layout, figures, callbacks, data).

---

## Guardrails

- **No dbt model creation or deletion.** Modifying existing queries in callbacks or figures is fine. Creating new dbt models or dropping existing ones is out-of-scope — create an issue instead.
- **No schema migrations.** Don't create, alter, or drop database tables. Read-only data verification is always allowed.
- **Branch protection.** Never commit to `main`, `staging`, or `development` directly. Always use the feature branch.
- **Scope control.** If a requested change would require modifying more than 5 files or involves architectural restructuring, flag it as out-of-scope for this workflow and suggest creating a proper issue instead.
- **Verify before assuming.** Never hardcode column names, table names, or data values without verifying against the actual database or dbt models first.

---

## Abort Procedure

If something goes wrong mid-session:

```bash
# Stop server
kill $(cat /tmp/dash-server.pid) 2>/dev/null

# Discard all changes and cleanup branch
git checkout -- .
git checkout development
git branch -D feat/ui-dashboard-<YYYYMMDD>
```

Note: Abort uses raw git intentionally — this is an emergency escape, not a normal workflow.
