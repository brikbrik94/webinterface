"""Helpers for querying systemd-managed services."""

from __future__ import annotations

from dataclasses import dataclass
import json
import shutil
import subprocess
from typing import Iterable, Sequence


class SystemdDiscoveryError(RuntimeError):
    """Raised when systemd information cannot be retrieved."""


@dataclass(slots=True)
class SystemdService:
    """Representation of a systemd unit entry."""

    name: str
    description: str
    load: str
    active: str
    sub: str
    following: str | None = None
    is_standard_service: bool = False


SYSTEMCTL = shutil.which("systemctl")

STANDARD_PREFIXES: Sequence[str] = (
    "systemd-",
    "sys-",
    "dbus",
    "user@",
    "session-",
    "serial-getty@",
    "getty@",
    "-.",
    "basic.",
    "multi-user.",
    "graphical.",
    "rescue.",
    "emergency.",
)

STANDARD_CONTAINS: Sequence[str] = (
    "network",
    "ssh",
    "chrony",
    "cron",
    "avahi",
    "systemd",
    "cups",
    "docker",
    "containerd",
    "polkit",
    "rsyslog",
    "wpa_supplicant",
)


def _run_systemctl(
    arguments: Iterable[str],
    *,
    allow_failure: bool = False,
) -> subprocess.CompletedProcess[str]:
    if SYSTEMCTL is None:
        raise SystemdDiscoveryError("systemctl executable is not available on this host")

    try:
        return subprocess.run(  # noqa: S603,S607 - trusted local execution
            [SYSTEMCTL, *arguments],
            check=not allow_failure,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:  # pragma: no cover - defensive fallback
        raise SystemdDiscoveryError("systemctl executable could not be found") from exc
    except subprocess.CalledProcessError as exc:
        raise SystemdDiscoveryError(exc.stderr.strip() or exc.stdout.strip() or str(exc)) from exc


def _heuristic_is_standard(name: str, description: str) -> bool:
    normalized_name = name.lower()
    normalized_description = description.lower()
    if any(normalized_name.startswith(prefix) for prefix in STANDARD_PREFIXES):
        return True
    if any(token in normalized_name for token in STANDARD_CONTAINS):
        return True
    if any(token in normalized_description for token in STANDARD_CONTAINS):
        return True
    return False


def _parse_json_units(payload: str) -> list[SystemdService]:
    entries = json.loads(payload)
    services: list[SystemdService] = []
    for entry in entries:
        name = entry.get("name")
        if not name:
            continue
        description = entry.get("description") or ""
        load = entry.get("load", "unknown")
        active = entry.get("active", entry.get("active_state", "unknown"))
        sub_state = entry.get("sub", entry.get("sub_state", "unknown"))
        following = entry.get("following") or None
        services.append(
            SystemdService(
                name=name,
                description=description,
                load=load,
                active=active,
                sub=sub_state,
                following=following,
                is_standard_service=_heuristic_is_standard(name, description),
            )
        )
    return services


def _parse_plain_units(payload: str) -> list[SystemdService]:
    services: list[SystemdService] = []
    for line in payload.splitlines():
        if not line.strip():
            continue
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        name, load, active, sub_state, description = parts
        services.append(
            SystemdService(
                name=name,
                description=description,
                load=load,
                active=active,
                sub=sub_state,
                following=None,
                is_standard_service=_heuristic_is_standard(name, description),
            )
        )
    return services


def list_systemd_services() -> list[SystemdService]:
    """Return a list of all systemd service units available on the host."""

    result = _run_systemctl(
        [
            "list-units",
            "--type=service",
            "--all",
            "--no-legend",
            "--no-pager",
            "--plain",
            "--output=json",
        ]
    )
    try:
        return _parse_json_units(result.stdout)
    except (json.JSONDecodeError, TypeError):
        return _parse_plain_units(result.stdout)


def service_states_for_units(units: Sequence[str]) -> list[dict[str, object]]:
    """Return a simplified status view for the requested units."""

    statuses: list[dict[str, object]] = []
    for unit in units:
        unit = unit.strip()
        if not unit:
            continue
        try:
            result = _run_systemctl(
                [
                    "status",
                    "--no-pager",
                    unit,
                ],
                allow_failure=True,
            )
            stdout = result.stdout
            details = stdout.splitlines()
            active_line = next((line.strip() for line in details if "Active:" in line), "")
            loaded_line = next((line.strip() for line in details if "Loaded:" in line), "")
            statuses.append(
                {
                    "unit": unit,
                    "status": "ok",  # will be corrected below if necessary
                    "details": {
                        "output": stdout,
                        "returncode": result.returncode,
                        "systemctl": {
                            "loaded": loaded_line,
                            "active": active_line,
                        },
                    },
                }
            )
        except SystemdDiscoveryError as exc:
            statuses.append(
                {
                    "unit": unit,
                    "status": "error",
                    "details": {"error": str(exc)},
                }
            )
            continue

        active_line = statuses[-1]["details"]["systemctl"].get("active", "").lower()
        if active_line.startswith("active: active"):
            statuses[-1]["status"] = "ok"
        else:
            statuses[-1]["status"] = "error"

    return statuses

