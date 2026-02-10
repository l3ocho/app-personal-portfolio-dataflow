# Prompt: UI Layout Adjust

**Track:** consumer
**Target Repo:** personal-portfolio
**Plugins Required:** viz-platform, git-flow
**Version Bump:** none

---

## Context

Interactive UI refinement workflow for non-dashboard pages (home, about, contact, projects, resume, blog). You will iterate on layout, styling, and component adjustments in a live Dash debug session. The user navigates the app in their browser, identifies components via dev tools, and describes changes. You execute them. The app auto-reloads on save.

This prompt does NOT load data-platform skills. If the user navigates to a dashboard page requiring data context, stop and advise starting a new session with the `ui-dashboard-adjust` prompt instead.

---

## Setup (Task 1 — Branch & Server)

1. **Create a feature branch using git-flow:**

```
/gitflow branch-start ui-adjust-<YYYYMMDD>
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
- Dash component ID (e.g., `id="sidebar-nav"`)
- CSS class or selector (e.g., `.page-content-wrapper`)
- File path and approximate location (e.g., `components/sidebar.py line 40`)
- Visual description (e.g., "the blue button in the top right")

If the description is ambiguous, ask ONE clarifying question before proceeding. Prefer asking for the component ID from browser dev tools.

### 2b. Locate & Edit

1. Find the target file(s) using `grep` or direct file navigation
2. Make the requested change — keep edits surgical and minimal
3. **Save the file** — Dash debug mode auto-reloads on save, no restart needed

### 2c. Confirm

Tell the user:
- What file was changed
- What specifically was modified (one sentence)
- Ask them to refresh/check the browser

### 2d. User Response Routing

| User Says | Action |
|-----------|--------|
| Looks good, next change | Loop back to 2a |
| Not quite right / adjust further | Revise the same component (loop 2b) |
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

## Design System Check (Task 2.5 — Before Commit)

Before proceeding to commit, if viz-platform MCP is available, run:

```
/viz design-gate ./portfolio_app/
```

- **PASS** → proceed to commit
- **FAIL** → show violations, fix them, re-run gate

If viz-platform MCP is not available, skip this step and note it was skipped.

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

This handles staging, conventional commit message, merge to development, push, and branch cleanup. When prompted for the commit message, use `style(ui): <brief description>` format. Ask the user for a brief description, or suggest one based on the changes made.

4. **Summary** — list all changes made in the session.

---

## Guardrails

- **No data operations.** If the user asks to modify queries, database connections, dbt models, or data transformations, stop and advise using the `ui-dashboard-adjust` prompt.
- **No callback logic changes** that alter data flow. Cosmetic callback changes (e.g., toggling visibility, changing animation) are fine.
- **Branch protection.** Never commit to `main`, `staging`, or `development` directly. Always use the feature branch.
- **Scope control.** If a requested change would require modifying more than 3 files or involves architectural restructuring, flag it as out-of-scope for this workflow and suggest creating a proper issue instead.

---

## Abort Procedure

If something goes wrong mid-session:

```bash
# Stop server
kill $(cat /tmp/dash-server.pid) 2>/dev/null

# Discard all changes and cleanup branch
git checkout -- .
git checkout development
git branch -D feat/ui-adjust-<YYYYMMDD>
```

Note: Abort uses raw git intentionally — this is an emergency escape, not a normal workflow.
