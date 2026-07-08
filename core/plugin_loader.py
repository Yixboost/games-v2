from dataclasses import dataclass
from importlib import import_module
import importlib.util
import json
import logging
from pathlib import Path
from typing import Protocol

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from core.auth import current_user, require_permission, require_user
from core.database import engine
from core.events import event_bus
from core.hooks import hook_registry
from core.permissions import permission_registry
from core.plugin_database import PluginDatabase
from core.services import service_registry
from core.templates import register_template_dir, templates, base_context, render_template
from core.paths import path_manager
from core.admin import admin

logger = logging.getLogger(__name__)

plugin_database = PluginDatabase(
    engine
)

class Plugin(Protocol):
    name: str

    def setup(
        self,
        app: FastAPI,
        context: "PluginContext",
    ) -> None:
        ...


@dataclass(frozen=True)
class PluginManifest:
    name: str
    version: str
    description: str = ""
    depends: tuple[str, ...] = ()
    database: dict | None = None
    libraries: tuple[str, ...] = ()


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

    def is_logged_in(self, request):
        return current_user(request) is not None

    def has_role(
        self,
        request,
        role_name: str,
    ):
        user = current_user(request)

        return bool(
            user and getattr(
                user,
                "role",
                None,
            ) == role_name
        )

    def has_permission(
        self,
        request,
        permission: str,
    ):
        user = current_user(request)

        return permission_registry.user_has_permission(
            user,
            permission,
        )

    def require_user(
        self,
        request,
    ):
        return require_user(request)

    def require_permission(
        self,
        request,
        permission: str,
    ):
        return require_permission(
            request,
            permission,
        )


class PluginLoader:

    def __init__(
        self,
        app: FastAPI,
    ):
        self.app = app

        self.loaded_plugins = []
        self.mounted_static = set()

        self.plugin_state_file = (
            path_manager.paths.root
            / "data"
            / "plugins.json"
        )

        self.plugin_states = self._load_plugin_states()

        self._register_admin_routes()


    def load_many(
        self,
        plugin_packages: tuple[str, ...],
    ):

        manifests = {
            package: self._read_manifest(package)
            for package in plugin_packages
        }

        for module_path in self._resolve_load_order(
            manifests
        ):
            plugin = self.load(
                module_path
            )

            if plugin:
                self.loaded_plugins.append(
                    plugin
                )

        return self.loaded_plugins


    def discover(
        self,
        namespace="plugins",
    ):

        namespace_module = import_module(
            namespace
        )

        if not namespace_module.__file__:
            return ()

        directory = Path(
            namespace_module.__file__
        ).parent

        plugins = []

        for path in sorted(
            directory.iterdir()
        ):

            if not path.is_dir():
                continue

            if (
                (path / "plugin.json").exists()
                and
                (path / "plugin.py").exists()
            ):
                plugins.append(
                    f"{namespace}.{path.name}"
                )

        return tuple(plugins)


    def load(
        self,
        plugin_package: str,
    ):

        manifest = self._read_manifest(
            plugin_package
        )


        if not self.is_enabled(
            manifest.name
        ):
            logger.info(
                "Plugin disabled: %s",
                manifest.name,
            )

            return None


        if not self._check_libraries(
            manifest
        ):
            return None


        module = import_module(
            f"{plugin_package}.plugin"
        )


        if not hasattr(
            module,
            "Plugin",
        ):
            raise RuntimeError(
                f"Plugin '{plugin_package}' has no Plugin class."
            )


        plugin_dir = self._plugin_dir(
            plugin_package
        )


        template_dir = plugin_dir / "templates"

        if template_dir.exists():
            register_template_dir(
                template_dir
            )


        self._register_static(
            plugin_package,
            plugin_dir,
        )


        if manifest.database:
            plugin_database.apply_manifest_requirements(
                manifest.database
            )


        plugin = module.Plugin()


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


        return LoadedPlugin(
            name=manifest.name,
            module_path=plugin_package,
            version=manifest.version,
        )


    def _check_libraries(
        self,
        manifest,
    ):

        missing = []

        for library in manifest.libraries:

            if importlib.util.find_spec(
                library
            ) is None:
                missing.append(
                    library
                )


        if missing:

            logger.error(
                "Plugin '%s' disabled. Missing libraries: %s",
                manifest.name,
                ", ".join(missing),
            )

            return False


        return True


    def _register_static(
        self,
        plugin_package,
        plugin_dir,
    ):

        static_dir = plugin_dir / "static"

        if not static_dir.exists():
            return


        plugin_id = plugin_package.split(".")[-1]


        if plugin_id in self.mounted_static:
            return


        self.app.mount(
            f"/static/{plugin_id}",
            StaticFiles(
                directory=static_dir
            ),
            name=f"{plugin_id}-static",
        )


        self.mounted_static.add(
            plugin_id
        )


    def _resolve_load_order(
        self,
        manifests,
    ):

        remaining = dict(manifests)

        loaded = set()

        ordered = []


        while remaining:

            progress = False


            for package, manifest in list(
                remaining.items()
            ):

                if set(
                    manifest.depends
                ).issubset(
                    loaded
                ):

                    ordered.append(
                        package
                    )

                    loaded.add(
                        manifest.name
                    )

                    del remaining[package]

                    progress = True


            if not progress:

                raise RuntimeError(
                    f"Plugin dependency error: {remaining}"
                )


        return ordered


    def _read_manifest(
        self,
        plugin_package,
    ):

        path = self._plugin_dir(
            plugin_package
        ) / "plugin.json"


        with path.open() as file:
            data = json.load(file)


        return PluginManifest(
            name=data["name"],
            version=data["version"],
            description=data.get(
                "description",
                "",
            ),
            depends=tuple(
                data.get(
                    "depends",
                    [],
                )
            ),
            database=data.get(
                "database"
            ),
            libraries=tuple(
                data.get(
                    "libraries",
                    [],
                )
            ),
        )


    @staticmethod
    def _plugin_dir(
        plugin_package,
    ):

        module = import_module(
            plugin_package
        )

        return Path(
            module.__file__
        ).parent



    def _load_plugin_states(self):

        if not self.plugin_state_file.exists():
            return {}


        with self.plugin_state_file.open() as file:
            return json.load(file)



    def _save_plugin_states(self):

        self.plugin_state_file.parent.mkdir(
            exist_ok=True
        )

        with self.plugin_state_file.open("w") as file:
            json.dump(
                self.plugin_states,
                file,
                indent=4,
            )



    def is_enabled(
        self,
        name,
    ):

        return self.plugin_states.get(
            name,
            True,
        )



    def set_enabled(
        self,
        name,
        enabled,
    ):

        self.plugin_states[name] = enabled

        self._save_plugin_states()



    def _register_admin_routes(self):

        self.app.add_api_route(
            "/admin/plugins",
            self.admin_plugins,
            methods=["GET"],
            response_class=HTMLResponse,
        )

        self.app.add_api_route(
            "/admin/plugins/{plugin_name}/toggle",
            self.toggle_plugin,
            methods=["POST"],
        )


    async def admin_plugins(
        self,
        request: Request,
    ):
        plugins = []

        for package in self.discover():
            manifest = self._read_manifest(package)

            plugins.append(
                {
                    "name": manifest.name,
                    "version": manifest.version,
                    "description": manifest.description,
                    "enabled": self.is_enabled(
                        manifest.name
                    ),
                }
            )

        return templates.TemplateResponse(
            request=request,
            name="admin/plugins.html",
            context=admin.build_context(
                request,
                plugins=plugins,
            ),
        )


    async def toggle_plugin(
        self,
        plugin_name: str,
    ):

        self.set_enabled(
            plugin_name,
            not self.is_enabled(
                plugin_name
            ),
        )


        return RedirectResponse(
            "/admin/plugins",
            status_code=303,
        )