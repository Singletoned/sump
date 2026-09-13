"""Verify the complete Sump workflow from the built wheel."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CAPTURE_SCRIPT = r"""
import json
import socket

import sentry_sdk
import sump

network_attempts = []


def reject_connection(*args, **kwargs):
    network_attempts.append({"args": repr(args), "kwargs": repr(kwargs)})
    raise AssertionError("network connection attempted during Sump capture")


socket.create_connection = reject_connection
socket.socket.connect = reject_connection
socket.socket.connect_ex = reject_connection

with sump.init("wheel-smoke", default_integrations=False):
    try:
        raise RuntimeError("installed wheel smoke exception")
    except RuntimeError:
        event_id = sentry_sdk.capture_exception()

if network_attempts:
    raise AssertionError(f"event delivery attempted network access: {network_attempts}")
print(json.dumps({"event_id": event_id}))
"""


def run_for_output(command, working_directory, environment):
    completed = subprocess.run(
        command,
        cwd=working_directory,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        completed.check_returncode()
    return completed.stdout


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def validate_claim(claim):
    require(claim["schema_version"] == 1, "claim schema version changed")
    require(claim["project"] == "wheel-smoke", "claim project changed")
    require(isinstance(claim["claim_id"], str), "claim ID is missing")
    require(isinstance(claim["claimed_at"], str), "claim timestamp is missing")
    require(isinstance(claim["expires_at"], str), "claim expiry is missing")
    require(len(claim["occurrences"]) == 1, "claim did not contain exactly one occurrence")
    occurrence = claim["occurrences"][0]
    require(isinstance(occurrence["occurrence_id"], str), "occurrence ID is missing")
    require(isinstance(occurrence["captured_at"], str), "capture timestamp is missing")
    require(isinstance(occurrence["envelope_headers"], dict), "envelope headers are missing")
    exception = occurrence["event"]["exception"]["values"][0]
    require(exception["type"] == "RuntimeError", "captured exception type changed")
    require(
        exception["value"] == "installed wheel smoke exception",
        "captured exception value changed",
    )
    require(occurrence["attachments"] == [], "unexpected smoke-test attachments")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: smoke_installed.py WHEEL")

    wheel = Path(sys.argv[1]).resolve(strict=True)
    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("uv is required for the installed-wheel smoke test")

    with tempfile.TemporaryDirectory(prefix="sump-wheel-smoke-") as directory:
        root = Path(directory)
        virtual_environment = root / ".venv"
        python = virtual_environment / "bin" / "python"
        sump_command = virtual_environment / "bin" / "sump"
        state_root = root / "state"

        subprocess.run(
            [uv, "venv", "--python", "3.10", virtual_environment],
            cwd=root,
            check=True,
        )
        subprocess.run(
            [uv, "pip", "install", "--python", python, wheel],
            cwd=root,
            check=True,
        )

        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment["SUMP_STATE_DIR"] = str(state_root)

        instructions = run_for_output([sump_command, "instructions"], root, environment)
        require('project="PROJECT_SLUG"' in instructions, "installed instructions lack setup")
        require(
            "sump claim PROJECT_SLUG" in instructions,
            "installed instructions lack the claim command",
        )
        require(
            "sump acknowledge PROJECT_SLUG CLAIM_ID" in instructions,
            "installed instructions lack the acknowledgement command",
        )
        require(
            "room for improvement" in instructions and "silently work around" in instructions,
            "installed instructions lack the improvement-reporting directive",
        )

        capture_result = json.loads(
            run_for_output([python, "-c", CAPTURE_SCRIPT], root, environment)
        )
        require(isinstance(capture_result["event_id"], str), "Sentry returned no event ID")

        first_claim_text = run_for_output([sump_command, "claim", "wheel-smoke"], root, environment)
        first_claim = json.loads(first_claim_text)
        validate_claim(first_claim)

        redelivered_text = run_for_output([sump_command, "claim", "wheel-smoke"], root, environment)
        require(redelivered_text == first_claim_text, "active claim redelivery changed")

        acknowledgement = json.loads(
            run_for_output(
                [
                    sump_command,
                    "acknowledge",
                    "wheel-smoke",
                    first_claim["claim_id"],
                ],
                root,
                environment,
            )
        )
        require(
            acknowledgement
            == {
                "schema_version": 1,
                "project": "wheel-smoke",
                "claim_id": first_claim["claim_id"],
                "acknowledged": True,
            },
            "acknowledgement response changed",
        )

        acknowledged_path = (
            state_root / "projects" / "wheel-smoke" / "acknowledged" / first_claim["claim_id"]
        )
        require(
            (acknowledged_path / "claim.json").is_file(),
            "acknowledged claim metadata was not retained",
        )
        require(
            len(list(acknowledged_path.glob("*.envelope"))) == 1,
            "acknowledged envelope was not retained",
        )

        empty_claim = json.loads(
            run_for_output([sump_command, "claim", "wheel-smoke"], root, environment)
        )
        require(
            empty_claim
            == {
                "schema_version": 1,
                "project": "wheel-smoke",
                "claim_id": None,
                "claimed_at": None,
                "expires_at": None,
                "occurrences": [],
            },
            "post-acknowledgement claim was not empty",
        )

    print("Installed wheel capture/claim/redelivery/acknowledgement smoke passed.")


if __name__ == "__main__":
    main()
