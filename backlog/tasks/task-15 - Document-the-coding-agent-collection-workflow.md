---
id: TASK-15
title: Document the coding-agent collection workflow
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-12 17:14'
updated_date: '2026-09-12 18:32'
labels:
  - documentation
dependencies:
  - TASK-10
  - TASK-12
references:
  - IMPLEMENTATION_PLAN.md
priority: medium
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Give developers and coding agents an exact contract for configuring applications and processing local errors safely.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 README instructions initialize an application with an explicit project slug
- [x] #2 README examples show claim, repeated delivery, acknowledgement, and empty-result behavior
- [x] #3 The schema_version 1 claim and acknowledgement fields are documented
- [x] #4 The documentation states the 100-occurrence limit, 30-minute expiry, and at-least-once duplicate behavior
- [x] #5 The default registry location, SUMP_STATE_DIR override, sensitive-data permissions, and indefinite retention are documented
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Replace the obsolete development placeholder with installation and explicit project-slug initialization instructions.
2. Document the coding-agent claim/retry/acknowledge loop, empty output, expiry, and at-least-once semantics.
3. Specify every schema-version-1 claim, occurrence, attachment, and acknowledgement field.
4. Document platform registry locations, SUMP_STATE_DIR, private permissions, sensitive data, indefinite retention, and fail-loud CLI behavior.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Replaced the obsolete development placeholder with complete local-alpha installation, explicit project-slug initialization, normal Sentry capture, and fail-loud behavior guidance. Added the coding-agent claim/retry/acknowledge/drain workflow with representative non-empty, acknowledgement, and empty schema-version-1 JSON documents.

Documented all claim, occurrence, attachment, and acknowledgement fields; oldest-first 100-item batches; immutable 30-minute active claims; expiry and stale acknowledgement; at-least-once duplicate handling; and when downstream work is safe to acknowledge. Added macOS/Linux platformdirs locations, absolute SUMP_STATE_DIR overrides, 0700/0600 privacy, sensitive data cautions, indefinite acknowledged-record retention, retained expiry metadata, and unbounded alpha storage growth.

Validation: taidy processed README.md without incidental changes; all three JSON examples parse; required contract markers are present; make check passed 37 tests; package build passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Documented the complete application and coding-agent workflow, schema v1 contract, retry and expiry semantics, and private retained registry behavior.
<!-- SECTION:FINAL_SUMMARY:END -->
