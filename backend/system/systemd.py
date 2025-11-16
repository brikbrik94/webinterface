"""Helpers for querying systemd-managed services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
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
JOURNALCTL = shutil.which("journalctl")

MAX_JOURNAL_ENTRIES = 1000

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


def _run_journalctl(arguments: Iterable[str]) -> subprocess.CompletedProcess[str]:
    if JOURNALCTL is None:
        raise SystemdDiscoveryError("journalctl executable is not available on this host")

    try:
        return subprocess.run(  # noqa: S603,S607 - trusted local execution
            [JOURNALCTL, *arguments],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:  # pragma: no cover - defensive fallback
        raise SystemdDiscoveryError("journalctl executable could not be found") from exc
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
        name = entry.get("name") or entry.get("unit")
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


def _format_timestamp(value: str | int | None) -> str:
    if value in (None, ""):
        return ""
    try:
        micros = int(value)
    except (TypeError, ValueError):
        return str(value)
    dt = datetime.fromtimestamp(micros / 1_000_000, tz=timezone.utc)
    return dt.isoformat()


PRIORITY_LABELS = {
    0: "emerg",
    1: "alert",
    2: "crit",
    3: "err",
    4: "warning",
    5: "notice",
    6: "info",
    7: "debug",
}


def _normalize_priority(value: str | int | None) -> str:
    if value in (None, ""):
        return "unknown"
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return str(value)
    return PRIORITY_LABELS.get(numeric, str(numeric))


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


def fetch_journal_entries(
    unit: str,
    *,
    limit: int = 200,
    since: str | None = None,
) -> list[dict[str, str]]:
    """Return the latest journalctl entries for the given systemd unit."""

    if not unit:
        raise SystemdDiscoveryError("A systemd unit must be provided to query journalctl")

    if limit < 1:
        limit = 1
    elif limit > MAX_JOURNAL_ENTRIES:
        limit = MAX_JOURNAL_ENTRIES

    arguments = [
        "-u",
        unit,
        "--no-pager",
        "--output=json",
        "-n",
        str(limit),
    ]
    if since:
        arguments.extend(["--since", since])

    result = _run_journalctl(arguments)
    entries: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        timestamp = payload.get("__REALTIME_TIMESTAMP") or payload.get("_SOURCE_REALTIME_TIMESTAMP")
        message = payload.get("MESSAGE") or ""
        identifier = (
            payload.get("SYSLOG_IDENTIFIER")
            or payload.get("_SYSTEMD_UNIT")
            or payload.get("_COMM")
            or unit
        )
        entries.append(
            {
                "timestamp": _format_timestamp(timestamp),
                "message": message.strip(),
                "priority": _normalize_priority(payload.get("PRIORITY")),
                "identifier": identifier,
            }
        )
    return entries

