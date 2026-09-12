---
id: TASK-3
title: Install Sump from a local wheel
status: To Do
assignee: []
created_date: '2026-09-12 17:14'
labels:
  - tooling
  - packaging
dependencies: []
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Provide the minimum package structure and metadata needed to install Sump locally on its supported Python versions.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 uv resolves and installs the project from a clean checkout on Python 3.10 or newer
- [ ] #2 uv build produces both a wheel and source distribution
- [ ] #3 Installing the built wheel makes the sump package importable
- [ ] #4 Installing the built wheel provides a sump command whose --help invocation succeeds
<!-- AC:END -->
