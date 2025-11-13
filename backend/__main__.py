"""Command-line entry point to start the FastAPI app with sensible defaults."""
from __future__ import annotations

import os
from typing import Final

import uvicorn


def _bool_from_env(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def main() -> None:
    """Start the API server and expose it to the local network by default."""

    host: Final[str] = os.getenv("WEB_HOST", "0.0.0.0")
    port: Final[int] = int(os.getenv("WEB_PORT", "8000"))
    reload_enabled: Final[bool] = _bool_from_env(os.getenv("WEB_RELOAD"))

    uvicorn.run(
        "backend.app:app",
        host=host,
        port=port,
        reload=reload_enabled,
        factory=False,
    )


if __name__ == "__main__":
    main()
