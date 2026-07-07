from collections import defaultdict
from collections.abc import Callable
from typing import Any

from markupsafe import Markup


HookRenderer = Callable[[dict[str, Any]], str]


class HookRegistry:
    def __init__(self):
        self._hooks: dict[str, list[HookRenderer]] = defaultdict(list)

    def register(
        self,
        hook_name: str,
        renderer: HookRenderer,
    ) -> None:
        self._hooks[hook_name].append(renderer)

    def render(
        self,
        hook_name: str,
        context: dict[str, Any],
    ) -> Markup:
        output = ""

        for renderer in self._hooks.get(hook_name, []):
            result = renderer(context)

            if result:
                output += result

        return Markup(output)

    def run(
        self,
        hook_name: str,
        context: dict[str, Any],
    ) -> list[str]:
        results = []

        for renderer in self._hooks.get(hook_name, []):
            result = renderer(context)

            if result:
                results.append(result)

        return results

    def clear(self) -> None:
        self._hooks.clear()


hook_registry = HookRegistry()