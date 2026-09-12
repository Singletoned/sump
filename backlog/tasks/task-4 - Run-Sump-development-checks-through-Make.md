---
id: TASK-4
title: Run Sump development checks through Make
status: To Do
assignee: []
created_date: '2026-09-12 17:14'
labels:
  - tooling
dependencies:
  - TASK-3
references:
  - IMPLEMENTATION_PLAN.md
priority: medium
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Give contributors one documented, repeatable interface for formatting, testing, checking, and building the package.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 mate --list shows setup, format, test, check, and build targets with descriptions
- [ ] #2 Each listed target succeeds from a clean checkout after setup
- [ ] #3 The format and check targets apply the repository Ruff configuration
- [ ] #4 The test target runs the built-in unittest suite
<!-- AC:END -->
