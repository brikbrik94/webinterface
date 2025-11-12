"""Service adapters package."""
from .base import ServiceAdapter, ServiceState, ShellCommandMixin
from .local_commands import CommandService
from .registry import AdapterRegistry, registry

# Register default adapters on import (idempotent)
try:  # pragma: no cover - trivial guard
    registry.register("command", CommandService)
except ValueError:
    # Already registered by a prior import
    pass

__all__ = [
    "AdapterRegistry",
    "CommandService",
    "ServiceAdapter",
    "ServiceState",
    "ShellCommandMixin",
    "registry",
]
