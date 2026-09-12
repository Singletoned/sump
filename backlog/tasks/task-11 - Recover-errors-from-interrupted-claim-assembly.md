---
id: TASK-11
title: Recover errors from interrupted claim assembly
status: To Do
assignee: []
created_date: '2026-09-12 17:14'
labels:
  - reliability
  - storage
dependencies:
  - TASK-9
references:
  - IMPLEMENTATION_PLAN.md
priority: high
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Ensure a collector crash during multi-file claim construction cannot strand or omit captured occurrences.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A claim becomes visible only after all selected envelopes and immutable claim metadata are complete
- [ ] #2 The next project operation returns every envelope from an incomplete staged claim to eligibility
- [ ] #3 Failure injection after moving any number of selected envelopes demonstrates that none are omitted
- [ ] #4 Multiple active claims or inconsistent claim metadata produce an explicit registry-corruption error
<!-- AC:END -->
