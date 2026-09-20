"""Integration and collection instructions for coding agents."""

from textwrap import dedent


def integration_instructions() -> str:
    """Return concise Sump integration and collection instructions."""
    return dedent(
        """\
        # Use Sump in this project

        Sump captures Sentry errors locally for coding agents. It is for development only and
        never sends events to Sentry.

        ## Integrate

        1. Choose `PROJECT_SLUG`. Use `[project].name` from `pyproject.toml`, other project
           metadata, or the repository name. If the project's identity is ambiguous, ask the
           user. Lowercase it, replace unsupported characters with hyphens, and keep it to 1-63
           letters, numbers, dots, underscores, or hyphens, starting and ending with a letter or
           number. Replace `PROJECT_SLUG` in every example below.
        2. Install this local checkout in the application. With uv, run
           `uv add /absolute/path/to/sump`. Ask the user for the path if needed.
        3. Replace the application's `sentry_sdk.init(...)` call with:

           ```python
           import sentry_sdk
           import sump

           sump.init(
               project="PROJECT_SLUG",
               # Keep the application's other sentry_sdk.init options.
           )
           ```

           Keep existing options and integrations except `dsn` and `transport`, which Sump owns.
           Keep using `capture_exception()`, `capture_message()`, and framework integrations.
        4. Initialize Sump once, early in startup. For a non-Python process that cannot use the
           SDK, invoke `sump capture PROJECT_SLUG --message "..."` with `--context-json` set to a
           JSON object. Treat a non-zero exit as a capture failure.
        5. Run the project's checks and verify a local captured error when practical. Do not add
           this setup to production. Leave `SUMP_STATE_DIR` unset unless already configured; the
           application and CLI must use the same value.

        ## Process errors

        1. Run `sump claim PROJECT_SLUG`.
        2. Read the schema-version-1 JSON from stdout. A claim contains up to 100 oldest-first
           occurrences. Inspect each raw `event`, `envelope_headers`, and Base64 `attachments`.
        3. Diagnose the errors and save durable backlog work. Group or deduplicate related
           occurrences yourself.
        4. Once that work is saved, run `sump acknowledge PROJECT_SLUG CLAIM_ID` with the returned
           claim ID. Acknowledgement is idempotent; the fixes do not need to be finished first.
        5. Repeat until `sump claim PROJECT_SLUG` returns:

           ```json
           "claim_id": null,
           "occurrences": []
           ```

        Claims last 30 minutes. Claiming again before expiry returns the identical claim so work
        can resume. Delivery is at-least-once: after expiry, occurrences can return under a new
        claim ID and the old acknowledgement is stale. Reconcile duplicates with saved work.
        Treat command and registry errors as failures. Never acknowledge errors you did not process.

        ## Report Sump issues

        Look for room for improvement and needed features. Report each issue to the user with
        evidence, expected behavior, and the affected command or integration point. Include poor
        instructions, missing context or framework support, awkward output, unsafe behavior, and
        manual work that should be automated. Do not silently work around a Sump problem.
        """
    )
