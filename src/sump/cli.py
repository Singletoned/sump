"""Command-line interface for Sump."""

import argparse
import json
import sys
from collections.abc import Sequence

from sump._claims import claim_project


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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Sump command-line interface."""
    arguments = create_parser().parse_args(argv)
    if arguments.command == "claim":
        result = claim_project(arguments.project)
    else:
        raise AssertionError(f"unhandled command: {arguments.command}")

    json.dump(result, sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
