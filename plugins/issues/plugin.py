from fastapi import APIRouter, FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from core.admin import admin
from core.templates import (
    base_context,
    render_template,
    templates,
)


class Plugin:

    name = "issues"


    def __init__(self):

        self.router = APIRouter()

        self.database = None

        self._register_routes()



    def setup(
        self,
        app: FastAPI,
        context,
    ):

        self.database = context.database


        context.hooks.register(
            "game_actions",
            self._render_report_button,
        )


        context.hooks.register(
            "admin_sidebar",
            self._render_admin_sidebar,
        )


        context.hooks.register(
            "admin_dashboard",
            self._render_admin_dashboard,
        )


        app.include_router(
            self.router
        )



    def _register_routes(self):

        self.router.add_api_route(
            "/report",
            self.report,
            methods=["GET"],
            response_class=HTMLResponse,
        )


        self.router.add_api_route(
            "/report",
            self.create_report,
            methods=["POST"],
            response_class=RedirectResponse,
        )


        self.router.add_api_route(
            "/admin/issues",
            self.admin_issues,
            methods=["GET"],
            response_class=HTMLResponse,
        )



    def _render_report_button(
        self,
        context: dict,
    ) -> str:

        return render_template(
            "issues/report_button.html",
            context,
        )



    def _render_admin_sidebar(
        self,
        context: dict,
    ) -> str:

        return render_template(
            "issues/admin/sidebar.html",
            context,
        )



    def _render_admin_dashboard(
        self,
        context: dict,
    ) -> str:

        open_issues = self.database.fetch_one(
            """
            SELECT COUNT(*) AS count
            FROM bug_reports
            WHERE status = 'open'
            """
        )


        return render_template(
            "issues/admin/dashboard.html",
            {
                **context,
                "open_issues": open_issues["count"],
            },
        )



    async def report(
        self,
        request: Request,
        success: bool = False,
        email: str = "",
        url: str = "",
        title: str = "",
        description: str = "",
    ):

        return templates.TemplateResponse(
            request=request,
            name="issues/report.html",
            context=base_context(
                request,
                success=success,
                email=email,
                url=url,
                title=title,
                description=description,
            ),
        )



    async def create_report(
        self,
        request: Request,
        email: str = Form(""),
        page_url: str = Form(""),
        title: str = Form(...),
        description: str = Form(...),
    ):

        self.database.execute(
            """
            INSERT INTO bug_reports
            (
                email,
                page_url,
                title,
                description
            )
            VALUES
            (
                :email,
                :page_url,
                :title,
                :description
            )
            """,
            {
                "email": email.strip()[:255],
                "page_url": page_url.strip()[:500],
                "title": title.strip()[:100],
                "description": description.strip()[:1000],
            },
        )


        return RedirectResponse(
            "/report?success=true",
            status_code=303,
        )



    async def admin_issues(
        self,
        request: Request,
    ):

        issues = self.database.fetch_all(
            """
            SELECT *
            FROM bug_reports
            ORDER BY id DESC
            """
        )


        return templates.TemplateResponse(
            request=request,
            name="issues/admin/index.html",
            context=admin.build_context(
                request,
                issues=issues,
            ),
        )