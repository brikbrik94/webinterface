"""Minimal FastAPI backend exposing service status endpoints."""
from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .config.loader import ConfigError, ServiceConfig, load_config
from .services import ServiceAdapter, ServiceState, registry

app = FastAPI(title="Local Service Orchestrator", version="0.1.0")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="ui")


@app.get("/", include_in_schema=False)
def redirect_to_ui() -> RedirectResponse:
    """Redirect the root path to the static HTML test UI."""

    return RedirectResponse(url="/ui/", status_code=307)


def get_service_configs() -> list[ServiceConfig]:
    try:
        app_config = load_config()
    except ConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return app_config.services


def build_adapter(service_config: ServiceConfig) -> ServiceAdapter:
    adapter_cls = registry.available_adapters().get(service_config.adapter)
    if adapter_cls is None:
        raise HTTPException(
            status_code=500,
            detail=f"Adapter '{service_config.adapter}' is not registered.",
        )
    return adapter_cls(
        key=service_config.key,
        name=service_config.name,
        metadata=service_config.metadata,
        commands={
            "start": service_config.commands.start,
            "stop": service_config.commands.stop,
            "restart": service_config.commands.restart,
            "status": service_config.commands.status,
        },
    )


@app.get("/services")
def list_services(configs: list[ServiceConfig] = Depends(get_service_configs)) -> list[dict[str, str]]:
    return [
        {
            "key": service.key,
            "name": service.name,
            "adapter": service.adapter,
        }
        for service in configs
    ]


@app.get("/services/{service_key}")
def get_service_state(
    service_key: str,
    configs: list[ServiceConfig] = Depends(get_service_configs),
) -> dict[str, object]:
    for service_config in configs:
        if service_config.key == service_key:
            adapter = build_adapter(service_config)
            state: ServiceState = adapter.fetch_state()
            return {
                "key": service_config.key,
                "name": service_config.name,
                "status": state.status,
                "details": state.details,
                "metadata": service_config.metadata,
            }
    raise HTTPException(status_code=404, detail=f"Service '{service_key}' not found")
