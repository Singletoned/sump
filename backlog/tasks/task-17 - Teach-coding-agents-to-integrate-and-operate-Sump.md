---
id: TASK-17
title: Teach coding agents to integrate and operate Sump
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-13 20:56'
updated_date: '2026-09-13 20:58'
labels:
  - cli
  - documentation
dependencies: []
references:
  - README.md
priority: high
ordinal: 17000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Coding agents need a self-contained prompt from the installed CLI that explains how to add Sump to an application, collect local errors safely, and feed product shortcomings back to Sump's maintainers.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 sump instructions PROJECT prints self-contained application integration steps using the supplied project slug
- [x] #2 The instructions explain claim, redelivery, acknowledgement, empty results, expiry, batch size, and duplicate handling
- [x] #3 The instructions direct agents to report concrete shortcomings and needed features to the user rather than silently working around them
- [x] #4 Invalid project slugs fail with the same explicit validation contract as application initialization
- [x] #5 Automated tests verify the command's output and project-specific examples
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add a project-specific sump instructions PROJECT subcommand that validates the slug and emits a standalone Markdown prompt.
2. Cover installation, initialization, normal Sentry capture, claim/redelivery/acknowledgement/drain semantics, and concrete feedback expectations in the prompt.
3. Test the parser, rendered project-specific commands, required operational guidance, and shared invalid-slug behavior.
4. Add the command to the README and installed-wheel smoke verification.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added sump instructions PROJECT, which emits an 81-line standalone Markdown prompt after applying the same project-slug validator used by sump.init. The prompt covers local-alpha installation, early initialization, preservation of Sentry options and integrations, managed dsn/transport behavior, local verification, and SUMP_STATE_DIR consistency.

The collection guidance covers schema-version-1 JSON, oldest-first batches of up to 100, active-claim redelivery, 30-minute expiry, at-least-once duplicates, durable downstream work before idempotent acknowledgement, stale claims, and draining until a null claim. It explicitly directs agents to report concrete improvement opportunities and needed features with evidence rather than silently working around them.

Added CLI tests for project-specific output, required workflow and feedback directives, help visibility, and validation parity. Updated README and the installed-wheel smoke workflow so the packaged command is exercised outside the source tree. Validation: 39 tests passed, make smoke passed on a clean temporary Python 3.10.20 environment, the Sentry SDK compatibility matrix passed, and git diff --check passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added a tested project-specific LLM instruction command covering Sump integration, safe error collection, duplicate semantics, and mandatory product-feedback reporting.
<!-- SECTION:FINAL_SUMMARY:END -->
