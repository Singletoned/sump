---
id: TASK-23
title: Add a safe mate release command
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-21 11:04'
updated_date: '2026-09-21 11:11'
labels:
  - packaging
  - cli
dependencies: []
references:
  - TASK-22
priority: high
ordinal: 23000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Provide a mate command that versions, verifies, commits, tags, and atomically pushes a new release without allowing dirty, stale, malformed, or partially pushed releases.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 mate release VERSION is listed with a required positional version argument and remains compatible with plain make
- [x] #2 Failures before a successful push restore the original local version, commit, and tag without modifying the remote
- [x] #3 Automated tests exercise successful local-remote publication and preflight or rollback failures, and mate --list plus project checks pass
- [x] #4 The command accepts an untagged current version plus final, alpha, beta, and release-candidate version updates supported by the release workflow, while rejecting invalid or already-tagged versions
- [x] #5 The command requires a clean synchronized main branch, updates pyproject.toml and uv.lock when needed, runs compatibility and smoke verification, creates a release commit and annotated tag, and atomically pushes main and the tag
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add a mate-compatible release VERSION target backed by a focused shell script.
2. Make the script validate version shape, clean synchronized main state, and local/remote tag availability before changing files.
3. Update through uv, run compatibility and smoke, create a release commit and annotated tag, then atomically push; roll local state back on any failure.
4. Add unittest coverage with temporary local and bare Git repositories plus fake uv/make commands so no real remote is touched.
5. Document the command and verify mate listing, tests, compatibility, build, and smoke.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added mate release VERSION and its plain-make equivalent. The release script accepts an untagged current version, version updates, and alpha, beta, and release-candidate forms matching the GitHub workflow. It requires clean main synchronized with origin/main; rejects malformed, local-tagged, and remote-tagged versions; updates through uv when needed; runs compatibility and smoke verification; creates an explicit release commit and annotated tag; and atomically pushes main plus the tag.

The command records the starting commit and rolls back version files, release commits, and local tags on verification, commit, tag, or push failure. It fetches the branch without tags so a rejected remote tag does not mutate local tag state. Remote refs remain unchanged when an atomic push fails. An untagged current version uses an empty release commit, allowing the initial v0.1.0 publication while preserving explicit release history and rollback behavior.

Added eight isolated unittest cases using temporary working and bare repositories with fake uv/make executables. They cover successful version updates, the current untagged version, all three prerelease forms, malformed versions, dirty and unsynchronized branches, existing remote tags, verification rollback, and rejected-push rollback without touching a real remote. Updated README release instructions to use mate release.

Validation: mate --list exposes release <version>; mate rejects a missing argument; plain make -n expands correctly; shell syntax and Ruff pass; all 48 tests pass; the Sentry compatibility matrix passes; a fresh build and installed-wheel smoke test pass; git diff --check passes.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added a tested transactional mate release VERSION command that supports the initial current version and future version bumps, then verifies, tags, and atomically pushes them.
<!-- SECTION:FINAL_SUMMARY:END -->
