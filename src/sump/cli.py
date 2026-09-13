"""Command-line interface for Sump."""

import argparse
import json
import sys
from collections.abc import Sequence

from sump._claims import acknowledge_claim, claim_project
from sump._instructions import integration_instructions


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="sump",
        description="Record and collect local Sentry SDK errors.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    claim_parser = commands.add_parser(
        "claim",
        help="Claim pending errors for a project",
    )
    claim_parser.add_argument("project", help="Project slug whose errors should be claimed")
    acknowledge_parser = commands.add_parser(
        "acknowledge",
        help="Acknowledge and retain an active claim",
    )
    acknowledge_parser.add_argument("project", help="Project slug that owns the claim")
    acknowledge_parser.add_argument("claim_id", help="Claim ID returned by sump claim")
    commands.add_parser(
        "instructions",
        help="Print integration and collection instructions for a coding agent",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Sump command-line interface."""
    arguments = create_parser().parse_args(argv)
    if arguments.command == "instructions":
        sys.stdout.write(integration_instructions())
        return 0

    if arguments.command == "claim":
        result = claim_project(arguments.project)
    elif arguments.command == "acknowledge":
        result = acknowledge_claim(arguments.project, arguments.claim_id)
    else:
        raise AssertionError(f"unhandled command: {arguments.command}")

    json.dump(result, sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
