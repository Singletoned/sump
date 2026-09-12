---
id: TASK-15
title: Document the coding-agent collection workflow
status: To Do
assignee: []
created_date: '2026-09-12 17:14'
labels:
  - documentation
dependencies:
  - TASK-10
  - TASK-12
references:
  - IMPLEMENTATION_PLAN.md
priority: medium
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Give developers and coding agents an exact contract for configuring applications and processing local errors safely.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 README instructions initialize an application with an explicit project slug
- [ ] #2 README examples show claim, repeated delivery, acknowledgement, and empty-result behavior
- [ ] #3 The schema_version 1 claim and acknowledgement fields are documented
- [ ] #4 The documentation states the 100-occurrence limit, 30-minute expiry, and at-least-once duplicate behavior
- [ ] #5 The default registry location, SUMP_STATE_DIR override, sensitive-data permissions, and indefinite retention are documented
<!-- AC:END -->
