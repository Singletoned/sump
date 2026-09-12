---
id: TASK-10
title: Acknowledge a project error claim without deleting it
status: To Do
assignee: []
created_date: '2026-09-12 17:14'
labels:
  - core
  - cli
dependencies:
  - TASK-9
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Let coding agents mark a represented batch complete while preserving its source records for later inspection.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 sump acknowledge PROJECT CLAIM_ID returns versioned JSON confirming acknowledgement
- [ ] #2 Acknowledged occurrences do not appear in later normal claims
- [ ] #3 Acknowledged claim metadata and envelopes remain in local registry storage
- [ ] #4 Repeating acknowledgement for the same project and claim ID returns success
- [ ] #5 An unknown project or claim ID produces a non-zero command failure
<!-- AC:END -->
