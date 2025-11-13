"""Utilities for interacting with the local operating system."""

from .systemd import (
    SystemdDiscoveryError,
    SystemdService,
    list_systemd_services,
    service_states_for_units,
)

__all__ = [
    "SystemdDiscoveryError",
    "SystemdService",
    "list_systemd_services",
    "service_states_for_units",
]

