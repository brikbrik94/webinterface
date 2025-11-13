"""Tests for the FastAPI application endpoints."""
from __future__ import annotations

import unittest
from unittest import mock

from backend import app as backend_app
from backend.system import SystemdDiscoveryError, SystemdService
from backend.services.base import ServiceState


class AppEndpointTestCase(unittest.TestCase):
    """Verify that the API endpoints expose service status data."""

    def _build_service_config(self):
        from backend.config.loader import ServiceCommand, ServiceConfig

        return ServiceConfig(
            key="dummy",
            name="Dummy Service",
            adapter="command",
            commands=ServiceCommand(start="echo start", status="echo status"),
            metadata={"description": "Dummy"},
        )

    def test_service_status_overview_returns_all_states(self) -> None:
        service_config = self._build_service_config()
        fake_state = ServiceState(status="ok", details={"systemctl": {"active": "Active: running"}})

        with mock.patch.object(backend_app, "build_adapter") as build_adapter:
            adapter = mock.Mock()
            adapter.fetch_state.return_value = fake_state
            build_adapter.return_value = adapter

            payload = backend_app.list_service_states(configs=[service_config])

        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["key"], "dummy")
        self.assertEqual(payload[0]["status"], "ok")
        self.assertIn("systemctl", payload[0]["details"])
        adapter.fetch_state.assert_called_once()

    def test_service_detail_returns_single_state(self) -> None:
        service_config = self._build_service_config()
        fake_state = ServiceState(status="error", details={"output": "failed"})

        with mock.patch.object(backend_app, "build_adapter") as build_adapter:
            adapter = mock.Mock()
            adapter.fetch_state.return_value = fake_state
            build_adapter.return_value = adapter

            payload = backend_app.get_service_state("dummy", configs=[service_config])

        self.assertEqual(payload["key"], "dummy")
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["details"].get("output"), "failed")
        adapter.fetch_state.assert_called_once()

    def test_systemd_services_endpoint_serialises_results(self) -> None:
        services = [
            SystemdService(
                name="custom.service",
                description="Custom",
                load="loaded",
                active="active",
                sub="running",
                following=None,
                is_standard_service=False,
            )
        ]

        with mock.patch.object(backend_app, "list_systemd_services", return_value=services):
            payload = backend_app.get_systemd_services()

        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["unit"], "custom.service")
        self.assertFalse(payload[0]["isStandardService"])

    def test_systemd_services_endpoint_propagates_errors(self) -> None:
        with mock.patch.object(
            backend_app,
            "list_systemd_services",
            side_effect=SystemdDiscoveryError("kaputt"),
        ):
            with self.assertRaises(Exception) as ctx:
                backend_app.get_systemd_services()

        self.assertIn("kaputt", str(ctx.exception))

    def test_systemd_status_endpoint_validates_units(self) -> None:
        with self.assertRaises(Exception):
            backend_app.get_systemd_service_status({"units": "not-a-list"})

    def test_systemd_status_endpoint_returns_payload(self) -> None:
        payload = [{"unit": "demo.service", "status": "ok", "details": {}}]
        with mock.patch.object(backend_app, "service_states_for_units", return_value=payload):
            result = backend_app.get_systemd_service_status({"units": ["demo.service"]})

        self.assertEqual(result, payload)


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
