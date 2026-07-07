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


    def get_game(self, game_id: str):
        db = SessionLocal()

        try:
            return (
                db.query(Game)
                .filter(Game.id == game_id)
                .first()
            )
        finally:
            db.close()


    def get_related_games(self, game: Game, limit: int = 4):
        db = SessionLocal()
        try:
            import random
            from sqlalchemy import or_
            words = [
                word.lower()
                for word in game.name.split()
                if not word.isdigit()
                and len(word) > 2
            ]
            related = []
            if words:
                filters = [
                    Game.name.ilike(f"%{word}%")
                    for word in words
                ]
                candidates = (
                    db.query(Game)
                    .filter(
                        Game.id != game.id,
                        or_(*filters)
                    )
                    .all()
                )
                score_groups = {}
                for item in candidates:
                    name_words = [
                        word.lower()
                        for word in item.name.split()
                    ]
                    score = 0
                    for keyword in words:
                        for name_word in name_words:
                            if name_word == keyword:
                                score += 10
                            elif keyword in name_word:
                                score += 3
                    if score > 0:
                        if score not in score_groups:
                            score_groups[score] = []
                        score_groups[score].append(item)
                related = []
                for score in sorted(
                    score_groups.keys(),
                    reverse=True
                ):
                    group = score_groups[score]
                    random.shuffle(group)
                    related.extend(group)
                    if len(related) >= limit:
                        break
                related = related[:limit]
            if len(related) < limit:
                existing_ids = [
                    item.id
                    for item in related
                ]
                existing_ids.append(game.id)
                extra_games = (
                    db.query(Game)
                    .filter(
                        Game.category == game.category,
                        ~Game.id.in_(existing_ids)
                    )
                    .all()
                )
                random.shuffle(extra_games)
                related.extend(
                    extra_games[:limit - len(related)]
                )
            random.shuffle(related)
            return related[:limit]
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
            tags=["API"]
        )

        self.game_service = GameService()

        self._register_routes()



    def setup(self, app: FastAPI, context):

        context.services.register(
            "games",
            self.game_service
        )

        app.include_router(self.router)
        app.include_router(self.api_router)



    def _register_routes(self):

        self.router.add_api_route(
            "/",
            self.home,
            methods=["GET"],
            response_class=HTMLResponse
        )


        self.router.add_api_route(
            "/g/{game_id}",
            self.game_detail,
            methods=["GET"],
            response_class=HTMLResponse
        )


        self.router.add_api_route(
            "/g/loader/{game_id}",
            self.game_loader,
            methods=["GET"],
            response_class=HTMLResponse
        )


        self.router.add_api_route(
            "/g/embed/{game_id}",
            self.game_embed,
            methods=["GET"],
            response_class=HTMLResponse
        )


        self.api_router.add_api_route(
            "/games",
            self.get_games,
            methods=["GET"]
        )



    async def home(self, request: Request):

        games = self._get_homepage_games()

        return templates.TemplateResponse(
            name="game_loader/index.html",
            request=request,
            context=base_context(
                request,
                games=games
            )
        )



    async def game_detail(
        self,
        request: Request,
        game_id: str
    ):

        game = self._get_game(game_id)

        if game is None:
            raise HTTPException(
                status_code=404,
                detail="Game not found"
            )


        related_games = self.game_service.get_related_games(
            game,
            limit=4
        )


        return templates.TemplateResponse(
            name="game_loader/game.html",
            request=request,
            context=base_context(
                request,
                game=game,
                related_games=related_games
            )
        )



    async def game_loader(
        self,
        request: Request,
        game_id: str
    ):

        game = self._get_game(game_id)

        if game is None:
            raise HTTPException(
                status_code=404,
                detail="Game not found"
            )


        return templates.TemplateResponse(
            name="game_loader/game_loader.html",
            request=request,
            context=base_context(
                request,
                game=game
            )
        )



    async def game_embed(
        self,
        request: Request,
        game_id: str
    ):

        game = self._get_game(game_id)

        if game is None:
            raise HTTPException(
                status_code=404,
                detail="Game not found"
            )


        return templates.TemplateResponse(
            name="game_loader/game_embed.html",
            request=request,
            context=base_context(
                request,
                game=game
            )
        )



    async def get_games(self):

        if "games" in cache:
            return cache["games"]


        games = self.game_service.list_games()


        result = [
            self._serialize_game(game)
            for game in games
        ]


        cache["games"] = result

        return result



    def _get_homepage_games(self):

        if "homepage_games" not in cache:
            cache["homepage_games"] = self.game_service.list_games()


        return cache["homepage_games"]



    def _get_game(self, game_id: str):

        cache_key = f"game:{game_id}"


        if cache_key not in cache:
            cache[cache_key] = self.game_service.get_game(game_id)


        return cache[cache_key]



    @staticmethod
    def _serialize_game(game: Game):

        return {
            "id": game.id,
            "number": game.number,
            "name": game.name,
            "image_url": game.image_url,
            "category": game.category
        }