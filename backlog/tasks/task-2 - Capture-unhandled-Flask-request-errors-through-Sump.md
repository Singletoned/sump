---
id: TASK-2
title: Capture unhandled Flask request errors through Sump
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
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Prove that a Flask application can use Sump with the official Sentry Flask integration and expose useful request errors to coding agents. This is intentionally deferred until the core capture and claim workflow is stable.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 An unhandled Flask request exception is recorded for the configured Sump project
- [ ] #2 The claimed event includes the exception type, message, stack trace, and request context supplied by the Sentry SDK
- [ ] #3 The integration test completes without sending event data over the network
- [ ] #4 Flask setup and supported versions are documented
<!-- AC:END -->
