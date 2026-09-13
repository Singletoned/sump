"""Integration and collection instructions for coding agents."""

from textwrap import dedent


def integration_instructions() -> str:
    """Return a self-contained Sump integration and collection prompt."""
    return dedent(
        """\
        # Integrate and operate Sump

        Follow these instructions as a coding agent. Sump is for local development only. It
        records Sentry error and message events in a private local registry and does not send
        them to a hosted or self-hosted Sentry service.

        ## Choose the project slug

        First derive one stable project slug. Inspect authoritative project metadata such as the
        `[project].name` in `pyproject.toml`, other package metadata, or the repository name. Use
        1-63 lowercase ASCII letters, numbers, dots, underscores, or hyphens, beginning and ending
        with a letter or number. Normalize spaces or other punctuation to hyphens. Use the same
        slug for initialization and every collection command. If the repository contains multiple
        applications or the intended identity is ambiguous, ask the user which stable slug to use.

        Every example below uses the literal placeholder `PROJECT_SLUG`. Replace it with the slug
        you chose; do not copy `PROJECT_SLUG` into the application or commands unchanged.

        ## Integrate the application

        1. Ensure the target application's environment contains this local Sump checkout. For
           a uv project, use `uv add /absolute/path/to/sump`. Do not invent the checkout path;
           ask the user if it is unknown.
        2. Find the application's Sentry SDK initialization. Import `sump` and initialize it
           once, early in application startup:

           ```python
           import sentry_sdk
           import sump

           sump.init(
               project="PROJECT_SLUG",
               # Preserve the application's other sentry_sdk.init options here.
           )
           ```

        3. Preserve appropriate existing `sentry_sdk.init` options and Sentry integrations, but
           remove `dsn` and `transport`: Sump owns both. Continue using normal Sentry APIs such
           as `sentry_sdk.capture_exception()` and `sentry_sdk.capture_message()`. Existing
           framework integrations should continue to capture unhandled errors.
        4. Do not configure remote Sentry delivery. Do not add Sump to production solely for
           this workflow. Run the project's checks and, when practical, verify locally that a
           captured test exception appears in `sump claim PROJECT_SLUG`.
        5. Normally leave `SUMP_STATE_DIR` unset. If the application already uses an override,
           the collection command must use the same absolute value or it will read a different
           registry.

        ## Collect errors

        1. Run:

           ```console
           sump claim PROJECT_SLUG
           ```

        2. Parse the schema-version-1 JSON on stdout. A non-empty claim contains up to 100
           oldest-first occurrences. Inspect each occurrence's raw `event`, `envelope_headers`,
           and Base64-encoded `attachments`. Diagnose the root cause and create durable backlog
           work for every relevant occurrence. You decide how to group or deduplicate errors.
        3. A claim remains active for 30 minutes. Repeating `sump claim PROJECT_SLUG` before expiry
           redelivers the identical claim and leaves newer errors pending. This makes interrupted
           processing safe to resume.
        4. Only after all work from the claim is safely recorded downstream, acknowledge it with
           the returned ID:

           ```console
           sump acknowledge PROJECT_SLUG CLAIM_ID
           ```

           Acknowledgement is idempotent. Do not wait for fixes to be completed before
           acknowledging; acknowledge once the backlog work is durable.
        5. Run `sump claim PROJECT_SLUG` again and repeat until the response includes:

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
        """
    )
