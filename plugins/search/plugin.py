from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse
import math
from core.templates import base_context, render_template, templates


class Plugin:
	name = "search"

	def __init__(self):
		self.router = APIRouter()
		self.game_service = None
		self._register_routes()

	def setup(self, app: FastAPI, context) -> None:
		self.game_service = context.services.get("games")
		context.hooks.register("navbar_actions", self._render_navbar_search)
		app.include_router(self.router)

	def _register_routes(self) -> None:
		self.router.add_api_route(
			"/search",
			self.search,
			methods=["GET"],
			response_class=HTMLResponse,
		)

	async def search(self, request: Request, q: str = "", page: int = 1):
		query = q.strip()
		if page < 1:
			page = 1
		if query:
			all_games = self.game_service.search_games(query)
		else:
			all_games = []
		per_page = 24
		total_games = len(all_games)
		total_pages = max(1, math.ceil(total_games / per_page))

		if page > total_pages:
			page = total_pages
		start = (page - 1) * per_page
		games = all_games[start : start + per_page]

		return templates.TemplateResponse(
			name="search/search.html",
			request=request,
			context=base_context(
				request,
				query=query,
				games=games,
				current_page=page,
				total_pages=total_pages,
			),
		)

	@staticmethod
	def _render_navbar_search(context: dict) -> str:
		return render_template("search/navbar_search.html", context)
