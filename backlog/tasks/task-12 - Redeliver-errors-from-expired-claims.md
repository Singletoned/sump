---
id: TASK-12
title: Redeliver errors from expired claims
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-12 17:14'
updated_date: '2026-09-12 18:24'
labels:
  - reliability
  - storage
dependencies:
  - TASK-10
  - TASK-11
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Recover work abandoned by a collector while preserving the at-least-once preference for duplicates over loss.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 An active claim remains unchanged for 30 minutes from its recorded claim time
- [x] #2 The first project operation after expiry makes every occurrence eligible under a new claim ID
- [x] #3 Acknowledging an expired claim after recovery fails with an explicit stale-claim error
- [x] #4 Expiry behavior is tested with an injected clock rather than elapsed wall time
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add an injectable UTC clock seam and strict parsing of immutable claim expiry metadata.
2. On each claim or acknowledgement operation, move an expired active claim through staging, recover every envelope to pending, and retain an expiry tombstone.
3. Create the replacement claim normally with a new ID while preserving occurrence identity and order.
4. Raise an explicit stale-claim error when an expired claim ID is acknowledged, and test lease boundaries without sleeping.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added strict immutable lease validation and a patchable UTC clock seam. Active claims are redelivered unchanged until expires_at; at the exact 30-minute boundary, the active directory moves through staging, all envelopes return to pending, and normal claim creation assigns a new claim ID.

Expired claim metadata is retained as a private tombstone so acknowledgement of an old ID raises StaleClaimError even after a replacement claim exists. Expiry recovery uses the existing staged recovery path, preserving at-least-once delivery across interruption boundaries. Tests inject exact clock values before and at expiry without sleeping, verify unchanged pre-expiry output, identical occurrences under a new ID, direct acknowledgement-triggered recovery, immutable tombstone metadata, and repeated stale acknowledgement.

Validation: make check passed 33 tests; Sentry compatibility and package build passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implemented deterministic 30-minute claim expiry, staged envelope recovery into replacement claims, retained stale-ID tombstones, and explicit stale acknowledgement errors.
<!-- SECTION:FINAL_SUMMARY:END -->
