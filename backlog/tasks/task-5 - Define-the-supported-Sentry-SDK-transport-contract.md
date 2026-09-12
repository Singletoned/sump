---
id: TASK-5
title: Define the supported Sentry SDK transport contract
status: To Do
assignee: []
created_date: '2026-09-12 17:14'
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
- [ ] #1 Compatibility tests prove that a custom transport receives error envelopes on the minimum and current supported Sentry SDK 2.x versions
- [ ] #2 Compatibility tests prove that event envelopes and attachments survive serialization and deserialization
- [ ] #3 A test establishes whether custom local transport initialization requires a DSN without permitting network delivery
- [ ] #4 A test establishes whether transport write exceptions propagate to the capture caller
- [ ] #5 The tested Sentry SDK version range and any failure-contract limitation are documented
<!-- AC:END -->
