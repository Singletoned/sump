---
id: TASK-1
title: Capture unhandled Django request errors through Sump
status: Backburner
assignee: []
created_date: '2026-09-12 17:03'
updated_date: '2026-09-12 17:14'
labels: []
dependencies:
  - TASK-16
references:
  - IMPLEMENTATION_PLAN.md
priority: low
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Prove that a Django application can use Sump with the official Sentry Django integration and expose useful request errors to coding agents. This is intentionally deferred until the core capture and claim workflow is stable.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 An unhandled Django request exception is recorded for the configured Sump project
- [ ] #2 The claimed event includes the exception type, message, stack trace, and request context supplied by the Sentry SDK
- [ ] #3 The integration test completes without sending event data over the network
- [ ] #4 Django setup and supported versions are documented
<!-- AC:END -->
