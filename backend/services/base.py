"""Service adapter interface definitions.

These interfaces describe the contract that every service integration has to
implement to participate in the orchestration system. Adapters provide the
link between the generic API layer and the underlying execution environment
(systemd, docker, custom scripts, etc.).
"""
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional


@dataclass
class ServiceState:
    """Represents the current status of a managed service."""

    status: str
    details: Mapping[str, Any]


class ServiceAdapter(abc.ABC):
    """Abstract base class for service adapters.

    Concrete implementations must provide the ``fetch_state`` method and can
    optionally override the lifecycle hooks (``start``, ``stop``, ``restart``)
    when the runtime environment allows it.
    """

    key: str
    name: str
    metadata: Mapping[str, Any]

    def __init__(self, key: str, name: str, metadata: Optional[Mapping[str, Any]] = None):
        self.key = key
        self.name = name
        self.metadata = metadata or {}

    @abc.abstractmethod
    def fetch_state(self) -> ServiceState:
        """Retrieve the latest service state information."""

    def start(self) -> None:
        """Optional hook to start the service."""

    def stop(self) -> None:
        """Optional hook to stop the service."""

    def restart(self) -> None:
        """Optional hook to restart the service."""


class ShellCommandMixin:
    """Utility mixin that stores configured shell commands for lifecycle hooks."""

    def __init__(self, *, commands: Mapping[str, str] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.commands = dict(commands or {})

    def get_command(self, key: str) -> Optional[str]:
        return self.commands.get(key)


__all__ = ["ServiceAdapter", "ServiceState", "ShellCommandMixin"]
