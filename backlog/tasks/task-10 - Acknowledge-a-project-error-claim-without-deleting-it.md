---
id: TASK-10
title: Acknowledge a project error claim without deleting it
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-12 17:14'
updated_date: '2026-09-12 18:17'
labels:
  - core
  - cli
dependencies:
  - TASK-9
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Let coding agents mark a represented batch complete while preserving its source records for later inspection.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 sump acknowledge PROJECT CLAIM_ID returns versioned JSON confirming acknowledgement
- [x] #2 Acknowledged occurrences do not appear in later normal claims
- [x] #3 Acknowledged claim metadata and envelopes remain in local registry storage
- [x] #4 Repeating acknowledgement for the same project and claim ID returns success
- [x] #5 An unknown project or claim ID produces a non-zero command failure
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add an acknowledged registry area and validate claim IDs and persisted claim state.
2. Acknowledge by atomically moving the active claim directory into retained acknowledged storage and fsyncing both directories.
3. Return the same versioned success response for first and repeated acknowledgement.
4. Add CLI coverage for retention, exclusion from later claims, idempotency, and unknown project/claim failures.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added sump acknowledge PROJECT CLAIM_ID and a versioned acknowledgement response. Acknowledgement validates project/claim identity, atomically moves the complete active claim directory into private acknowledged storage, and fsyncs both source and destination directories. Existing acknowledged claims are validated and return the same success response; unknown projects and claims fail with full CLI tracebacks.

Tests prove acknowledged envelope bytes and claim metadata remain unchanged, acknowledged occurrences are excluded from subsequent claims, retry is idempotent, and later pending events remain collectible. Validation: make check passed 29 tests; Sentry compatibility and package build passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implemented atomic, retained, idempotent claim acknowledgement with versioned CLI output and explicit unknown-claim failures.
<!-- SECTION:FINAL_SUMMARY:END -->
