"""Tests for the Sump command-line entry point."""

import unittest

from sump.cli import create_parser, main


class CommandLineTests(unittest.TestCase):
    def test_parser_uses_sump_program_name(self) -> None:
        self.assertEqual(create_parser().prog, "sump")

    def test_main_accepts_no_arguments(self) -> None:
        self.assertEqual(main([]), 0)


if __name__ == "__main__":
    unittest.main()
