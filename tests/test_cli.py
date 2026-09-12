"""Tests for the Sump command-line entry point."""

import unittest
from contextlib import redirect_stdout
from io import StringIO

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


if __name__ == "__main__":
    unittest.main()
