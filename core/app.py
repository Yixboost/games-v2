from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.auth import auth_middleware, current_user
from core.config import settings
from core.database import Base, engine
from core.errors import HTTP_EXCEPTIONS
from core.events import event_bus
from core.hooks import hook_registry
from core.migrations import run_core_migrations
from core.oauth import router as auth_router
from core.paths import path_manager
from core.permissions import Role, permission_registry
from core.plugin_loader import PluginLoader
from core.routes import router as core_router
from core.services import service_registry
from core.templates import set_template_dirs
from core.user_service import user_service


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        exception_handlers=HTTP_EXCEPTIONS,
    )

    app.middleware("http")(auth_middleware)
    Base.metadata.create_all(bind=engine)
    run_core_migrations()
    set_template_dirs([path_manager.paths.templates_dir])
    service_registry.clear()
    service_registry.register("users", user_service)
    service_registry.register(
        "auth",
        {
            "current_user": current_user,
        },
    )

    event_bus.clear()
    hook_registry.clear()
    permission_registry.clear()

    permission_registry.register_role(
        Role(
            name="user",
            permissions={
                "profile.view_own",
            },
        )
    )

    permission_registry.register_role(
        Role(
            name="admin",
            permissions={
                "profile.view_own",
                "admin.access",
            },
        )
    )

    loader = PluginLoader(app)
    plugin_packages = tuple(
        dict.fromkeys(
            settings.builtin_plugins
            + settings.external_plugin_packages
        )
    )
    app.state.plugins = loader.load_many(plugin_packages)

    app.mount(
        "/static",
        StaticFiles(directory=path_manager.paths.static_dir),
        name="static",
    )

    app.include_router(core_router)
    app.include_router(auth_router)

    return app


app = create_app()