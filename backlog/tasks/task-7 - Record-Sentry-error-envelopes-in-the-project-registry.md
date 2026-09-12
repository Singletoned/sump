---
id: TASK-7
title: Record Sentry error envelopes in the project registry
status: To Do
assignee: []
created_date: '2026-09-12 17:14'
labels:
  - core
  - storage
dependencies:
  - TASK-6
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Persist each captured error or message as a complete local occurrence without exposing partial records to collectors.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Captured exceptions and messages create separate pending occurrences under the configured project
- [ ] #2 Envelopes without an event item do not create pending occurrences
- [ ] #3 Each pending occurrence preserves the complete serialized envelope and associated attachments
- [ ] #4 A collector cannot observe a pending occurrence before its complete contents are durably installed
- [ ] #5 Registry directories and event files deny group and world access
- [ ] #6 Permission, malformed-path, and disk write failures surface as explicit errors
<!-- AC:END -->
