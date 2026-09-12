---
id: TASK-11
title: Recover errors from interrupted claim assembly
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-12 17:14'
updated_date: '2026-09-12 18:20'
labels:
  - reliability
  - storage
dependencies:
  - TASK-9
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Ensure a collector crash during multi-file claim construction cannot strand or omit captured occurrences.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A claim becomes visible only after all selected envelopes and immutable claim metadata are complete
- [x] #2 The next project operation returns every envelope from an incomplete staged claim to eligibility
- [x] #3 Failure injection after moving any number of selected envelopes demonstrates that none are omitted
- [x] #4 Multiple active claims or inconsistent claim metadata produce an explicit registry-corruption error
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Assemble claims in a private staging directory and expose them only through one final atomic directory rename.
2. Recover every staged envelope back to pending at the start of claim and acknowledgement operations.
3. Introduce an explicit RegistryCorruptionError for multiple active claims, malformed metadata, and inconsistent directory contents.
4. Inject failures after each envelope transition and before publication to prove complete next-operation recovery.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Claims are now assembled under a private staging/<claim-id> directory. Metadata is fsynced, selected envelopes are moved and the staged directory is fsynced, then one atomic directory rename publishes the complete active claim. Claim and acknowledgement operations first recover all valid staged envelopes to pending and remove incomplete staging state.

Added RegistryCorruptionError and explicit validation for multiple active claims, missing/malformed/mismatched metadata, inconsistent envelope lists, invalid staging entries, and filename collisions. Failure injection interrupts after zero, one, two, or all three envelope moves (including before final publication); every case exposes no active claim and the next operation returns all occurrences in order.

Validation: make check passed 31 tests; Sentry compatibility and package build passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added atomic staged claim publication, deterministic interrupted-claim recovery, exhaustive move-boundary failure tests, and explicit registry-corruption diagnostics.
<!-- SECTION:FINAL_SUMMARY:END -->
