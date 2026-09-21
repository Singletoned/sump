---
id: TASK-21
title: Prepare package metadata for PyPI
status: Done
assignee:
  - '@singletoned'
created_date: '2026-09-21 10:23'
updated_date: '2026-09-21 10:24'
labels:
  - packaging
  - documentation
dependencies: []
priority: high
ordinal: 21000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add the approved MIT license and public package metadata, and replace local-alpha installation guidance with PyPI installation instructions before the first release.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The source distribution and wheel declare MIT licensing and include the LICENSE file
- [x] #2 PyPI metadata identifies Ed Singleton as author and links homepage, repository, and issue tracker to github.com/singletoned/sump
- [x] #3 README installation guidance uses the published sump package while retaining local development commands
- [x] #4 Package checks, build, metadata inspection, and installed-wheel smoke verification pass
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Add the standard MIT license using the approved 2026 Ed Singleton copyright.
2. Add PEP 621 author, license, keywords, classifiers, and GitHub project URLs to pyproject.toml.
3. Replace local-alpha installation text with uv and pip installation commands while preserving contributor setup.
4. Re-lock, format, test, build, inspect both artifacts for metadata/license inclusion, and run installed-wheel smoke verification.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added the standard MIT license with the approved Copyright (c) 2026 Ed Singleton notice. Added PEP 639 MIT licensing and license-file metadata, author identity, package keywords, alpha/platform/Python classifiers, and Homepage, Repository, and Issues URLs under https://github.com/singletoned/sump.

Replaced the README’s local-checkout installation with uv and pip PyPI commands, retained contributor commands, added an explicit license section, and updated the generated coding-agent guide to install the published package with uv add sump.

Validation: uv lock succeeded with no lockfile change; formatting and lint passed; all 40 tests passed; the Sentry SDK 2.0.0/current compatibility matrix passed; the final wheel installed and passed the no-network capture/claim/redelivery/acknowledgement smoke workflow in clean Python 3.10.20. Parsed wheel metadata confirmed Name sump, Version 0.1.0, License-Expression MIT, Ed Singleton author metadata, and all three project URLs. Both wheel and source distribution contain LICENSE. git diff --check passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added the MIT license, complete public PyPI metadata, and published-package installation guidance.
<!-- SECTION:FINAL_SUMMARY:END -->
