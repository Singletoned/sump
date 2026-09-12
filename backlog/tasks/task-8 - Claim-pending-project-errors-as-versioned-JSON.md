---
id: TASK-8
title: Claim pending project errors as versioned JSON
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-12 17:14'
updated_date: '2026-09-12 18:13'
labels:
  - core
  - cli
dependencies:
  - TASK-7
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Allow a coding agent to claim a bounded, project-specific batch of captured errors through a stable machine-readable command.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 sump claim PROJECT returns one JSON document with schema_version 1 and claim metadata
- [x] #2 A non-empty claim contains at most the 100 oldest pending occurrences for only the requested project
- [x] #3 Each occurrence includes its identity, capture time, envelope headers, raw Sentry event, and Base64 attachment records
- [x] #4 Attachment records retain filename and content type metadata
- [x] #5 A project with no eligible occurrences returns claim_id null and an empty occurrences array
- [x] #6 Malformed stored envelopes cause a non-zero command failure with a traceback on stderr
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add persisted claim directories and deterministic occurrence filename parsing.
2. Parse up to 100 oldest pending envelopes into the versioned claim schema, including raw events and Base64 attachments.
3. Add the claim CLI subcommand while allowing errors to propagate to stderr with a non-zero exit.
4. Test project isolation, ordering/bounds, empty output, attachment metadata, and malformed-envelope failures.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Implemented sump claim PROJECT with schema version 1, persisted claim metadata, a fixed 100-occurrence limit, chronological selection, project isolation, raw event/envelope data, and Base64 attachment records. Empty projects return a null claim ID without creating state. Malformed envelopes propagate through the CLI as non-zero failures with full tracebacks.

Validation: make check passed 24 tests; Sentry compatibility passed on 2.0.0 and 2.69.1; package build and the sump entry-point empty-claim smoke test passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added the versioned JSON claim command with bounded oldest-first project claims, complete event and attachment data, empty results, and fail-loud corruption handling.
<!-- SECTION:FINAL_SUMMARY:END -->
