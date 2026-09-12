"""Tests for application-facing Sentry SDK initialization."""

import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sentry_sdk

import sump
from sump._transport import LocalTransport


class InitializationTests(unittest.TestCase):
    def test_initializes_real_sdk_with_project_transport_without_network(self) -> None:
        with (
            patch.object(
                socket,
                "create_connection",
                side_effect=AssertionError("network access attempted"),
            ),
            sump.init("example-app", default_integrations=False),
        ):
            transport = sentry_sdk.get_client().transport

        self.assertIsInstance(transport, LocalTransport)
        self.assertEqual(transport.project, "example-app")
        self.assertIsNone(transport.parsed_dsn)

    def test_forwards_unmanaged_sentry_options(self) -> None:
        sentinel = object()

        with patch("sump._sdk.sentry_sdk.init", return_value=sentinel) as sdk_init:
            result = sump.init(
                "example-app",
                default_integrations=False,
                environment="development",
            )

        self.assertIs(result, sentinel)
        options = sdk_init.call_args.kwargs
        self.assertEqual(options["default_integrations"], False)
        self.assertEqual(options["environment"], "development")
        self.assertIsInstance(options["transport"], LocalTransport)
        self.assertNotIn("dsn", options)

    def test_rejects_sentry_options_managed_by_sump(self) -> None:
        for option in ("dsn", "transport"):
            with self.subTest(option=option):
                with (
                    patch("sump._sdk.sentry_sdk.init") as sdk_init,
                    self.assertRaisesRegex(TypeError, option),
                ):
                    sump.init("example-app", **{option: None})

                sdk_init.assert_not_called()

    def test_rejects_invalid_projects_without_creating_registry(self) -> None:
        invalid_projects = (
            "",
            "Example-App",
            "example/app",
            "example app",
            "-example",
            "example-",
            "a" * 64,
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            registry = Path(temporary_directory) / "registry"
            with patch.dict("os.environ", {"SUMP_STATE_DIR": str(registry)}):
                for project in invalid_projects:
                    with self.subTest(project=project), self.assertRaises(ValueError):
                        sump.init(project)

            self.assertFalse(registry.exists())

    def test_rejects_non_string_project(self) -> None:
        with self.assertRaisesRegex(TypeError, "project must be a string"):
            sump.init(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
