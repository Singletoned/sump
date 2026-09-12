---
id: TASK-13
title: Preserve captured errors from concurrent writers
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-12 17:14'
updated_date: '2026-09-12 18:27'
labels:
  - reliability
  - concurrency
dependencies:
  - TASK-7
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Keep successful application captures complete and collectible when multiple local processes write to one project.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Concurrent subprocess writers produce one uniquely identified occurrence per successful capture
- [x] #2 Every occurrence produced by concurrent writers deserializes as a complete Sentry envelope
- [x] #3 A collector holding the project claim lock does not block a transport write
- [x] #4 No successfully captured occurrence is omitted from successive acknowledged claim batches
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add a private per-project POSIX claim-lock primitive while keeping transport capture completely lock-free.
2. Launch multiple subprocess writers against one project and verify unique files and complete deserializable envelopes.
3. Hold the project lock while a subprocess captures to prove collector coordination cannot block transport writes.
4. Drain all concurrent captures through successive 100-item claims and acknowledgements and verify no successful capture is omitted.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added a per-project POSIX advisory claim-lock primitive backed by a private project.lock file. Transport storage remains lock-free and does not inspect or acquire this lock.

Subprocess tests launch six writers concurrently, each synchronously capturing 20 events into one project. All 120 successful captures produce unique filenames, deserialize as complete Sentry envelopes, and preserve the exact message set. Successive claim/acknowledge batches contain 100 and 20 events with no duplicates or omissions. A separate subprocess capture completes while the parent process holds the project claim lock.

Validation: make check passed 35 tests; Sentry compatibility and package build passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Verified lock-free concurrent transport writes with unique durable envelopes, non-blocking capture under the collector lock, and omission-free multi-batch collection.
<!-- SECTION:FINAL_SUMMARY:END -->
