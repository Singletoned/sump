---
id: TASK-14
title: Serialize concurrent project collectors
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-12 17:14'
updated_date: '2026-09-12 18:30'
labels:
  - reliability
  - concurrency
dependencies:
  - TASK-12
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Prevent simultaneous coding agents from splitting claim state or corrupting project transitions.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Concurrent claim subprocesses for one project return the same active claim ID
- [x] #2 Concurrent claim subprocesses return the same ordered occurrence set
- [x] #3 Concurrent acknowledgement retries leave exactly one retained acknowledged claim
- [x] #4 Interrupted acknowledgement can be retried to a successful or already-acknowledged result
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Wrap every claim and acknowledgement state transition in the existing per-project POSIX advisory lock.
2. Keep validation and registry resolution outside the lock, then run recovery, expiry, publication, and acknowledgement atomically while held.
3. Add simultaneous subprocess claim and acknowledgement tests that compare complete JSON results and retained state.
4. Inject failures immediately before and after the acknowledgement rename and prove retry succeeds in both cases.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Claim and acknowledgement now acquire the private per-project flock before reading or mutating collector state. Staging recovery, expiry, active-claim redelivery, claim publication, and acknowledgement all execute within the same lock; transport capture remains lock-free.

Subprocess tests queue six claim commands behind a held lock and prove every command returns the same complete JSON claim, ID, timestamp data, and occurrence order with one active directory. Six concurrent acknowledgement retries all return the same success response and leave exactly one retained acknowledged directory. Failure injection before the acknowledgement rename and after the rename but before directory fsync proves a subsequent retry succeeds in both states.

Validation: make check passed 37 tests; Sentry compatibility and package build passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Serialized collector state transitions with per-project flock and verified identical concurrent claims, idempotent concurrent acknowledgements, and interruption-safe acknowledgement retries.
<!-- SECTION:FINAL_SUMMARY:END -->
