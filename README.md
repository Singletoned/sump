# Sump

Sump records Python Sentry SDK errors in a private machine-local registry for coding agents to collect during local development. It replaces Sentry's network transport; it is not a production monitoring service and does not send events to hosted or self-hosted Sentry.

## Compatibility and installation

Sump supports macOS and Linux, Python 3.10 or newer, and `sentry-sdk>=2.0.0,<3`. Its transport contract is tested against Sentry SDK 2.0.0 and the current version locked by this project.

Sump is currently a local alpha rather than a PyPI release. Add a local checkout to an application's uv environment:

```console
uv add /absolute/path/to/sump
```

For Sump development itself:

```console
make setup
make check
make build
make smoke
```

`make smoke` first runs the checks and build, then installs the wheel into a clean temporary Python 3.10 environment. It captures a real exception with socket connections prohibited and verifies claim, identical redelivery, acknowledgement, retained records, and the final empty result through the installed command.

## Application setup

Initialize Sump once with an explicit, stable project slug, then use normal `sentry_sdk` capture APIs and integrations:

```python
import sentry_sdk
import sump

sump.init(
    project="example-app",
    # Other Sentry SDK options are forwarded unchanged.
    default_integrations=True,
)

sentry_sdk.capture_message("Example failure")

try:
    raise RuntimeError("Example exception")
except RuntimeError:
    sentry_sdk.capture_exception()
```

Project slugs contain 1–63 lowercase ASCII letters, numbers, dots, underscores, or hyphens and must begin and end with a letter or number. Sump rejects invalid slugs and caller-supplied `dsn` or `transport` options. Storage failures propagate from synchronous capture calls rather than pretending an event was recorded.

Sump stores message and error event envelopes, including attachments. Transactions, sessions, metrics, profiles, and check-ins are not collected.

## Give instructions to a coding agent

Generate a self-contained integration and collection prompt without needing to know a project slug first:

```console
sump instructions
```

The Markdown output tells an agent how to derive a stable project slug, install and initialize Sump, preserve existing Sentry integrations, claim and acknowledge errors safely, handle retries and duplicates, and report shortcomings or needed features to the user so they can be improved in Sump.

## Coding-agent collection workflow

### 1. Claim errors

```console
sump claim example-app
```

A successful command writes exactly one schema-version-1 JSON document to stdout. A non-empty response contains at most the 100 oldest pending occurrences for that project:

```json
{
  "schema_version": 1,
  "project": "example-app",
  "claim_id": "15cc282473f74ef49d205f333e2d6592",
  "claimed_at": "2026-02-03T04:05:06Z",
  "expires_at": "2026-02-03T04:35:06Z",
  "occurrences": [
    {
      "occurrence_id": "af085e126c9e4bd6a3de86313a6537ab",
      "captured_at": "2026-02-03T04:00:00.000000Z",
      "envelope_headers": {},
      "event": {
        "message": "Example failure"
      },
      "attachments": [
        {
          "filename": "diagnostic.txt",
          "content_type": "text/plain",
          "content_base64": "ZXhhbXBsZSBjb250ZW50cw=="
        }
      ]
    }
  ]
}
```

Create durable downstream work, such as Backlog tasks, before acknowledging the claim. The agent is responsible for grouping or deduplicating occurrences.

### 2. Retry safely

If processing is interrupted, run the same claim command again:

```console
sump claim example-app
```

For 30 minutes from `claimed_at`, Sump returns the same active `claim_id`, immutable timestamps, and ordered occurrences. Events captured after that claim was created stay pending for a later claim.

At `expires_at`, the claim is abandoned. Its occurrences become eligible immediately and the next claim returns them under a new claim ID. Delivery is therefore **at least once**: agents must tolerate duplicate occurrences, particularly after expiry or an uncertain interruption. Sump favors duplicates over silently losing captured errors.

### 3. Acknowledge durable downstream work

After the claim's occurrences are safely represented downstream, acknowledge it:

```console
sump acknowledge example-app 15cc282473f74ef49d205f333e2d6592
```

The response is:

```json
{
  "schema_version": 1,
  "project": "example-app",
  "claim_id": "15cc282473f74ef49d205f333e2d6592",
  "acknowledged": true
}
```

Acknowledgement is idempotent: repeating the command returns the same successful shape. Acknowledging a claim that expired and was recovered fails explicitly as stale; claim again and reconcile possible duplicates. Unknown projects and claim IDs also fail.

Acknowledgement means the occurrences are durably represented downstream. Fixes can happen afterward without holding the claim open.

### 4. Continue until empty

After acknowledgement, claim again to receive the next batch. When no occurrence is eligible, Sump returns:

```json
{
  "schema_version": 1,
  "project": "example-app",
  "claim_id": null,
  "claimed_at": null,
  "expires_at": null,
  "occurrences": []
}
```

## Schema version 1

Claim documents contain:

- `schema_version`: integer `1`.
- `project`: the requested project slug.
- `claim_id`: a lowercase UUID string, or `null` for an empty result.
- `claimed_at`: the UTC claim timestamp, or `null` for an empty result.
- `expires_at`: the UTC timestamp 30 minutes after `claimed_at`, or `null` for an empty result.
- `occurrences`: an oldest-first array containing no more than 100 records.

Each occurrence contains:

- `occurrence_id`: the stable lowercase UUID assigned at capture.
- `captured_at`: the UTC capture timestamp assigned at capture.
- `envelope_headers`: the raw Sentry envelope header object.
- `event`: the raw Sentry event object.
- `attachments`: attachment records in envelope order. Each has `filename`, `content_type`, and Base64-encoded bytes in `content_base64`.

Acknowledgement documents contain `schema_version`, `project`, `claim_id`, and the boolean `acknowledged` field.

Successful claim and acknowledgement commands reserve stdout for JSON; `sump instructions` writes Markdown. Invalid input, malformed registry data, permission failures, stale claims, and storage failures exit non-zero with a traceback on stderr.

## Registry storage and security

The default registry root is selected by `platformdirs`:

- macOS: `~/Library/Application Support/sump`
- Linux: `$XDG_STATE_HOME/sump`, normally `~/.local/state/sump`

For isolated development or tests, set an absolute override before starting the application and collector:

```console
export SUMP_STATE_DIR=/absolute/path/to/isolated-sump-state
```

Empty and relative overrides are rejected. Applications normally should not need this setting; the shared default location is intentionally hidden behind Sump.

Sentry events can contain source code, request values, user details, and attachment contents. Sump creates managed directories with mode `0700` and records and lock files with mode `0600`, denying group and world access. Keep the registry local and do not place it in a shared or synchronized directory.

Acknowledged envelopes and metadata are retained indefinitely for audit and debugging. Expired-claim metadata is also retained so stale acknowledgements remain identifiable. The alpha has no automatic cleanup, quota, or Sump-specific attachment-size limit, so registry growth and available disk space remain the user's responsibility.
