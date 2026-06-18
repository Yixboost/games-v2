from typing import Any


class ServiceRegistry:
    def __init__(self):
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        if name in self._services:
            raise RuntimeError(f"Service '{name}' is already registered.")

        self._services[name] = service

    def get(self, name: str) -> Any:
        if name not in self._services:
            raise RuntimeError(f"Service '{name}' is not registered.")

        return self._services[name]

    def has(self, name: str) -> bool:
        return name in self._services

    def clear(self) -> None:
        self._services.clear()


service_registry = ServiceRegistry()
