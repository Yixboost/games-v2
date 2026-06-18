from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from core.auth import require_user
from core.templates import base_context, templates

router = APIRouter()


@router.get("/ping", response_class=PlainTextResponse)
async def ping():
    return "pong!"


@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    user = require_user(request)
    if not hasattr(user, "id"):
        return user

    return templates.TemplateResponse(
        name="profile.html",
        request=request,
        context=base_context(request, user=user),
    )
