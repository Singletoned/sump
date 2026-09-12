# Implementation Plan

## Project Context

Sump is a local-development Python package that reuses the official Sentry Python SDK and its framework integrations while replacing network delivery with a durable machine-local error registry. Its primary consumer is a coding agent that claims errors for one project, creates durable Backlog tasks, and then acknowledges the claim.

The delivery contract is intentionally at-least-once: duplicate delivery is acceptable, but silently losing an error is not. Sump stores every error/message occurrence without grouping it.

## Current State

- `PROJECT.md` records the approved project goals and boundaries.
- The repository contains project and Backlog configuration but no Python package, build configuration, tests, or user documentation yet.
- The working tree contains a new `Backburner` Backlog status and two deferred integration tasks:
  - `TASK-1`: Capture unhandled Django request errors through Sump
  - `TASK-2`: Capture unhandled Flask request errors through Sump
- The first release targets macOS and Linux with Python 3.10 or newer.
- The first milestone is an installable local alpha, not a PyPI release.

## Target Outcome

The first alpha provides:

```python
import sentry_sdk
import sump

sump.init(project="example-app")

# Existing SDK APIs and automatic integrations continue to be used.
sentry_sdk.capture_message("Example failure")
```

A coding agent can then run:

```console
sump claim example-app
sump acknowledge example-app <claim-id>
```

`claim` emits one versioned JSON document containing up to 100 error/message occurrences. A repeated claim request for a project with an active claim returns that same claim and its events. Acknowledgement retains the claimed records locally but excludes them from later normal claims.

The alpha is complete when this workflow works from an installed wheel, survives concurrent local writers and interrupted collectors, and is covered by automated tests that exercise the filesystem state transitions.

## Confirmed Decisions

- Support macOS and Linux on Python 3.10+.
- Build on `sentry-sdk` 2.x and the current `Transport.capture_envelope` API.
- Expose `sump.init(project=..., **sentry_options)` and continue using `sentry_sdk` for capture calls.
- Require an explicit, stable project identifier.
- Store one serialized Sentry envelope per occurrence using a maildir-style filesystem registry.
- Retain envelopes containing an `event` item, including message events and associated attachments.
- Ignore transactions, sessions, metrics, profiles, and check-ins in v1.
- Return a single versioned JSON document per claim.
- Limit each claim to 100 occurrences.
- Allow at most one active claim per project.
- Redeliver the active claim when `sump claim PROJECT` is repeated.
- Expire claims after 30 minutes and make their occurrences eligible for a new claim.
- Acknowledge after backlog tasks have been created, not after fixes are completed.
- Retain acknowledged records indefinitely in the initial release.
- Prefer duplicate delivery over event loss.
- Surface storage and registry failures plainly rather than reporting false success.
- Defer Django and Flask end-to-end fixtures until after the core alpha.

## Planning Assumptions

- Package and distribution name: `sump`; import package: `sump`; console command: `sump`.
- Use a `src/` package layout, Hatchling as the build backend, `uv` for dependency management, Ruff for formatting/linting, and built-in `unittest` for tests.
- Use `sentry-sdk>=2,<3` initially. Test against the oldest selected 2.x release and the current 2.x release before broad compatibility is claimed.
- Use `platformdirs` to resolve an OS-appropriate per-user state directory. Support `SUMP_STATE_DIR` as an advanced environment override for tests and isolated local environments; applications do not need to know the default path.
- Restrict project identifiers to a documented lowercase ASCII slug format so project names are safe and unambiguous as directory names. Reject invalid identifiers rather than silently rewriting them.
- Create registry directories with user-only permissions and files without group/world access because Sentry events can contain source, request, and user data.
- Do not impose a Sump-specific envelope or attachment size limit in the alpha. Disk exhaustion must produce an explicit failure; retention and quotas are deferred.
- `stdout` is reserved for command JSON. Diagnostics and tracebacks go to `stderr`, and failures return a non-zero exit status.

## Phase 1: Deliver the Direct-Capture Vertical Slice

### Outcome

A locally installed package can capture direct Sentry error/message events, claim them for one project, redeliver an active claim, and acknowledge it in a single-process workflow.

### Work

1. **Bootstrap the package and development workflow**
   - Add `pyproject.toml`, `uv.lock`, `src/sump/`, `tests/`, `README.md`, and a `Makefile`.
   - Configure Hatchling, the `sump` console script, Python 3.10+, `sentry-sdk`, `platformdirs`, and Ruff.
   - Add mate-compatible `.PHONY` Make targets with `##` descriptions for setup, formatting, tests, checks, and building.
   - Verify `mate --list`, each changed Make target, and wheel/sdist creation.

2. **Prove the Sentry SDK extension points before committing the public API**
   - Add focused compatibility tests for constructing a custom `Transport`, receiving `capture_envelope`, serializing/deserializing envelopes, extracting `event` items, and reading attachments.
   - Verify whether a synthetic local DSN is required for an active custom transport. If required, keep it private and prove that the selected transport performs no network I/O.
   - Verify that write exceptions from `capture_envelope` reach the caller with the tested SDK versions. If the SDK suppresses them, stop and revise the failure contract before continuing.
   - Record the supported SDK range based on evidence rather than assuming all 2.x versions behave identically.

3. **Add application initialization**
   - Implement `sump.init(project: str, **sentry_options)` as a typed, concise wrapper around `sentry_sdk.init`.
   - Validate the required project slug.
   - Reject caller-supplied `dsn` and `transport` options because v1 is local-only and must not silently send elsewhere or replace Sump's transport.
   - Forward all other Sentry options unchanged.

4. **Write event envelopes durably**
   - Store only envelopes for which `Envelope.get_event()` returns an event; this includes exceptions and captured messages.
   - Preserve the complete serialized envelope so attachments and future-readable metadata are not lost.
   - Write to a uniquely named temporary file on the registry filesystem, flush and `fsync` it, then atomically rename it into the project's pending directory and `fsync` the directory.
   - Use generated occurrence IDs and UTC capture timestamps in filenames; do not depend on mutable file timestamps for identity.
   - Implement `flush` and `kill` as explicit no-ops because capture is synchronous and leaves no in-memory queue.

5. **Implement the basic claim and acknowledgement commands**
   - Add `sump claim PROJECT` and `sump acknowledge PROJECT CLAIM_ID` using `argparse`.
   - Claim the oldest 100 pending records into one claim directory.
   - Return an existing active claim unchanged when the same project is claimed again.
   - Atomically move an acknowledged claim directory under the project's acknowledged area.
   - Make acknowledgement idempotent: retrying acknowledgement for an already acknowledged claim returns success.
   - Return an empty, versioned response with `claim_id: null` and `occurrences: []` when no records are eligible.

### Phase 1 Exit Evidence

- A unit/integration test captures `capture_exception` and `capture_message`, invokes the CLI, and validates the returned event payloads.
- Associated attachments survive envelope storage and appear in the claim response.
- Calling `claim` twice before acknowledgement returns the same claim ID and occurrences.
- After acknowledgement, the next claim excludes those occurrences while their files remain under acknowledged storage.
- Invalid project names, conflicting initialization options, malformed records, and write failures produce explicit errors.
- A built wheel installs into a clean temporary environment and completes a capture/claim/acknowledge smoke test without network access.

## Phase 2: Harden At-Least-Once Delivery for Concurrent and Interrupted Processes

### Outcome

The Phase 1 workflow remains correct with concurrent application writers, concurrent collectors, process interruption at each filesystem transition, and expired claims.

### Work

1. **Introduce a recoverable per-project state machine**
   - Use these states within one registry filesystem: `pending`, `staging`, `claimed`, and `acknowledged`.
   - Build a claim in a uniquely named staging directory, including immutable claim metadata, before atomically renaming the complete directory into `claimed`.
   - On the next project operation, recover incomplete staging directories by returning their envelopes to `pending` before creating or returning a claim.
   - Treat multiple active claim directories or inconsistent metadata as registry corruption and fail with a diagnostic instead of guessing.

2. **Serialize claim transitions without blocking event capture**
   - Use a per-project POSIX advisory lock (`fcntl.flock`) around claim, expiry, recovery, and acknowledgement transitions.
   - Keep transport writes lock-free: unique temporary files and atomic renames allow applications to continue recording while a collector holds the project lock.
   - Ensure two concurrent claim commands return the same active claim rather than partitioning or losing occurrences.

3. **Implement 30-minute claim expiry**
   - Store UTC `claimed_at` and `expires_at` values in immutable claim metadata.
   - Before returning an active claim, check its expiry. An unexpired claim is redelivered unchanged.
   - Recover an expired claim's envelopes to `pending`, then create a new claim with a new ID. This deliberately permits duplicate downstream processing.
   - Reject acknowledgement of an expired/recovered claim clearly. Retrying acknowledgement of a claim already in `acknowledged` remains successful.

4. **Stabilize the versioned machine contract**
   - Define schema version `1` with claim metadata and an `occurrences` array.
   - Each occurrence includes `occurrence_id`, `captured_at`, envelope headers, the raw Sentry event object, and attachment records. Encode binary attachment content as Base64 and retain filename/content-type metadata.
   - Keep ordering deterministic: oldest pending occurrence first and stable attachment ordering.
   - Document exit codes, empty results, idempotent acknowledgement, expiry, retry behavior, and the fact that delivery is at-least-once.

5. **Add failure-injection and subprocess coverage**
   - Interrupt capture before and after each flush/rename boundary and prove no partial pending record becomes visible.
   - Interrupt claim construction after moving any number of records and prove the next operation recovers all of them.
   - Interrupt acknowledgement and prove retry either completes it or reports it already complete.
   - Run concurrent subprocess writers and verify every successfully captured occurrence is readable and no envelope is corrupt.
   - Run concurrent claimers and verify they receive one claim ID with no occurrence omitted.
   - Exercise claim expiry with an injected clock rather than sleeping.
   - Run the full suite on macOS and Linux with the minimum and current supported Python versions.

### Phase 2 Exit Evidence

- All deterministic unit, integration, subprocess concurrency, and failure-injection tests pass.
- `make check`, package build, clean-environment installation, and end-to-end smoke verification pass.
- `mate --list` and every public Make target work with plain `make` as well.
- The README gives coding agents exact initialization, claim, acknowledgement, retry, and storage-sensitivity guidance.
- The repository contains no network-delivery path and the smoke suite fails if an event attempts network access.

## Architecture and Design Decisions

### Registry Layout

The exact platform-specific root is resolved centrally. Beneath it:

```text
<state-root>/
  tmp/
  projects/
    <project>/
      project.lock
      pending/
        <captured-at>-<occurrence-id>.envelope
      staging/
        <claim-id>/
      claimed/
        <claim-id>/
          claim.json
          <captured-at>-<occurrence-id>.envelope
      acknowledged/
        <claim-id>/
          claim.json
          <captured-at>-<occurrence-id>.envelope
```

All rename-based transitions stay within the same state root/filesystem. Capture uses `tmp` followed by atomic rename into `pending`. Claim assembly is hidden in `staging` until the complete directory is atomically renamed into `claimed`. Acknowledgement is an atomic directory rename from `claimed` to `acknowledged`.

### Public Python API

```python
def init(project: str, **sentry_options: object) -> object:
    """Initialize the Sentry SDK with Sump's local transport."""
```

The exact return annotation follows the installed `sentry_sdk.init` API. Sump does not wrap or re-export capture functions; callers use normal `sentry_sdk` APIs so existing integrations continue to behave normally.

### CLI Contract

Successful `sump claim example-app` output has this shape:

```json
{
  "schema_version": 1,
  "project": "example-app",
  "claim_id": "uuid",
  "claimed_at": "UTC timestamp",
  "expires_at": "UTC timestamp",
  "occurrences": [
    {
      "occurrence_id": "uuid",
      "captured_at": "UTC timestamp",
      "envelope_headers": {},
      "event": {},
      "attachments": [
        {
          "filename": "example.txt",
          "content_type": "text/plain",
          "content_base64": "..."
        }
      ]
    }
  ]
}
```

Successful acknowledgement returns a small versioned JSON confirmation containing the project, claim ID, and `acknowledged: true`. It returns the same success shape when repeated for an already acknowledged claim.

### Consistency and Failure Policy

- A record is collectible only after its complete envelope has been atomically installed in `pending`.
- An active claim becomes visible only after its complete staging directory becomes `claimed`.
- Acknowledgement becomes visible through one atomic directory rename.
- Every multi-step operation has a deterministic recovery rule exercised through failure injection.
- No broad exception handler converts corruption, permission failures, malformed envelopes, or disk errors into empty results.
- Duplicate delivery can occur after agent crashes or claim expiry; missing delivery after a successful capture is not acceptable.

### Sentry Compatibility Boundary

Sentry SDK 2.x deprecates `Transport.capture_event` in favor of `Transport.capture_envelope`, and current envelope APIs provide serialization, deserialization, and event extraction. The implementation should depend only on those tested APIs and isolate SDK-specific parsing in one module so compatibility changes do not leak into registry and CLI code.

References:

- Sentry Python 1.x to 2.x transport migration: https://docs.sentry.io/platforms/python/migration/1.x-to-2.x
- Sentry Python transport option: https://docs.sentry.io/platforms/python/configuration/options/
- Current transport source/API: https://getsentry.github.io/sentry-python/_modules/sentry_sdk/transport.html
- Current envelope source/API: https://getsentry.github.io/sentry-python/_modules/sentry_sdk/envelope.html

## Task Breakdown

Create the core Backlog tasks only after this plan is approved. Use outcome-based tasks with real dependencies rather than one task per internal layer.

1. **Install Sump and run its development checks**
   - Outcome: a clean checkout can be synced, checked, tested, and built using documented Make targets.

2. **Capture Sentry error envelopes in a project registry**
   - Outcome: `sump.init` records complete error/message envelopes locally and rejects unsafe or invalid configuration.
   - Depends on task 1.

3. **Claim project errors through a versioned JSON command**
   - Outcome: a coding agent receives up to 100 oldest occurrences and repeated calls redeliver one active claim.
   - Depends on task 2.

4. **Acknowledge claimed errors without deleting them**
   - Outcome: acknowledgement is idempotent, retained records leave normal collection, and unrecognized claims fail clearly.
   - Depends on task 3.

5. **Recover interrupted and expired claims**
   - Outcome: staged or 30-minute-expired claims become collectible again without omitted occurrences.
   - Depends on tasks 3 and 4.

6. **Preserve delivery under concurrent local processes**
   - Outcome: concurrent writers and claimers cannot corrupt, omit, or split successfully captured occurrences.
   - Depends on task 5.

7. **Verify the installable alpha from a built wheel**
   - Outcome: a clean environment completes the documented no-network capture/claim/acknowledge workflow.
   - Depends on tasks 2, 4, 5, and 6.

Deferred tasks already created:

- `TASK-1`: Capture unhandled Django request errors through Sump (`Backburner`)
- `TASK-2`: Capture unhandled Flask request errors through Sump (`Backburner`)

## Testing and Validation

- Use built-in `unittest`; do not add pytest solely for fixtures.
- Unit-test project validation, path resolution, envelope filtering/parsing, JSON encoding, expiry decisions, and error messages.
- Use temporary directories through `SUMP_STATE_DIR`; never touch a developer's real registry during tests.
- Use the real Sentry SDK for transport compatibility and end-to-end capture tests rather than mocking the behavior being integrated.
- Use mocks only at hard boundaries such as the clock, atomic filesystem operation failure points, and prohibited network access.
- Use subprocesses for locking, process interruption, and concurrent writer/collector tests; thread-only tests are insufficient for filesystem coordination.
- Verify file and directory permissions on both supported operating systems.
- Test the lower and upper supported `sentry-sdk` range in CI or a local version matrix.
- Run `taidy .`, then immediately inspect `git status` and the complete diff before committing formatter changes.
- Run `make check` frequently and before each logical commit.

## Risks and Mitigations

### Sentry custom transports may not propagate failures consistently

Mitigation: make exception propagation a Phase 1 compatibility gate. Do not claim fail-loudly behavior until tests prove it on the supported SDK range. If the SDK intentionally suppresses transport exceptions, revise the API or success criterion explicitly rather than hiding the mismatch.

### Filesystem transitions are not a multi-file transaction

Mitigation: expose claim directories only through a final atomic rename, keep incomplete work in `staging`, hold a per-project lock, and test recovery after every transition boundary.

### Advisory locks do not protect against non-cooperating manual edits

Mitigation: treat the registry as application-managed state, use strict validation, and fail on inconsistent layouts. Human readability is useful for diagnosis but does not make manual mutation supported.

### Large attachments can make a 100-occurrence response very large

Mitigation: preserve correctness in the alpha, document the risk, and keep the schema versioned. Add byte limits or attachment retrieval commands only after real usage demonstrates a need.

### Indefinite retention can exhaust disk space

Mitigation: document the storage location and retention behavior. Cleanup and quotas remain a later feature rather than being added without usage evidence.

### Newer Sentry envelope item types may change compatibility

Mitigation: store exact envelope bytes, parse only the event and attachment items needed by the v1 output contract, ignore unrelated item types deliberately, and test against a defined SDK range.

## Later Phases

- Execute deferred Django integration task `TASK-1`.
- Execute deferred Flask integration task `TASK-2`.
- Add explicit inspection of acknowledged records if coding-agent workflows require it.
- Add cleanup/retention controls after measuring local registry growth.
- Evaluate bounded response bytes or separate attachment retrieval if real payloads make claim documents unwieldy.
- Add compatibility for newer Sentry SDK major versions only after dedicated tests.
- Add PyPI publication metadata, release automation, and a support matrix when local alpha behavior is stable.
- Consider non-Python producers only if a concrete consumer requires them.

## Open Questions

These do not block Phases 1 or 2 unless evidence from implementation changes the assumptions:

- Which open-source license, if any, should be used before public distribution?
- What tested minimum `sentry-sdk` 2.x version provides all required envelope and transport behavior?
- Should a future cleanup policy be age-based, size-based, or explicitly invoked?
- Should attachments eventually be fetched separately to keep claim JSON smaller?

## Definition of Done

The first local alpha is done when:

- The package installs from a locally built wheel on supported Python versions.
- `sump.init(project=...)` captures Sentry exceptions and messages without network delivery.
- Complete event envelopes and attachments are durably stored under the correct project.
- Claims contain no more than 100 oldest eligible occurrences in the documented schema.
- Repeated project claims redeliver one active claim.
- Acknowledgement is idempotent, excludes records from future claims, and retains them locally.
- Interrupted or expired claims are recoverable with at-least-once semantics.
- Concurrent writers and claimers pass subprocess tests without corruption or omitted successful captures.
- Storage, malformed-data, invalid-input, expiry, and conflicting-option errors are explicit and actionable.
- Unit, integration, failure-injection, concurrency, formatting, linting, build, and clean-install smoke checks pass.
- `README.md` documents application setup and the coding-agent claim/acknowledge workflow.
- `mate --list` and all changed Make targets work.
- Django, Flask, cleanup, PyPI publication, and non-Python support remain explicitly deferred.
