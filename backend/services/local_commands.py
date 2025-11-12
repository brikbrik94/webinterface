"""Generic adapter executing shell commands for lifecycle operations."""
from __future__ import annotations

from collections.abc import Mapping
import subprocess
from typing import Any, Optional

from .base import ServiceAdapter, ServiceState, ShellCommandMixin


class CommandService(ShellCommandMixin, ServiceAdapter):
    """Adapter that exposes lifecycle commands and a status probe.

    The adapter executes shell commands defined in the YAML configuration. It is
    intentionally minimal and intended as a baseline for future specialised
    adapters (e.g. systemd via DBus, Docker, Kubernetes).
    """

    def __init__(
        self,
        key: str,
        name: str,
        metadata: Optional[Mapping[str, Any]] = None,
        *,
        commands: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(key=key, name=name, metadata=metadata, commands=commands)

    def fetch_state(self) -> ServiceState:
        status_cmd = self.get_command("status")
        if not status_cmd:
            return ServiceState(status="unknown", details={"message": "No status command configured."})

        try:
            output = subprocess.check_output(status_cmd, shell=True, text=True, stderr=subprocess.STDOUT)
            details: dict[str, Any] = {"output": output.strip()}
            summary = self._extract_systemctl_summary(output)
            if summary:
                details["systemctl"] = summary
            return ServiceState(status="ok", details=details)
        except subprocess.CalledProcessError as exc:
            output = exc.output or ""
            details = {"returncode": exc.returncode, "output": output.strip()}
            summary = self._extract_systemctl_summary(output)
            if summary:
                details["systemctl"] = summary
            return ServiceState(status="error", details=details)

    def _extract_systemctl_summary(self, output: str) -> dict[str, str]:
        """Return selected lines from a ``systemctl`` output for quick inspection."""

        summary: dict[str, str] = {}
        for raw_line in output.splitlines():
            line = raw_line.strip()
            if line.startswith("Loaded:"):
                summary.setdefault("loaded", line)
            elif line.startswith("Active:"):
                summary.setdefault("active", line)
            elif line.startswith("Main PID:"):
                summary.setdefault("main_pid", line)
            elif line.startswith("Tasks:"):
                summary.setdefault("tasks", line)
            elif line.startswith("Memory:"):
                summary.setdefault("memory", line)
            elif line.startswith("CPU:"):
                summary.setdefault("cpu", line)
        return summary

    def _run_command(self, key: str) -> None:
        command = self.get_command(key)
        if not command:
            raise RuntimeError(f"No '{key}' command configured for service '{self.key}'")
        subprocess.check_call(command, shell=True)

    def start(self) -> None:  # pragma: no cover - requires integration testing
        self._run_command("start")

    def stop(self) -> None:  # pragma: no cover - requires integration testing
        self._run_command("stop")

    def restart(self) -> None:  # pragma: no cover - requires integration testing
        command = self.get_command("restart")
        if command:
            subprocess.check_call(command, shell=True)
        else:
            # Fallback to stop/start if explicit restart is unavailable
            self.stop()
            self.start()
