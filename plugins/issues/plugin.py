from fastapi import APIRouter, FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from sqlalchemy import text

from core.templates import base_context, templates
from core.plugin_database import plugin_database
from core.database import engine


class Plugin:
	name = "issues"

	def __init__(self):
		self.router = APIRouter()
		self._register_routes()

	def setup(self, app: FastAPI, context) -> None:
		plugin_database.require_table(
			"bug_reports",
			{
				"id": "INTEGER PRIMARY KEY AUTOINCREMENT",
				"email": "TEXT",
				"page_url": "TEXT",
				"title": "TEXT NOT NULL",
				"description": "TEXT NOT NULL",
				"status": "TEXT NOT NULL DEFAULT 'open'",
				"created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
			},
		)

		context.hooks.register(
			"game_actions",
			self._render_report_button,
		)

		app.include_router(self.router)

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

	def _render_report_button(self, context: dict) -> str:
		game = context["game"]

		return f"""
		<li>
			<a href="/report?url=/g/{game.id}&title=Report%20for%20{game.name}">
				<i class="fa-solid fa-flag text-danger"></i>
				Report
			</a>
		</li>
		"""

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
			name="issues/report.html",
			request=request,
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
		email = email.strip()
		page_url = page_url.strip()
		title = title.strip()
		description = description.strip()

		email = email[:255]
		page_url = page_url[:500]
		title = title[:100]
		description = description[:1000]

		with engine.begin() as connection:
			connection.execute(
				text(
					"""
					INSERT INTO bug_reports
					(email, page_url, title, description)
					VALUES
					(:email, :page_url, :title, :description)
					"""
				),
				{
					"email": email,
					"page_url": page_url,
					"title": title,
					"description": description,
				},
			)

		return RedirectResponse(
			url="/report?success=true",
			status_code=303,
		)