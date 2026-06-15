from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Base, User, Game
from routes.api import router as api_router
from cache import cache

async def custom_404_exception_handler(request, exc):
    return templates.TemplateResponse(
        request=request,
        name="404.html",
        context={"current_year": datetime.now().year},
    )


HTTP_EXCEPTIONS = {404: custom_404_exception_handler}

app = FastAPI(exception_handlers=HTTP_EXCEPTIONS)
Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")

app.mount("/assets", StaticFiles(directory="static"), name="static")
app.include_router(api_router)

from cache import cache

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):

    games = cache.get("homepage_games")

    if games is None:
        db = SessionLocal()

        try:
            games = db.query(Game).all()

            cache["homepage_games"] = games

        finally:
            db.close()

    return templates.TemplateResponse(
        name="index.html",
        request=request,
        context={
            "current_year": datetime.now().year,
            "games": games
        }
    )


@app.get("/ping", response_class=PlainTextResponse)
async def ping():
    return "pong!"


@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    user = {
        "username": "Test User",
        "join_date": "2026-01-10"
    }

    return templates.TemplateResponse(
        name="profile.html",
        request=request,
        context={
            "user": user
        }
    )