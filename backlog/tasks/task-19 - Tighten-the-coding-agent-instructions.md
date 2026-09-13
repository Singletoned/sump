---
id: TASK-19
title: Tighten the coding-agent instructions
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-13 21:07'
updated_date: '2026-09-13 21:09'
labels:
  - cli
  - documentation
dependencies: []
references:
  - TASK-18
priority: high
ordinal: 19000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The argument-free instructions are complete but verbose and open with awkward implementation jargon. They should read as direct, useful operating instructions for both humans and coding agents.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 sump instructions opens with a direct description of what to do rather than asking the reader to derive a slug
- [x] #2 The complete output is no more than 65 lines
- [x] #3 The concise output retains setup, slug selection, claim, retry, acknowledgement, empty-result, duplicate, and improvement-reporting guidance
- [x] #4 Tests and installed-wheel verification pass with the revised text
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Replace the long prompt with direct setup, collection, retry, acknowledgement, and feedback sections capped at 65 lines.
2. Phrase slug selection in terms of the project name and metadata, avoiding abstract jargon.
3. Strengthen CLI tests for the concise shape while preserving every required workflow marker.
4. Run formatting, checks, compatibility, and installed-wheel smoke verification.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Rewrote the prompt around direct actions: choose the project name, install Sump, replace Sentry initialization, process claims, and report Sump issues. Removed the awkward “derive one stable project slug” opening and condensed repetitive explanation while retaining slug validation, SUMP_STATE_DIR consistency, local-only scope, raw event/attachment handling, durable backlog creation, acknowledgement, retry, expiry, duplicates, and feedback reporting.

Added regression expectations that the prompt stays at or below 65 lines and does not reintroduce the rejected phrase. The final output is 60 lines and 384 words, down from 93 lines before this task.

Validation: the new concision test failed against the previous 93-line prompt before the rewrite; all 39 tests pass; make smoke passed against the installed wheel in clean Python 3.10.20; the Sentry SDK compatibility matrix passed; git diff --check passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Replaced the verbose agent prompt with a direct 60-line setup, processing, and feedback guide.
<!-- SECTION:FINAL_SUMMARY:END -->
