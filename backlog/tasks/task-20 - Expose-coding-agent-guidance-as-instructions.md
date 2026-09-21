---
id: TASK-20
title: Expose coding-agent guidance as --instructions
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-21 07:41'
updated_date: '2026-09-21 07:47'
labels:
  - cli
dependencies: []
references:
  - TASK-19
priority: high
ordinal: 20000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The coding-agent guide should be a top-level CLI flag so its invocation is immediately recognizable as command-line help rather than a workflow subcommand.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 sump --instructions prints the coding-agent guide and exits successfully
- [x] #2 The obsolete sump instructions subcommand is rejected
- [x] #3 CLI help, README usage, tests, and installed-wheel smoke coverage use sump --instructions
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add --instructions as a top-level argparse action and remove the instructions subparser.
2. Update CLI tests first to prove the old interface fails and the new flag works.
3. Update README and installed-wheel smoke usage.
4. Run formatting, checks, compatibility, and installed-wheel smoke verification.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Replaced the instructions subcommand with a top-level --instructions flag. A dedicated argparse action writes the Markdown directly to stdout so argparse does not collapse headings, code blocks, or line breaks. The normal required-subcommand behavior remains unchanged for operational commands.

Updated CLI help assertions, README examples and stream documentation, and the installed-wheel smoke invocation. Added regression coverage proving the old sump instructions spelling is rejected as an invalid command.

Validation: the new tests failed against the subcommand interface before implementation; all 40 tests now pass; make smoke built and tested the installed wheel in clean Python 3.10.20; the Sentry SDK compatibility matrix passed; explicit CLI help and old-command rejection checks passed; git diff --check passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Moved the coding-agent guide from sump instructions to the explicit sump --instructions flag.
<!-- SECTION:FINAL_SUMMARY:END -->
