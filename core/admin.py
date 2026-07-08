from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse

from core.templates import base_context, templates


class Admin:
    name = "admin"

    def __init__(self):
        self.router = APIRouter()
        self.hooks = None

        self._register_routes()

    def setup(
        self,
        app: FastAPI,
        hooks,
    ) -> None:
        self.hooks = hooks

        app.include_router(
            self.router,
        )

    def _register_routes(self) -> None:
        self.router.add_api_route(
            "/admin",
            self.index,
            methods=["GET"],
            response_class=HTMLResponse,
        )

    def build_context(
        self,
        request: Request,
        **kwargs,
    ) -> dict:
        context = base_context(
            request,
            **kwargs,
        )

        context["current_path"] = request.url.path

        context["sidebar"] = ""
        context["dashboard"] = ""

        if self.hooks:
            context["sidebar"] = self.hooks.render(
                "admin_sidebar",
                context,
            )

            context["dashboard"] = self.hooks.render(
                "admin_dashboard",
                context,
            )

        return context

    async def index(
        self,
        request: Request,
    ):
        context = self.build_context(
            request,
        )

        return templates.TemplateResponse(
            request=request,
            name="admin/index.html",
            context=context,
        )


admin = Admin()


def setup_admin(
    app: FastAPI,
    hooks,
):
    admin.setup(
        app,
        hooks,
    )