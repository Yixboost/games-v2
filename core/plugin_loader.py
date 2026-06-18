from dataclasses import dataclass
from importlib import import_module
import json
from pathlib import Path
from typing import Protocol

from fastapi import FastAPI

from core.events import event_bus
from core.hooks import hook_registry
from core.permissions import permission_registry
from core.services import service_registry
from core.templates import register_template_dir


class Plugin(Protocol):
    name: str

    def setup(self, app: FastAPI, context: "PluginContext") -> None:
        ...


@dataclass(frozen=True)
class PluginManifest:
    name: str
    version: str
    description: str = ""
    depends: tuple[str, ...] = ()


@dataclass(frozen=True)
class LoadedPlugin:
    name: str
    module_path: str
    version: str


@dataclass(frozen=True)
class PluginContext:
    manifest: PluginManifest
    services: object
    events: object
    hooks: object
    permissions: object


class PluginLoader:
    def __init__(self, app: FastAPI):
        self.app = app
        self.loaded_plugins: list[LoadedPlugin] = []

    def load_many(self, plugin_packages: tuple[str, ...]) -> list[LoadedPlugin]:
        manifests = {
            plugin_package: self._read_manifest(plugin_package)
            for plugin_package in plugin_packages
        }

        for module_path in self._resolve_load_order(manifests):
            self.load(module_path)

        return self.loaded_plugins

    def discover(self, namespace: str = "plugins") -> tuple[str, ...]:
        namespace_module = import_module(namespace)
        if not namespace_module.__file__:
            return ()

        namespace_dir = Path(namespace_module.__file__).parent
        plugin_packages = []

        for path in sorted(namespace_dir.iterdir()):
            if not path.is_dir():
                continue

            if (path / "plugin.json").exists() and (path / "plugin.py").exists():
                plugin_packages.append(f"{namespace}.{path.name}")

        return tuple(plugin_packages)

    def load(self, plugin_package: str) -> LoadedPlugin:
        manifest = self._read_manifest(plugin_package)
        module = import_module(f"{plugin_package}.plugin")

        if not hasattr(module, "Plugin"):
            raise RuntimeError(f"Plugin module '{plugin_package}' does not expose 'Plugin'.")

        template_dir = self._plugin_dir(plugin_package) / "templates"
        if template_dir.exists():
            register_template_dir(template_dir)

        plugin: Plugin = module.Plugin()
        plugin.setup(
            self.app,
            PluginContext(
                manifest=manifest,
                services=service_registry,
                events=event_bus,
                hooks=hook_registry,
                permissions=permission_registry,
            ),
        )

        loaded_plugin = LoadedPlugin(
            name=manifest.name,
            module_path=plugin_package,
            version=manifest.version,
        )
        self.loaded_plugins.append(loaded_plugin)
        return loaded_plugin

    def _resolve_load_order(
        self,
        manifests: dict[str, PluginManifest],
    ) -> list[str]:
        remaining = dict(manifests)
        loaded_names: set[str] = set()
        ordered: list[str] = []

        while remaining:
            progressed = False

            for module_path, manifest in list(remaining.items()):
                if set(manifest.depends).issubset(loaded_names):
                    ordered.append(module_path)
                    loaded_names.add(manifest.name)
                    del remaining[module_path]
                    progressed = True

            if not progressed:
                unresolved = {
                    manifest.name: list(manifest.depends)
                    for manifest in remaining.values()
                }
                raise RuntimeError(f"Could not resolve plugin dependencies: {unresolved}")

        return ordered

    def _read_manifest(self, plugin_package: str) -> PluginManifest:
        manifest_path = self._plugin_dir(plugin_package) / "plugin.json"

        if not manifest_path.exists():
            raise RuntimeError(f"Plugin '{plugin_package}' is missing plugin.json.")

        with manifest_path.open() as manifest_file:
            data = json.load(manifest_file)

        return PluginManifest(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            depends=tuple(data.get("depends", [])),
        )

    @staticmethod
    def _plugin_dir(plugin_package: str) -> Path:
        module = import_module(plugin_package)
        if not module.__file__:
            raise RuntimeError(f"Plugin package '{plugin_package}' has no filesystem path.")

        return Path(module.__file__).parent
