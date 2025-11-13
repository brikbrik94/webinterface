"""Configuration loading utilities for the service orchestrator backend."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# The configuration file should be resolved relative to the project root so that
# loading works no matter which working directory the process starts from.
_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = _REPO_ROOT / "config" / "services.yaml"


@dataclass
class ServiceCommand:
    """Runtime command definition for a service.

    Attributes:
        start: Command used to start the service.
        stop: Optional command used to stop the service.
        restart: Optional command used to restart the service.
        status: Optional command used to retrieve the service status.
    """

    start: str
    stop: Optional[str] = None
    restart: Optional[str] = None
    status: Optional[str] = None


@dataclass
class ServiceConfig:
    """Configuration entry describing a managed service."""

    key: str
    name: str
    adapter: str
    commands: ServiceCommand
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppConfig:
    """Top-level application configuration."""

    services: List[ServiceConfig]


class ConfigError(Exception):
    """Raised when the configuration file is invalid."""


def load_config(path: Path | None = None) -> AppConfig:
    """Load the application configuration from ``path``.

    Args:
        path: Optional path to the configuration YAML file. Defaults to
            ``config/services.yaml`` relative to the repository root.

    Raises:
        ConfigError: If the configuration file is missing required fields.

    Returns:
        Parsed :class:`AppConfig` instance.
    """

    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise ConfigError(f"Configuration file not found at {config_path!s}")

    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    services_data = data.get("services")
    if services_data is None:
        raise ConfigError("The configuration must define a 'services' list")

    services: List[ServiceConfig] = []
    for raw_service in services_data:
        try:
            commands = raw_service["commands"]
            service_config = ServiceConfig(
                key=raw_service["key"],
                name=raw_service.get("name", raw_service["key"].title()),
                adapter=raw_service["adapter"],
                commands=ServiceCommand(
                    start=commands["start"],
                    stop=commands.get("stop"),
                    restart=commands.get("restart"),
                    status=commands.get("status"),
                ),
                metadata=raw_service.get("metadata", {}),
            )
        except KeyError as exc:  # pragma: no cover - simple mapping error
            raise ConfigError(
                f"Missing required service attribute {exc} in configuration"
            ) from exc

        services.append(service_config)

    return AppConfig(services=services)


__all__ = ["AppConfig", "ServiceConfig", "ServiceCommand", "ConfigError", "load_config"]
