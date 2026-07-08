import random

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

from core.cache import cache
from core.templates import base_context, templates



class GameService:

    def __init__(
        self,
        database,
    ):
        self.database = database



    def list_games(self):

        return self.database.fetch_all(
            """
            SELECT *
            FROM games
            ORDER BY number ASC
            """
        )



    def get_game(
        self,
        game_id: str,
    ):

        return self.database.fetch_one(
            """
            SELECT *
            FROM games
            WHERE id = :id
            LIMIT 1
            """,
            {
                "id": game_id,
            },
        )



    def search_games(
        self,
        query: str,
    ):

        return self.database.fetch_all(
            """
            SELECT *
            FROM games
            WHERE name LIKE :query
            ORDER BY name ASC
            """,
            {
                "query": f"%{query}%",
            },
        )



    def get_related_games(
        self,
        game,
        limit: int = 4,
    ):

        words = {
            word.lower()
            for word in game["name"].split()
            if not word.isdigit()
            and len(word) > 2
        }


        related = []


        if words:

            conditions = " OR ".join(
                [
                    f"name LIKE :word{i}"
                    for i in range(len(words))
                ]
            )


            params = {
                f"word{i}": f"%{word}%"
                for i, word in enumerate(words)
            }

            params["id"] = game["id"]


            candidates = self.database.fetch_all(
                f"""
                SELECT *
                FROM games
                WHERE id != :id
                AND ({conditions})
                """,
                params,
            )


            scored = []

            for item in candidates:

                score = 0

                item_words = {
                    word.lower()
                    for word in item["name"].split()
                }


                for keyword in words:

                    if keyword in item_words:
                        score += 10

                    elif any(
                        keyword in word
                        for word in item_words
                    ):
                        score += 3


                if score:
                    scored.append(
                        (
                            score,
                            item,
                        )
                    )


            scored.sort(
                key=lambda x: x[0],
                reverse=True,
            )


            for _, item in scored:

                related.append(
                    item
                )

                if len(related) >= limit:
                    break



        if len(related) < limit:

            used_ids = [
                item["id"]
                for item in related
            ]

            used_ids.append(
                game["id"]
            )


            extra = self.database.fetch_all(
                """
                SELECT *
                FROM games
                WHERE category = :category
                """,
                {
                    "category": game["category"],
                },
            )


            extra = [
                item
                for item in extra
                if item["id"] not in used_ids
            ]


            random.shuffle(
                extra
            )


            related.extend(
                extra[
                    :limit - len(related)
                ]
            )


        random.shuffle(
            related
        )


        return related[:limit]





class Plugin:

    name = "game_loader"



    def __init__(self):

        self.router = APIRouter()

        self.api_router = APIRouter(
            prefix="/api/v1",
            tags=["API"],
        )

        self.game_service = None
        self.hooks = None

        self._register_routes()



    def setup(
        self,
        app: FastAPI,
        context,
    ):

        self.game_service = GameService(
            context.database
        )

        self.hooks = context.hooks


        context.services.register(
            "games",
            self.game_service,
        )


        app.include_router(
            self.router
        )

        app.include_router(
            self.api_router
        )



    def _register_routes(self):

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


        self.router.add_api_route(
            "/g/loader/{game_id}",
            self.game_loader,
            methods=["GET"],
            response_class=HTMLResponse,
        )


        self.router.add_api_route(
            "/g/embed/{game_id}",
            self.game_embed,
            methods=["GET"],
            response_class=HTMLResponse,
        )


        self.api_router.add_api_route(
            "/games",
            self.get_games,
            methods=["GET"],
        )



    async def home(
        self,
        request: Request,
    ):

        return templates.TemplateResponse(
            request=request,
            name="game_loader/index.html",
            context=base_context(
                request,
                games=self._homepage_games(),
            ),
        )



    async def game_detail(
        self,
        request: Request,
        game_id: str,
    ):

        game = self._get_game(
            game_id
        )


        if not game:

            raise HTTPException(
                404,
                "Game not found",
            )


        return templates.TemplateResponse(
            request=request,
            name="game_loader/game.html",
            context=base_context(
                request,
                game=game,
                related_games=self.game_service.get_related_games(
                    game
                ),
                game_actions=self.hooks.run(
                    "game_actions",
                    {
                        "request": request,
                        "game": game,
                    },
                ),
            ),
        )



    async def game_loader(
        self,
        request: Request,
        game_id: str,
    ):

        return await self._render_game_page(
            request,
            game_id,
            "game_loader/game_loader.html",
        )



    async def game_embed(
        self,
        request: Request,
        game_id: str,
    ):

        return await self._render_game_page(
            request,
            game_id,
            "game_loader/game_embed.html",
        )



    async def _render_game_page(
        self,
        request,
        game_id,
        template,
    ):

        game = self._get_game(
            game_id
        )


        if not game:

            raise HTTPException(
                404,
                "Game not found",
            )


        return templates.TemplateResponse(
            request=request,
            name=template,
            context=base_context(
                request,
                game=game,
            ),
        )



    async def get_games(self):

        if "games" not in cache:

            cache["games"] = [
                dict(game)
                for game in self.game_service.list_games()
            ]


        return cache["games"]



    def _homepage_games(self):

        if "homepage_games" not in cache:

            cache["homepage_games"] = (
                self.game_service.list_games()
            )


        return cache["homepage_games"]



    def _get_game(
        self,
        game_id,
    ):

        key = f"game:{game_id}"


        if key not in cache:

            cache[key] = (
                self.game_service.get_game(
                    game_id
                )
            )


        return cache[key]