# Sprint 9 - Always Read CLAUDE.md Before Asking Questions

## Context
Starting Sprint 9 planning session with `/projman:sprint-plan` command.

## Problem
Asked the user "what should I do?" when all the necessary context was already documented in CLAUDE.md:
- Current sprint number and phase
- Implementation plan location
- Remaining phases to complete
- Project conventions and workflows

This caused user frustration: "why are you asking what to do? cant you see this yourself"

## Solution
Before asking any questions about what to do:
1. Read `CLAUDE.md` in the project root
2. Check "Project Status" section for current sprint/phase
3. Follow references to implementation plans
4. Review "Projman Plugin Workflow" section for expected behavior

## Prevention
- **ALWAYS** read CLAUDE.md at the start of any sprint-related command
- Look for "Current Sprint" and "Phase" indicators
- Check for implementation plan references in `docs/changes/`
- Only ask questions if information is genuinely missing from documentation
- The projman plugin expects autonomous behavior based on documented context

## Tags
projman, claude-code, context, documentation, workflow, sprint-planning
