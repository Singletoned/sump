---
id: TASK-13
title: Preserve captured errors from concurrent writers
status: To Do
assignee: []
created_date: '2026-09-12 17:14'
labels:
  - reliability
  - concurrency
dependencies:
  - TASK-7
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Keep successful application captures complete and collectible when multiple local processes write to one project.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Concurrent subprocess writers produce one uniquely identified occurrence per successful capture
- [ ] #2 Every occurrence produced by concurrent writers deserializes as a complete Sentry envelope
- [ ] #3 A collector holding the project claim lock does not block a transport write
- [ ] #4 No successfully captured occurrence is omitted from successive acknowledged claim batches
<!-- AC:END -->
