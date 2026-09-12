---
id: TASK-8
title: Claim pending project errors as versioned JSON
status: To Do
assignee: []
created_date: '2026-09-12 17:14'
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
- [ ] #1 sump claim PROJECT returns one JSON document with schema_version 1 and claim metadata
- [ ] #2 A non-empty claim contains at most the 100 oldest pending occurrences for only the requested project
- [ ] #3 Each occurrence includes its identity, capture time, envelope headers, raw Sentry event, and Base64 attachment records
- [ ] #4 Attachment records retain filename and content type metadata
- [ ] #5 A project with no eligible occurrences returns claim_id null and an empty occurrences array
- [ ] #6 Malformed stored envelopes cause a non-zero command failure with a traceback on stderr
<!-- AC:END -->
