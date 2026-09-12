---
id: TASK-14
title: Serialize concurrent project collectors
status: To Do
assignee: []
created_date: '2026-09-12 17:14'
labels:
  - reliability
  - concurrency
dependencies:
  - TASK-12
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Prevent simultaneous coding agents from splitting claim state or corrupting project transitions.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Concurrent claim subprocesses for one project return the same active claim ID
- [ ] #2 Concurrent claim subprocesses return the same ordered occurrence set
- [ ] #3 Concurrent acknowledgement retries leave exactly one retained acknowledged claim
- [ ] #4 Interrupted acknowledgement can be retried to a successful or already-acknowledged result
<!-- AC:END -->
