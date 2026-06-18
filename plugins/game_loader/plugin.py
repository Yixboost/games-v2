from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

from core.cache import cache
from core.database import SessionLocal
from core.models import Game
from core.templates import base_context, templates


class GameService:
    def list_games(self):
        db = SessionLocal()

        try:
            return db.query(Game).all()
        finally:
            db.close()

    def get_game(self, game_id: int):
        db = SessionLocal()

        try:
            return db.query(Game).filter(Game.id == game_id).first()
        finally:
            db.close()

    def search_games(self, query: str):
        db = SessionLocal()

        try:
            return (
                db.query(Game)
                .filter(Game.name.ilike(f"%{query}%"))
                .order_by(Game.name.asc())
                .all()
            )
        finally:
            db.close()


class Plugin:
    name = "game_loader"

    def __init__(self):
        self.router = APIRouter()
        self.api_router = APIRouter(
            prefix="/api/v1",
            tags=["API"],
        )
        self.game_service = GameService()
        self._register_routes()

    def setup(self, app: FastAPI, context) -> None:
        context.services.register("games", self.game_service)
        app.include_router(self.router)
        app.include_router(self.api_router)

    def _register_routes(self) -> None:
        self.router.add_api_route(
            "/",
            self.home,
            methods=["GET"],
            response_class=HTMLResponse,
        )
        self.router.add_api_route(
            "/g/{game_id}",
            self.game_detail,
            methods=["GET"],
            response_class=HTMLResponse,
        )
        self.api_router.add_api_route(
            "/games",
            self.get_games,
            methods=["GET"],
        )

    async def home(self, request: Request):
        games = self._get_homepage_games()

        return templates.TemplateResponse(
            name="game_loader/index.html",
            request=request,
            context=base_context(request, games=games),
        )

    async def game_detail(self, request: Request, game_id: int):
        game = self._get_game(game_id)

        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")

        return templates.TemplateResponse(
            name="game_loader/game.html",
            request=request,
            context=base_context(request, game=game),
        )

    async def get_games(self):
        if "games" in cache:
            return cache["games"]

        db = SessionLocal()

        try:
            games = self.game_service.list_games()
            result = [self._serialize_game(game) for game in games]
            cache["games"] = result
            return result
        finally:
            db.close()

    def _get_homepage_games(self):
        if "homepage_games" in cache:
            return cache["homepage_games"]

        games = self.game_service.list_games()
        cache["homepage_games"] = games
        return games

    def _get_game(self, game_id: int):
        cache_key = f"game:{game_id}"

        if cache_key in cache:
            return cache[cache_key]

        game = self.game_service.get_game(game_id)
        cache[cache_key] = game
        return game

    @staticmethod
    def _serialize_game(game: Game) -> dict:
        return {
            "id": game.id,
            "name": game.name,
            "image_url": game.image_url,
            "category": game.category,
        }
