# Project Lessons Learned

This folder contains lessons learned from sprints and development work. These lessons help prevent repeating mistakes and capture valuable insights.

**Note:** Sprint-level lessons are also captured in the Gitea wiki via `/projman sprint-close`. This folder serves as the local reference archive.

---

## Lessons Index

| Date | Sprint/Phase | Title | Tags | Relevant? |
|------|--------------|-------|------|-----------|
| 2026-01-16 | Phase 4 | [dbt Test Syntax Deprecation](./phase-4-dbt-test-syntax.md) | dbt, testing, yaml, deprecation | ✅ Data pipeline |
| 2026-01-17 | Sprint 9 | [Gitea Labels API Requires Org Context](./sprint-9-gitea-labels-user-repos.md) | gitea, mcp, api, labels, projman, configuration | ✅ Workflow |
| 2026-01-17 | Sprint 9 | [Always Read CLAUDE.md Before Asking Questions](./sprint-9-read-claude-md-first.md) | projman, claude-code, context, documentation, workflow | ✅ Workflow |
| 2026-01-17 | Sprint 9-10 | [Graceful Error Handling in Service Layers](./sprint-9-10-graceful-error-handling.md) | python, postgresql, error-handling, graceful-degradation, arm64 | ✅ Data pipeline |
| 2026-01-17 | Sprint 9-10 | [Modular Callback Structure](./sprint-9-10-modular-callback-structure.md) | dash, callbacks, architecture, python | ⚠️ Webapp only |
| 2026-01-17 | Sprint 9-10 | [Figure Factory Pattern](./sprint-9-10-figure-factory-pattern.md) | plotly, dash, design-patterns, python, visualization | ⚠️ Webapp only |
| 2026-02-01 | Sprint 10 | [Formspree Integration with Dash Callbacks](./sprint-10-formspree-dash-integration.md) | formspree, dash, callbacks, forms | ⚠️ Webapp only |

> **⚠️ Webapp only** — lessons marked as such relate to the Dash frontend which lives in the `personal-portfolio` webapp repository. They are kept here for historical reference.

---

## How to Use

### When Starting a Sprint
1. Review relevant lessons in this folder before implementation
2. Search by tags or keywords to find applicable insights
3. Apply prevention strategies from past lessons

### When Closing a Sprint
1. Document any significant lessons learned
2. Use the template below
3. Add entry to the index table above

---

## Lesson Template

```markdown
# [Sprint/Phase] - [Lesson Title]

## Context
[What were you trying to do?]

## Problem
[What went wrong or what insight emerged?]

## Solution
[How did you solve it?]

## Prevention
[How can this be avoided in future sprints?]

## Tags
[Comma-separated tags for search]
```
