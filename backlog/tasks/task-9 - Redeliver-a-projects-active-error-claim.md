---
id: TASK-9
title: Redeliver a project's active error claim
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-12 17:14'
updated_date: '2026-09-12 18:15'
labels:
  - core
  - reliability
dependencies:
  - TASK-8
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Provide at-least-once retrieval when a coding agent retries after interruption without requiring it to remember extra recovery state.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A project can have no more than one active claim
- [x] #2 Repeating sump claim PROJECT before acknowledgement returns the same claim ID
- [x] #3 A redelivered active claim contains the same ordered occurrences and immutable claim timestamps
- [x] #4 Events captured after claim creation remain pending for a later claim
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Detect and validate the single persisted active claim before considering pending occurrences.
2. Rebuild redelivery JSON from immutable claim metadata and its recorded envelope order.
3. Fail plainly on multiple active claims or inconsistent active-claim contents.
4. Test stable repeat delivery and ensure newly captured events remain pending.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Claim now checks for an existing active claim before inspecting pending occurrences, validates that exactly one claim directory and its immutable metadata agree, and reconstructs output in the originally recorded occurrence order. Multiple active claims and inconsistent claim state fail plainly rather than selecting one. Events captured after claim creation remain untouched in pending while retries return byte-equivalent JSON data.

Validation: make check passed 26 tests; Sentry compatibility passed on 2.0.0 and 2.69.1.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added stable active-claim redelivery with immutable metadata/order, pending-event isolation, and explicit multiple-claim corruption detection.
<!-- SECTION:FINAL_SUMMARY:END -->
