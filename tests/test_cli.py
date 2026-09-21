"""Tests for the Sump command-line entry point."""

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from sump._claims import claim_project
from sump.cli import create_parser, main


class CommandLineTests(unittest.TestCase):
    def test_parser_uses_sump_program_name(self) -> None:
        self.assertEqual(create_parser().prog, "sump")

    def test_help_exits_successfully(self) -> None:
        output = StringIO()

        with redirect_stdout(output), self.assertRaises(SystemExit) as exit_context:
            main(["--help"])

        self.assertEqual(exit_context.exception.code, 0)
        self.assertIn("claim", output.getvalue())
        self.assertIn("capture", output.getvalue())
        self.assertIn("--instructions", output.getvalue())

    def test_instructions_need_no_project_and_cover_the_agent_workflow(self) -> None:
        output = StringIO()

        with redirect_stdout(output), self.assertRaises(SystemExit) as exit_context:
            main(["--instructions"])

        instructions = output.getvalue()
        self.assertEqual(exit_context.exception.code, 0)
        self.assertLessEqual(len(instructions.splitlines()), 65)
        self.assertNotIn("derive one stable project slug", instructions.lower())
        self.assertIn('project="PROJECT_SLUG"', instructions)
        self.assertIn("sump claim PROJECT_SLUG", instructions)
        self.assertIn("sump acknowledge PROJECT_SLUG CLAIM_ID", instructions)
        self.assertIn("metadata", instructions.lower())
        self.assertIn("ambiguous", instructions.lower())
        self.assertIn('"claim_id": null', instructions)
        self.assertIn("100", instructions)
        self.assertIn("30 minutes", instructions)
        self.assertIn("at-least-once", instructions)
        self.assertIn("report", instructions.lower())
        self.assertRegex(instructions.lower(), r"needed\s+features")
        self.assertIn("silently work around", instructions.lower())

    def test_capture_records_a_message_with_structured_context(self) -> None:
        output = StringIO()

        with (
            tempfile.TemporaryDirectory() as temporary_directory,
            patch.dict("os.environ", {"SUMP_STATE_DIR": str(Path(temporary_directory))}),
            redirect_stdout(output),
        ):
            exit_code = main(
                [
                    "capture",
                    "example-app",
                    "--message",
                    "SQLite I/O error",
                    "--context-json",
                    '{"tool":"ctx_batch_execute"}',
                ]
            )
            claimed = claim_project("example-app")

        result = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertRegex(result["event_id"], r"^[0-9a-f]{32}$")
        self.assertEqual(claimed["occurrences"][0]["event"]["message"], "SQLite I/O error")
        self.assertEqual(claimed["occurrences"][0]["event"]["environment"], "development")
        self.assertEqual(
            claimed["occurrences"][0]["event"]["contexts"]["sump"]["tool"],
            "ctx_batch_execute",
        )

    def test_instructions_subcommand_is_rejected(self) -> None:
        errors = StringIO()

        with redirect_stderr(errors), self.assertRaises(SystemExit) as exit_context:
            main(["instructions"])

        self.assertEqual(exit_context.exception.code, 2)
        self.assertIn("invalid choice: 'instructions'", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
