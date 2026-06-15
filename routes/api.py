from fastapi import APIRouter

from database import SessionLocal
from models import Game
from cache import cache

router = APIRouter(
    prefix="/api",
    tags=["API"]
)


@router.get("/games")
async def get_games():
    if "games" in cache:
        return cache["games"]

    db = SessionLocal()

    try:
        games = db.query(Game).all()

        result = [
            {
                "id": game.id,
                "name": game.name,
                "image_url": game.image_url,
                "category": game.category
            }
            for game in games
        ]

        cache["games"] = result

        return result

    finally:
        db.close()