---
id: TASK-3
title: Install Sump from a local wheel
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-12 17:14'
updated_date: '2026-09-12 17:27'
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
- [x] #1 uv resolves and installs the project from a clean checkout on Python 3.10 or newer
- [x] #2 uv build produces both a wheel and source distribution
- [x] #3 Installing the built wheel makes the sump package importable
- [x] #4 Installing the built wheel provides a sump command whose --help invocation succeeds
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add the src-layout Hatchling package metadata and placeholder sump module/CLI.
2. Resolve runtime and development dependencies with uv.
3. Build wheel and source distribution.
4. Install the wheel into an isolated environment and verify import plus sump --help.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Initialized the package with uv using a src layout and Hatchling. Added sentry-sdk 2.x, platformdirs, Ruff, a typed argparse entry point, and standard build/cache ignores.

Validation: uv locked sync succeeded in an isolated Python 3.10.20 project copy; uv build produced dist/sump-0.1.0-py3-none-any.whl and dist/sump-0.1.0.tar.gz; installing the wheel into a temporary environment passed import and sump --help checks.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Created the installable Sump package skeleton and verified clean Python 3.10 sync, wheel/sdist builds, installed import, and CLI help.
<!-- SECTION:FINAL_SUMMARY:END -->
