from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.auth import auth_middleware
from core.config import settings
from core.database import Base, engine
from core.errors import HTTP_EXCEPTIONS
from core.events import event_bus
from core.hooks import hook_registry
from core.permissions import permission_registry
from core.permissions import Role
from core.plugin_loader import PluginLoader
from core.routes import router as core_router
from core.services import service_registry
from core.migrations import run_core_migrations
from core.oauth import router as auth_router
from core.templates import set_template_dirs
from core.theme import theme_manager
from core.user_service import user_service
from core.auth import current_user


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        exception_handlers=HTTP_EXCEPTIONS,
    )

    app.middleware("http")(auth_middleware)
    Base.metadata.create_all(bind=engine)
    run_core_migrations()
    settings.custom_plugins_dir.mkdir(exist_ok=True)
    settings.custom_themes_dir.mkdir(exist_ok=True)
    active_theme = theme_manager.find_theme()
    template_dirs = []
    if active_theme.templates_dir.exists():
        template_dirs.append(active_theme.templates_dir)
    template_dirs.append(settings.templates_dir)
    set_template_dirs(template_dirs)
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

    app.mount(
        "/assets",
        StaticFiles(directory=str(settings.static_dir)),
        name="static",
    )
    if active_theme.assets_dir.exists():
        app.mount(
            "/theme-assets",
            StaticFiles(directory=str(active_theme.assets_dir)),
            name="theme_assets",
        )

    app.include_router(core_router)
    app.include_router(auth_router)

    loader = PluginLoader(app)
    plugin_packages = tuple(
        dict.fromkeys(
            settings.builtin_plugins
            + loader.discover("plugins")
            + loader.discover("custom_plugins")
            + settings.external_plugin_packages
        )
    )
    app.state.plugins = loader.load_many(
        plugin_packages,
    )

    return app


app = create_app()
