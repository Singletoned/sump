---
id: TASK-7
title: Record Sentry error envelopes in the project registry
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-12 17:14'
updated_date: '2026-09-12 17:35'
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
- [x] #1 Captured exceptions and messages create separate pending occurrences under the configured project
- [x] #2 Envelopes without an event item do not create pending occurrences
- [x] #3 Each pending occurrence preserves the complete serialized envelope and associated attachments
- [x] #4 A collector cannot observe a pending occurrence before its complete contents are durably installed
- [x] #5 Registry directories and event files deny group and world access
- [x] #6 Permission, malformed-path, and disk write failures surface as explicit errors
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Resolve and create a private per-user registry layout only when an event is captured.
2. Persist event envelopes through same-filesystem temporary files, fsync, and atomic rename into project pending storage.
3. Filter non-event envelopes and keep transport flush/kill synchronous no-ops.
4. Add real SDK capture, attachment, permissions, partial-write, malformed-path, permission, and disk-failure tests.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added platformdirs-based state resolution with an absolute SUMP_STATE_DIR override, private root/project/pending/tmp directories, and 0600 envelope files. LocalTransport now filters non-event envelopes and synchronously stores event envelopes through a same-filesystem temporary file, file fsync, atomic replace, and pending-directory fsync.

Partial serialization and file-sync failures leave no visible pending occurrence. Exact serialized envelopes retain attachments. Explicit tests cover exceptions, messages, ignored envelopes, permissions, malformed roots, relative/empty overrides, permission failures, and disk-sync failures.

Validation: make check passed 20 tests; the Sentry compatibility matrix remained green on 2.0.0 and 2.69.1.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implemented durable private event-envelope capture with event filtering, atomic pending visibility, attachment preservation, and fail-loud storage errors.
<!-- SECTION:FINAL_SUMMARY:END -->
