from collections import defaultdict
from collections.abc import Callable
from typing import Any


class EventBus:
    def __init__(self):
        self._listeners: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    def on(self, event_name: str, handler: Callable[..., Any]) -> None:
        self._listeners[event_name].append(handler)

    def emit(self, event_name: str, **payload: Any) -> list[Any]:
        return [handler(**payload) for handler in self._listeners[event_name]]

    def clear(self) -> None:
        self._listeners.clear()


event_bus = EventBus()
