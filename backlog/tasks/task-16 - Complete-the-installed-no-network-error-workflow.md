---
id: TASK-16
title: Complete the installed no-network error workflow
status: To Do
assignee: []
created_date: '2026-09-12 17:14'
labels:
  - release
  - integration
dependencies:
  - TASK-4
  - TASK-13
  - TASK-14
  - TASK-15
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 16000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Prove that the local alpha's documented user journey works from its built artifact on the supported environment.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A clean temporary environment installs the locally built wheel
- [ ] #2 The installed package captures an exception through the real Sentry SDK
- [ ] #3 The installed command claims, redelivers, and acknowledges that occurrence using the documented JSON contract
- [ ] #4 The smoke workflow fails if any event delivery attempts a network connection
- [ ] #5 make check and make build pass before the smoke workflow runs
<!-- AC:END -->
