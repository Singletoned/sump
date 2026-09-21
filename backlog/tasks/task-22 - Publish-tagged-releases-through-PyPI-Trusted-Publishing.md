---
id: TASK-22
title: Publish tagged releases through PyPI Trusted Publishing
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-21 10:51'
updated_date: '2026-09-21 10:54'
labels:
  - packaging
  - ci
dependencies: []
references:
  - TASK-21
priority: high
ordinal: 22000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add a GitHub Actions release workflow that verifies tagged distributions and publishes them to PyPI through the configured pypi environment without stored credentials.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Final, alpha, beta, and release-candidate semantic version tags trigger the workflow
- [x] #2 A least-privilege build job runs project checks, the Sentry compatibility matrix, build, and installed-distribution verification before exposing publishing permissions
- [x] #3 A separate publish job downloads the exact verified artifacts, generates attestations, and runs uv publish with only id-token write permission
- [x] #4 The publish job uses the pypi GitHub environment and all third-party actions are pinned to immutable commit SHAs
- [x] #5 The workflow passes local syntax and structural validation
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Follow uv’s current two-job Trusted Publishing pattern with immutable action SHAs and semantic-version tag filters.
2. In the unprivileged build job, install Python 3.10, run compatibility and checks, build once, smoke-test both wheel and source distribution, and upload dist as one artifact.
3. In the pypi publish job, download only that artifact, generate PEP 740 attestations, and publish through OIDC.
4. Validate YAML and workflow structure locally, rerun project checks and both distribution smoke tests, then document the remaining GitHub/PyPI configuration.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added a tag-triggered Trusted Publishing workflow based on uv’s current two-job security pattern. Final, alpha, beta, and release-candidate tags are accepted, and the build job rejects tags that do not exactly match the pyproject version.

The unprivileged build job runs the Sentry SDK compatibility matrix, all project checks, builds both distributions, smoke-tests the wheel and source distribution, and uploads the verified dist directory. The separate pypi-environment publish job downloads only that artifact, generates PEP 740 attestations, and publishes with its sole id-token: write permission. Global permissions default to none; checkout credentials and action caches are disabled; all six third-party action uses are pinned to immutable 40-character commit SHAs.

Documented the release procedure and required GitHub/PyPI configuration in README.md.

Validation: Ruby parsed the workflow YAML; structural checks confirmed all tag patterns, exact SHA pins, permission isolation, and tag/version behavior. The Sentry compatibility matrix and all 40 tests passed. Fresh wheel and source distributions both passed the installed no-network workflow. git diff --check passed. The workflow cannot be executed end-to-end until a release tag is pushed and the human-configured PyPI Trusted Publisher exists.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added a least-privilege, attested GitHub Actions workflow for verified tag-driven PyPI releases.
<!-- SECTION:FINAL_SUMMARY:END -->
