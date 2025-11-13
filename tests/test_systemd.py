from __future__ import annotations

import json
import unittest
from unittest import mock

from backend.system import SystemdDiscoveryError, list_systemd_services, service_states_for_units


class SystemdHelpersTestCase(unittest.TestCase):
    def test_list_systemd_services_uses_json_output(self) -> None:
        payload = json.dumps(
            [
                {
                    "name": "ssh.service",
                    "description": "OpenSSH server",
                    "load": "loaded",
                    "active": "active",
                    "sub": "running",
                },
                {
                    "name": "ais-catcher.service",
                    "description": "AIS Catcher",
                    "load": "loaded",
                    "active": "active",
                    "sub": "running",
                },
            ]
        )

        with mock.patch("backend.system.systemd._run_systemctl") as run:
            run.return_value = mock.Mock(stdout=payload)
            services = list_systemd_services()

        self.assertEqual(len(services), 2)
        ssh, ais = services
        self.assertTrue(ssh.is_standard_service)
        self.assertFalse(ais.is_standard_service)
        self.assertEqual(ssh.active, "active")
        self.assertEqual(ais.name, "ais-catcher.service")

    def test_list_systemd_services_falls_back_to_plain_output(self) -> None:
        plain_output = "ssh.service loaded active running OpenSSH server\ncustom.service loaded inactive dead Custom Service"

        with mock.patch("backend.system.systemd._run_systemctl") as run, mock.patch(
            "backend.system.systemd.json.loads",
            side_effect=json.JSONDecodeError("boom", "", 0),
        ):
            run.return_value = mock.Mock(stdout=plain_output)
            services = list_systemd_services()

        self.assertEqual(len(services), 2)
        self.assertEqual(services[0].name, "ssh.service")
        self.assertEqual(services[1].description, "Custom Service")

    def test_service_states_for_units_reports_errors(self) -> None:
        outputs = [
            mock.Mock(
                stdout="""● ais-catcher.service - AIS\n     Loaded: loaded (/etc/systemd/system/ais.service; enabled)\n     Active: active (running)""",
                returncode=0,
            ),
            SystemdDiscoveryError("not found"),
        ]

        with mock.patch("backend.system.systemd._run_systemctl", side_effect=outputs):
            statuses = service_states_for_units(["ais-catcher.service", "missing.service"])

        self.assertEqual(len(statuses), 2)
        self.assertEqual(statuses[0]["unit"], "ais-catcher.service")
        self.assertEqual(statuses[0]["status"], "ok")
        self.assertEqual(statuses[1]["status"], "error")
        self.assertIn("not found", statuses[1]["details"]["error"])


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()

