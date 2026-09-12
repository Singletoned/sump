---
id: TASK-9
title: Redeliver a project's active error claim
status: To Do
assignee: []
created_date: '2026-09-12 17:14'
labels:
  - core
  - reliability
dependencies:
  - TASK-8
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Provide at-least-once retrieval when a coding agent retries after interruption without requiring it to remember extra recovery state.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A project can have no more than one active claim
- [ ] #2 Repeating sump claim PROJECT before acknowledgement returns the same claim ID
- [ ] #3 A redelivered active claim contains the same ordered occurrences and immutable claim timestamps
- [ ] #4 Events captured after claim creation remain pending for a later claim
<!-- AC:END -->
