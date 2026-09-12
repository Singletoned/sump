---
id: TASK-6
title: Initialize Sentry SDK for a local Sump project
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-12 17:14'
updated_date: '2026-09-12 17:32'
labels:
  - core
  - sentry
dependencies:
  - TASK-5
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Let applications opt into local capture with a small Sentry-like initialization call while preventing accidental remote delivery.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 sump.init accepts a valid explicit project slug and initializes the Sentry SDK with Sump's transport
- [x] #2 Sentry options other than dsn and transport are forwarded unchanged
- [x] #3 Caller-supplied dsn or transport options raise a clear configuration error
- [x] #4 Missing or invalid project identifiers raise a clear validation error without creating registry files
- [x] #5 Initialization does not send data over the network
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add strict project-slug validation and a configured local transport type.
2. Implement sump.init as a typed wrapper that rejects dsn/transport conflicts and forwards all other options.
3. Test real SDK initialization, option forwarding, validation failures, and network isolation.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added sump.init with lowercase project-slug validation and explicit rejection of caller-managed dsn/transport options. Other SDK options are forwarded to a configured LocalTransport. Invalid configuration is rejected before registry access.

The actual SDK initialization test runs with socket connection creation disabled and confirms the active client uses LocalTransport with no parsed DSN. Until TASK-7 adds storage, capture_envelope fails loudly instead of dropping an event.

Validation: make check passed 10 tests; make compatibility still passed on sentry-sdk 2.0.0 and 2.69.1.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added the local-only sump.init API with project validation, safe Sentry option forwarding, conflict rejection, and no-network initialization tests.
<!-- SECTION:FINAL_SUMMARY:END -->
