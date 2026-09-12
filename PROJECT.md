# Sump

## Problem Statement

Coding agents working on local Python web applications need access to runtime errors so they can turn those errors into backlog tasks and fix them. Hosted Sentry is unnecessary for this development-only workflow, while application-specific log locations and formats make automated collection inconsistent.

Sump provides a Sentry-like local error workflow: applications continue to use the Sentry Python SDK and its integrations, while events are recorded in a machine-local central registry that coding agents can consume reliably without applications knowing where that registry lives.

## Target Audience

The primary users are coding agents that inspect errors from locally running Python web applications, create backlog tasks, and implement fixes. Developers configure the applications and may inspect or operate the collection workflow, but interactive human use is secondary to a stable machine-readable interface.

## Goals

- Require only a small, familiar initialization change in applications already using, or able to use, the Sentry Python SDK.
- Preserve the useful Sentry event information produced by existing SDK capture APIs and framework integrations.
- Store events reliably in a central location on the local machine without exposing that location to each application.
- Keep events from different applications isolated through a required, stable project identifier.
- Let coding agents claim each project's new errors, process them, and explicitly acknowledge successful collection.
- Prevent an interrupted collector from silently losing claimed errors.

## Key Features

- A Python package that configures the Sentry Python SDK to capture events locally rather than send them to a Sentry service.
- A required project identifier supplied during application initialization.
- Safe recording from locally running application processes into a shared machine-local registry.
- A command-line interface with a stable machine-readable contract for claiming uncollected errors belonging to one project.
- Explicit acknowledgement of claimed errors after downstream work succeeds.
- Recovery of abandoned claims so errors become available to collectors again.
- Retention of acknowledged records for later inspection, while excluding them from normal collection.
- Delivery of every captured occurrence; deduplication and issue grouping are left to the consuming coding agent.

## Constraints and Assumptions

- The package is for local development only, not production monitoring.
- Python applications and the collector run on the same machine and under a user account that can access the local registry.
- The Sentry Python SDK remains responsible for event capture and framework integration behavior.
- Local capture must not require a running server or external service.
- Reliability and clear collection state take priority over minimizing retained data or providing a rich interactive interface.
- The registry may contain sensitive application context and must remain local to the machine by default.

## Non-Goals

- Replacing Sentry as a hosted monitoring, alerting, search, or collaboration platform.
- Sending or forwarding events to hosted or self-hosted Sentry, including dual delivery.
- Supporting non-Python SDKs in the initial scope.
- Grouping, deduplicating, prioritizing, or automatically converting errors into backlog tasks.
- Hiding project identity through automatic working-directory inference.
- Automatically deleting or expiring acknowledged events in the initial scope.
- Building a graphical user interface.

## Success Criteria

- A local Python web application can adopt Sump through a small Sentry-like initialization change and a stable project name.
- Exceptions captured through normal Sentry SDK APIs or supported framework integrations appear in the local registry with enough event context for a coding agent to diagnose them.
- A collector requesting one project receives only that project's eligible, uncollected occurrences in a stable machine-readable form.
- Successfully acknowledged occurrences do not appear in subsequent normal collections.
- Unacknowledged claims can be recovered after collector interruption rather than being lost permanently.
- Concurrent application writes and collection do not expose partial records or corrupt collection state.
- Acknowledged events remain available for explicit later inspection.
- Normal use requires no network service and sends no event data off the local machine.

## Open Questions and Risks

- The supported operating systems and filesystems need to be defined, particularly where atomic file operations and concurrent access differ.
- Claim expiry and recovery semantics must balance prompt retries against duplicate processing by slow collectors.
- The stable machine-readable output and acknowledgement contract will need versioning so coding-agent integrations do not break unexpectedly.
- Sentry envelopes can contain large payloads or sensitive values; practical storage limits, redaction expectations, and eventual cleanup policy remain undecided.
- Compatibility expectations across Sentry Python SDK versions and event types need validation before the package can claim broad drop-in behavior.

## Preferred Approach

Build on the official Sentry Python SDK and replace only its delivery path with a local transport. Use durable, atomic local storage semantics and expose collection as a claim-and-acknowledge workflow. Keep applications unaware of the registry path while requiring an explicit project identity.

---

_Generated by Pi project-planner._
