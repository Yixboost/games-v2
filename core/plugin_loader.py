from dataclasses import dataclass
from importlib import import_module
import json
from pathlib import Path
from typing import Protocol

from fastapi import FastAPI

from core.events import event_bus
from core.hooks import hook_registry
from core.permissions import permission_registry
from core.plugin_database import plugin_database
from core.services import service_registry
from core.templates import register_template_dir
from core.auth import current_user, require_permission, require_user


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
    database: dict | None = None


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
    database: object
    auth: object


class AuthContext:
    def current_user(self, request):
        return current_user(request)

    def is_logged_in(self, request) -> bool:
        return current_user(request) is not None

    def has_role(self, request, role_name: str) -> bool:
        user = current_user(request)
        return bool(user and getattr(user, "role", None) == role_name)

    def has_permission(self, request, permission: str) -> bool:
        user = current_user(request)
        return permission_registry.user_has_permission(user, permission)

    def require_user(self, request):
        return require_user(request)

    def require_permission(self, request, permission: str):
        return require_permission(request, permission)


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

        if manifest.database:
            plugin_database.apply_manifest_requirements(manifest.database)

        plugin: Plugin = module.Plugin()
        plugin.setup(
            self.app,
            PluginContext(
                manifest=manifest,
                services=service_registry,
                events=event_bus,
                hooks=hook_registry,
                permissions=permission_registry,
                database=plugin_database,
                auth=AuthContext(),
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
            database=data.get("database"),
        )

    @staticmethod
    def _plugin_dir(plugin_package: str) -> Path:
        module = import_module(plugin_package)
        if not module.__file__:
            raise RuntimeError(f"Plugin package '{plugin_package}' has no filesystem path.")

        return Path(module.__file__).parent
