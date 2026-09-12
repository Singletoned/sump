---
id: TASK-6
title: Initialize Sentry SDK for a local Sump project
status: To Do
assignee: []
created_date: '2026-09-12 17:14'
labels:
  - core
  - sentry
dependencies:
  - TASK-5
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Let applications opt into local capture with a small Sentry-like initialization call while preventing accidental remote delivery.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 sump.init accepts a valid explicit project slug and initializes the Sentry SDK with Sump's transport
- [ ] #2 Sentry options other than dsn and transport are forwarded unchanged
- [ ] #3 Caller-supplied dsn or transport options raise a clear configuration error
- [ ] #4 Missing or invalid project identifiers raise a clear validation error without creating registry files
- [ ] #5 Initialization does not send data over the network
<!-- AC:END -->
