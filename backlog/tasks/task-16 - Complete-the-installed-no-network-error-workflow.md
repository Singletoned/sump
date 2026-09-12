---
id: TASK-16
title: Complete the installed no-network error workflow
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-12 17:14'
updated_date: '2026-09-12 18:35'
labels:
  - release
  - integration
dependencies:
  - TASK-4
  - TASK-13
  - TASK-14
  - TASK-15
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 16000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Prove that the local alpha's documented user journey works from its built artifact on the supported environment.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A clean temporary environment installs the locally built wheel
- [x] #2 The installed package captures an exception through the real Sentry SDK
- [x] #3 The installed command claims, redelivers, and acknowledges that occurrence using the documented JSON contract
- [x] #4 The smoke workflow fails if any event delivery attempts a network connection
- [x] #5 make check and make build pass before the smoke workflow runs
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add a mate-compatible smoke target that requires check and build before running the installed workflow.
2. Create a temporary Python 3.10 virtual environment, install only the built wheel and its dependencies, and run outside the source tree.
3. Capture a real Sentry exception while instrumenting socket connection APIs so any event-delivery network attempt fails the smoke.
4. Exercise and validate claim, identical redelivery, acknowledgement, retained storage, and final empty JSON through the installed sump command; document the verification command.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added a mate-compatible make smoke target with check and build prerequisites. The smoke runner creates a clean temporary CPython 3.10 virtual environment, installs the locally built wheel with uv, removes PYTHONPATH, and executes outside the source tree.

The installed package captures a real RuntimeError through sentry_sdk.capture_exception while socket.create_connection, socket.socket.connect, and connect_ex record and reject any network attempt. The installed sump command then validates the complete schema-version-1 claim, exact active-claim redelivery, acknowledgement response, retained claim metadata/envelope, and final empty claim. Every check raises explicitly rather than relying on optimizable assert statements. README now documents make smoke.

Validation: make smoke ran make check (37 tests) and make build before creating Python 3.10.20, installing five wheel dependencies, and passing the installed workflow. The Sentry compatibility matrix passed, and mate --list exposes the smoke target.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added and passed a clean Python 3.10 installed-wheel smoke workflow covering real exception capture, prohibited network delivery, claim redelivery, acknowledgement, retention, and empty completion.
<!-- SECTION:FINAL_SUMMARY:END -->
