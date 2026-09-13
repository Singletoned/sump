"""Project-specific instructions for coding agents."""

from textwrap import dedent

from sump._sdk import validate_project


def integration_instructions(project: str) -> str:
    """Return a self-contained Sump integration and collection prompt."""
    validate_project(project)
    return dedent(
        f'''\
        # Integrate and operate Sump for `{project}`

        Follow these instructions as a coding agent. Sump is for local development only. It
        records Sentry error and message events in a private local registry and does not send
        them to a hosted or self-hosted Sentry service.

        ## Integrate the application

        1. Ensure the target application's environment contains this local Sump checkout. For
           a uv project, use `uv add /absolute/path/to/sump`. Do not invent the checkout path;
           ask the user if it is unknown.
        2. Find the application's Sentry SDK initialization. Import `sump` and initialize it
           once, early in application startup, with this exact stable project slug:

           ```python
           import sentry_sdk
           import sump

           sump.init(
               project="{project}",
               # Preserve the application's other sentry_sdk.init options here.
           )
           ```

        3. Preserve appropriate existing `sentry_sdk.init` options and Sentry integrations, but
           remove `dsn` and `transport`: Sump owns both. Continue using normal Sentry APIs such
           as `sentry_sdk.capture_exception()` and `sentry_sdk.capture_message()`. Existing
           framework integrations should continue to capture unhandled errors.
        4. Do not configure remote Sentry delivery. Do not add Sump to production solely for
           this workflow. Run the project's checks and, when practical, verify locally that a
           captured test exception appears in `sump claim {project}`.
        5. Normally leave `SUMP_STATE_DIR` unset. If the application already uses an override,
           the collection command must use the same absolute value or it will read a different
           registry.

        ## Collect errors

        1. Run:

           ```console
           sump claim {project}
           ```

        2. Parse the schema-version-1 JSON on stdout. A non-empty claim contains up to 100
           oldest-first occurrences. Inspect each occurrence's raw `event`, `envelope_headers`,
           and Base64-encoded `attachments`. Diagnose the root cause and create durable backlog
           work for every relevant occurrence. You decide how to group or deduplicate errors.
        3. A claim remains active for 30 minutes. Repeating `sump claim {project}` before expiry
           redelivers the identical claim and leaves newer errors pending. This makes interrupted
           processing safe to resume.
        4. Only after all work from the claim is safely recorded downstream, acknowledge it with
           the returned ID:

           ```console
           sump acknowledge {project} CLAIM_ID
           ```

           Acknowledgement is idempotent. Do not wait for fixes to be completed before
           acknowledging; acknowledge once the backlog work is durable.
        5. Run `sump claim {project}` again and repeat until the response includes:

           ```json
           "claim_id": null,
           "occurrences": []
           ```

        Sump uses at-least-once delivery. At the 30-minute expiry boundary, unacknowledged
        occurrences become eligible under a new claim ID and may be duplicates. An old
        acknowledgement then fails as stale. Reconcile the replacement claim with work already
        created rather than discarding it. Command or registry errors must be treated as real
        failures; do not acknowledge data you could not process.

        ## Report opportunities to improve Sump

        While integrating and collecting, actively look for room for improvement and needed
        features. Report concrete findings to the user so they can be fixed in Sump. This
        includes confusing instructions, awkward commands, missing framework support or event
        context, incompatible Sentry behavior, unsafe retry semantics, malformed or inconvenient
        output, and any manual step that should be automated. Include evidence, expected behavior,
        and the affected command or integration point. Do not silently work around a Sump
        shortcoming and leave it unreported.
        '''
    )
