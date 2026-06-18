from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.config import settings
from core.database import Base, engine
from core.errors import HTTP_EXCEPTIONS
from core.events import event_bus
from core.hooks import hook_registry
from core.permissions import permission_registry
from core.plugin_loader import PluginLoader
from core.routes import router as core_router
from core.services import service_registry


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        exception_handlers=HTTP_EXCEPTIONS,
    )

    Base.metadata.create_all(bind=engine)
    service_registry.clear()
    event_bus.clear()
    hook_registry.clear()
    permission_registry.clear()

    app.mount(
        "/assets",
        StaticFiles(directory=str(settings.static_dir)),
        name="static",
    )

    app.include_router(core_router)

    loader = PluginLoader(app)
    plugin_packages = tuple(
        dict.fromkeys(
            settings.builtin_plugins
            + loader.discover("plugins")
            + settings.external_plugin_packages
        )
    )
    app.state.plugins = loader.load_many(
        plugin_packages,
    )

    return app


app = create_app()
