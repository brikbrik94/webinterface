"""Utilities for interacting with the local operating system."""

from .systemd import (
    SystemdDiscoveryError,
    SystemdService,
    fetch_journal_entries,
    list_systemd_services,
    service_states_for_units,
)

__all__ = [
    "SystemdDiscoveryError",
    "SystemdService",
    "fetch_journal_entries",
    "list_systemd_services",
    "service_states_for_units",
]

