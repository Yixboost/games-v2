from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from core.cache import cache
from core.templates import templates, base_context

class GameTilesService:
    def __init__(
        self,
        game_service,
    ):
        self.game_service = game_service
    def get_games(
        self,
        *,
        category=None,
        name_contains=None,
        limit=24,
        order="number",
    ):
        cache_key = (
            "game_tiles:"
            f"{category}:"
            f"{name_contains}:"
            f"{limit}:"
            f"{order}"
        )

        if cache_key in cache:
            return cache[cache_key]

        query = """
        SELECT *
        FROM games
        WHERE 1=1
        """
        params = {}

        if category:
            query += """
            AND LOWER(category) = LOWER(:category)
            """
            params["category"] = category

        if name_contains:
            query += """
            AND LOWER(name) LIKE LOWER(:name)
            """
            params["name"] = (
                f"%{name_contains}%"
            )

        order_map = {
            "number": "number ASC",
            "name": "name ASC",
            "random": "RANDOM()",
        }

        query += f"""
        ORDER BY {order_map.get(
            order,
            "number ASC"
        )}
        """
        query += """
        LIMIT :limit
        """
        params["limit"] = limit
        games = self.game_service.database.fetch_all(
            query,
            params,
        )

        cache[cache_key] = games
        return games

    def category_exists(
        self,
        category,
    ):

        result = self.game_service.database.fetch_one(
            """
            SELECT category
            FROM games
            WHERE LOWER(category) = LOWER(:category)
            LIMIT 1
            """,
            {
                "category": category,
            },
        )

        return result is not None



class Plugin:
    name = "game_tiles"

    def __init__(self):
        self.router = APIRouter()
        self.service = None
        self._register_routes()

    def setup(
        self,
        app: FastAPI,
        context,
    ):

        game_service = context.services.get(
            "games"
        )

        if not game_service:
            raise RuntimeError(
                "game_tiles requires game_loader plugin"
            )

        self.service = GameTilesService(
            game_service
        )

        context.services.register(
            "game_tiles",
            self.service,
        )

        templates.env.globals[
            "game_tiles"
        ] = self.service.get_games

        app.include_router(
            self.router
        )

    def _register_routes(self):
        self.router.add_api_route(
            "/category/{category}",
            self.category_page,
            methods=["GET"],
            response_class=HTMLResponse,
        )

    async def category_page(
        self,
        request: Request,
        category: str,
    ):
        if not self.service.category_exists(
            category
        ):
            raise HTTPException(
                status_code=404,
                detail="Category not found",
            )

        games = self.service.get_games(
            category=category,
            limit=9999,
            order="name",
        )

        real_category = games[0]["category"]
        return templates.TemplateResponse(
            request=request,
            name="game_tiles/category.html",
            context=base_context(
                request,
                games=games,
                title=real_category,
            ),
        )