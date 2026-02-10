# Sprint 9 - Gitea Labels API Requires Org Context

## Context
Creating Gitea issues with labels via MCP tools during Sprint 9 planning for the personal-portfolio project.

## Problem
When calling `create_issue` with a `labels` parameter, received:
```
404 Client Error: Not Found for url: https://gitea.hotserv.cloud/api/v1/orgs/lmiranda/labels
```

The API attempted to fetch labels from an **organization** endpoint, but `lmiranda` is a **user account**, not an organization.

## Solution
Created issues without the `labels` parameter and documented intended labels in the issue body instead:
```markdown
**Labels:** Type/Feature, Priority/Medium, Complexity/Simple, Efforts/XS, Component/Docs, Tech/Python
```

This provides visibility into intended categorization while avoiding the API error.

## Prevention
- When working with user-owned repos (not org repos), avoid using the `labels` parameter in `create_issue`
- Document labels in issue body as a workaround
- Consider creating a repo-level label set for user repos (Gitea supports this)
- Update projman plugin to handle user vs org repos differently

## Tags
gitea, mcp, api, labels, projman, configuration
