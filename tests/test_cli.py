"""Tests for the Sump command-line entry point."""

import unittest
from contextlib import redirect_stdout
from io import StringIO

import sump
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
        self.assertIn("instructions", output.getvalue())

    def test_instructions_are_project_specific_and_cover_the_agent_workflow(self) -> None:
        output = StringIO()

        with redirect_stdout(output):
            exit_code = main(["instructions", "example-app"])

        instructions = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn('project="example-app"', instructions)
        self.assertIn("sump claim example-app", instructions)
        self.assertIn("sump acknowledge example-app CLAIM_ID", instructions)
        self.assertIn('"claim_id": null', instructions)
        self.assertIn("100", instructions)
        self.assertIn("30-minute", instructions)
        self.assertIn("at-least-once", instructions)
        self.assertIn("report", instructions.lower())
        self.assertRegex(instructions.lower(), r"needed\s+features")
        self.assertIn("silently work around", instructions.lower())

    def test_instructions_use_application_project_validation(self) -> None:
        with self.assertRaises(ValueError) as init_context:
            sump.init(project="Invalid Project")

        with self.assertRaises(ValueError) as instructions_context:
            main(["instructions", "Invalid Project"])

        self.assertEqual(str(instructions_context.exception), str(init_context.exception))


if __name__ == "__main__":
    unittest.main()
