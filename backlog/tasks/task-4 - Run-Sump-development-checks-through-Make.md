---
id: TASK-4
title: Run Sump development checks through Make
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-12 17:14'
updated_date: '2026-09-12 17:28'
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
- [x] #1 mate --list shows setup, format, test, check, and build targets with descriptions
- [x] #2 Each listed target succeeds from a clean checkout after setup
- [x] #3 The format and check targets apply the repository Ruff configuration
- [x] #4 The test target runs the built-in unittest suite
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add the standard Ruff configuration and a minimal unittest suite.
2. Add mate-compatible setup, format, test, check, and build Make targets.
3. Run every target and verify mate --list from a clean project copy.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added the standard Ruff configuration, a minimal built-in unittest suite, and mate-compatible setup, format, test, check, and build targets.

Validation: mate listed all five targets. In an isolated project copy, setup, format, test (2 tests), check, and build all succeeded.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added and verified the Make-based development workflow, Ruff checks, unittest execution, and package build targets.
<!-- SECTION:FINAL_SUMMARY:END -->
