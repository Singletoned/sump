"""Command-line interface for Sump."""

import argparse
from collections.abc import Sequence


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    return argparse.ArgumentParser(
        prog="sump",
        description="Record and collect local Sentry SDK errors.",
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Sump command-line interface."""
    parser = create_parser()
    parser.parse_args(argv)
    return 0
