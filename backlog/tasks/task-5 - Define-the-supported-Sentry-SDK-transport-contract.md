---
id: TASK-5
title: Define the supported Sentry SDK transport contract
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-12 17:14'
updated_date: '2026-09-12 17:30'
labels:
  - sentry
  - compatibility
dependencies:
  - TASK-3
references:
  - IMPLEMENTATION_PLAN.md
  - 'https://docs.sentry.io/platforms/python/migration/1.x-to-2.x'
  - 'https://getsentry.github.io/sentry-python/_modules/sentry_sdk/transport.html'
priority: high
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Establish the tested Sentry SDK 2.x behavior that Sump can safely build on before committing its public capture API.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Compatibility tests prove that a custom transport receives error envelopes on the minimum and current supported Sentry SDK 2.x versions
- [x] #2 Compatibility tests prove that event envelopes and attachments survive serialization and deserialization
- [x] #3 A test establishes whether custom local transport initialization requires a DSN without permitting network delivery
- [x] #4 A test establishes whether transport write exceptions propagate to the capture caller
- [x] #5 The tested Sentry SDK version range and any failure-contract limitation are documented
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add an executable transport-contract test covering custom envelope delivery, serialization, attachments, DSN behavior, network isolation, and write exceptions.
2. Run the contract against the selected minimum Sentry SDK 2.x release and the current locked release.
3. Narrow or document the supported range and failure semantics from the observed results.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Contract results on sentry-sdk 2.0.0 and locked 2.69.1: a custom transport receives event envelopes without a DSN; event and attachment bytes survive Envelope serialization; and synchronous transport OSError exceptions propagate to the capture caller. Added a compatibility Make target that runs the same three contract tests against both endpoints.

Validation: make compatibility passed 3 tests on each SDK endpoint; make check passed 5 tests.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Defined and tested the Sentry SDK 2.x custom transport contract, including no-DSN capture, envelope attachments, no network endpoint, and fail-loud write exceptions.
<!-- SECTION:FINAL_SUMMARY:END -->
