"""Service adapter registry and factory utilities."""
from __future__ import annotations

from importlib import import_module
from typing import Dict, Iterable, List, Mapping, Type

from .base import ServiceAdapter


class AdapterRegistry:
    """Central registry holding service adapter classes."""

    def __init__(self) -> None:
        self._registry: Dict[str, Type[ServiceAdapter]] = {}

    def register(self, adapter_type: str, adapter_cls: Type[ServiceAdapter]) -> None:
        if adapter_type in self._registry:
            raise ValueError(f"Adapter type '{adapter_type}' is already registered")
        self._registry[adapter_type] = adapter_cls

    def get(self, adapter_type: str) -> Type[ServiceAdapter]:
        try:
            return self._registry[adapter_type]
        except KeyError as exc:
            raise KeyError(
                f"No adapter registered for type '{adapter_type}'."
                " Ensure the module defining it is imported."
            ) from exc

    def available_adapters(self) -> Mapping[str, Type[ServiceAdapter]]:
        return dict(self._registry)


registry = AdapterRegistry()


def import_string(dotted_path: str) -> Type[ServiceAdapter]:
    """Resolve an adapter class from a dotted import path."""
    module_path, _, class_name = dotted_path.rpartition(".")
    if not module_path:
        raise ValueError(f"Invalid adapter path '{dotted_path}'. Must include module.")

    module = import_module(module_path)
    try:
        adapter_cls = getattr(module, class_name)
    except AttributeError as exc:  # pragma: no cover - simple attribute error
        raise ImportError(
            f"Module '{module_path}' does not define a '{class_name}' adapter"
        ) from exc

    if not issubclass(adapter_cls, ServiceAdapter):
        raise TypeError(f"Adapter '{dotted_path}' must subclass ServiceAdapter")
    return adapter_cls


def build_adapters(configs: Iterable[Mapping[str, object]]) -> List[ServiceAdapter]:
    """Instantiate adapters from configuration entries."""

    adapters: List[ServiceAdapter] = []
    for config in configs:
        adapter_type = config["adapter"]
        adapter_cls = registry.available_adapters().get(adapter_type)
        if adapter_cls is None:
            adapter_cls = import_string(adapter_type)
        adapters.append(adapter_cls(**config["init_args"]))
    return adapters


__all__ = ["registry", "AdapterRegistry", "build_adapters", "import_string"]
