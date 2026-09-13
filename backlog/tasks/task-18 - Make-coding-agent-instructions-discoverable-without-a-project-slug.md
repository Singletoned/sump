---
id: TASK-18
title: Make coding-agent instructions discoverable without a project slug
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-13 21:01'
updated_date: '2026-09-13 21:03'
labels:
  - cli
  - bug
dependencies: []
references:
  - TASK-17
priority: high
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The instructions command currently requires the project slug before it explains how to choose and use that slug, so a new integrator cannot invoke it without already knowing part of the workflow.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 sump instructions succeeds without positional arguments
- [x] #2 The output tells the agent how to derive a stable valid slug from the project and ask the user only when ambiguous
- [x] #3 Integration, claim, and acknowledgement examples consistently show the agent where to substitute the chosen slug
- [x] #4 Passing an unexpected argument to sump instructions is rejected by the CLI
- [x] #5 Unit and installed-wheel smoke tests exercise the argument-free command
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Change sump instructions and its renderer to accept no project argument.
2. Replace interpolated examples with a clearly defined PROJECT_SLUG placeholder and teach the agent to derive a valid stable slug from project metadata, consulting the user only when ambiguous.
3. Update CLI tests, README usage, and installed-wheel smoke coverage for the argument-free interface.
4. Run formatting, checks, compatibility, and the installed-wheel workflow.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Changed sump instructions to take no positional arguments, removing the circular requirement to know a slug before reading how Sump works. The standalone prompt now tells agents to inspect authoritative project metadata or the repository name, normalize it to Sump’s slug contract, use it consistently, and ask the user only when multiple application identities make the choice ambiguous.

All integration and collection examples use the explicit PROJECT_SLUG placeholder and warn not to copy it unchanged. Updated README usage, CLI tests, and installed-wheel smoke coverage. Added a negative test proving an unexpected argument exits 2.

Validation: the regression tests failed against the argument-requiring behavior before the fix; all 39 tests now pass; make smoke built and installed the wheel in clean Python 3.10.20 and passed; the Sentry SDK compatibility matrix passed; explicit unexpected-argument verification exited 2; git diff --check passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Made sump instructions argument-free and taught agents to derive, validate, and consistently substitute the project slug themselves.
<!-- SECTION:FINAL_SUMMARY:END -->
