---
id: TASK-12
title: Redeliver errors from expired claims
status: To Do
assignee: []
created_date: '2026-09-12 17:14'
labels:
  - reliability
  - storage
dependencies:
  - TASK-10
  - TASK-11
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Recover work abandoned by a collector while preserving the at-least-once preference for duplicates over loss.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 An active claim remains unchanged for 30 minutes from its recorded claim time
- [ ] #2 The first project operation after expiry makes every occurrence eligible under a new claim ID
- [ ] #3 Acknowledging an expired claim after recovery fails with an explicit stale-claim error
- [ ] #4 Expiry behavior is tested with an injected clock rather than elapsed wall time
<!-- AC:END -->
