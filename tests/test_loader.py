"""Tests for the configuration loader utilities."""
from __future__ import annotations

import os
from pathlib import Path

import unittest


class LoadConfigTestCase(unittest.TestCase):
    """Integration tests for :func:`backend.config.loader.load_config`."""

    def test_default_path_resolved_from_any_working_directory(self) -> None:
        """The loader should find the default YAML even from another CWD."""

        from backend.config import loader

        original_cwd = Path.cwd()
        try:
            os.chdir("/")
            config = loader.load_config()
        finally:
            os.chdir(original_cwd)

        self.assertTrue(config.services, "Expected at least one service to be loaded")
        # Ensure the ORS service from the sample configuration is present.
        service_keys = {service.key for service in config.services}
        self.assertIn("ors", service_keys)


if __name__ == "__main__":  # pragma: no cover - manual test execution
    unittest.main()

