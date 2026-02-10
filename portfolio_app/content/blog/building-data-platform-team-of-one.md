---
title: "Building a Data Platform as a Team of One"
date: "2025-01-15"
description: "What I learned from 5 years as the sole data professional at a mid-size company"
tags:
  - data-engineering
  - career
  - lessons-learned
status: published
---

When I joined Summitt Energy in 2019, there was no data infrastructure. No warehouse. No pipelines. No documentation. Just a collection of spreadsheets and a Genesys Cloud instance spitting out CSVs.

Five years later, I'd built DataFlow: an enterprise platform processing 1B+ rows across 21 tables, feeding dashboards that executives actually opened. Here's what I learned doing it alone.

## The Reality of "Full Stack Data"

When you're the only data person, "full stack" isn't a buzzword—it's survival. In a single week, I might:

- Debug a Python ETL script at 7am because overnight loads failed
- Present quarterly metrics to leadership at 10am
- Design a new dimensional model over lunch
- Write SQL transformations in the afternoon
- Handle ad-hoc "can you pull this data?" requests between meetings

There's no handoff. No "that's not my job." Everything is your job.

## Prioritization Frameworks

The hardest part isn't the technical work—it's deciding what to build first when everything feels urgent.

### The 80/20 Rule, Applied Ruthlessly

I asked myself: **What 20% of the data drives 80% of decisions?**

For a contact center, that turned out to be:
- Call volume by interval
- Abandon rate
- Average handle time
- Service level

Everything else was nice-to-have. I built those four metrics first, got them bulletproof, then expanded.

### The "Who's Screaming?" Test

When multiple stakeholders want different things:
1. Who has executive backing?
2. What's blocking revenue?
3. What's causing visible pain?

If nobody's screaming, it can probably wait.

## Technical Debt vs. Shipping

I rewrote DataFlow three times:

- **v1 (2020)**: Hacky Python scripts. Worked, barely.
- **v2 (2021)**: Proper dimensional model. Still messy code.
- **v3 (2022)**: SQLAlchemy ORM, proper error handling, logging.
- **v4 (2023)**: dbt-style transformations, FastAPI layer.

Was v1 embarrassing? Yes. Did it work? Also yes.

**The lesson**: Ship something that works, then iterate. Perfect is the enemy of done, especially when you're alone.

## Building Stakeholder Trust

The technical work is maybe 40% of the job. The rest is politics.

### Quick Wins First

Before asking for resources or patience, I delivered:
- Automated a weekly report that took someone 4 hours
- Fixed a dashboard that had been wrong for months
- Built a simple tool that answered a frequent question

Trust is earned in small deposits.

### Speak Their Language

Executives don't care about your star schema. They care about:
- "This will save 10 hours/week"
- "This will catch errors before they hit customers"
- "This will let you see X in real-time"

Translate technical work into business outcomes.

## What I'd Do Differently

1. **Document earlier**. I waited too long. When I finally wrote things down, onboarding became possible.

2. **Say no more**. Every "yes" to an ad-hoc request is a "no" to infrastructure work. Guard your time.

3. **Build monitoring first**. I spent too many mornings discovering failures manually. Alerting should be table stakes.

4. **Version control everything**. Even SQL. Even documentation. If it's not in Git, it doesn't exist.

## The Upside

Being a team of one forced me to learn things I'd have specialized away from on a bigger team:
- Data modeling
- Pipeline architecture
- Dashboard design
- Stakeholder management
- System administration

It's brutal, but it makes you dangerous. You understand the whole stack.

---

*This is part of a series on building data infrastructure at small companies. More posts coming on dimensional modeling, dbt patterns, and surviving legacy systems.*
