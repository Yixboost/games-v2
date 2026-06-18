import base64
import hashlib
import hmac
import json
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

from core.config import settings
from core.permissions import permission_registry
from core.user_service import user_service


def _encode_session(data: dict[str, Any]) -> str:
    payload = base64.urlsafe_b64encode(
        json.dumps(data, separators=(",", ":")).encode()
    ).decode()
    signature = hmac.new(
        settings.session_secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}.{signature}"


def _decode_session(value: str | None) -> dict[str, Any]:
    if not value or "." not in value:
        return {}

    payload, signature = value.rsplit(".", 1)
    expected = hmac.new(
        settings.session_secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        return {}

    try:
        decoded = base64.urlsafe_b64decode(payload.encode())
        return json.loads(decoded)
    except (ValueError, json.JSONDecodeError):
        return {}


async def auth_middleware(request: Request, call_next):
    request.state.session = _decode_session(
        request.cookies.get(settings.session_cookie_name)
    )
    request.state.session_modified = False
    request.state.current_user = None

    user_id = request.state.session.get("user_id")
    if user_id is not None:
        request.state.current_user = user_service.get(int(user_id))

    response = await call_next(request)

    if request.state.session_modified:
        if request.state.session:
            response.set_cookie(
                settings.session_cookie_name,
                _encode_session(request.state.session),
                httponly=True,
                samesite="lax",
                secure=False,
            )
        else:
            response.delete_cookie(settings.session_cookie_name)

    return response


def login_user(request: Request, user) -> None:
    request.state.session["user_id"] = user.id
    request.state.session_modified = True
    request.state.current_user = user


def logout_user(request: Request) -> None:
    request.state.session.clear()
    request.state.session_modified = True
    request.state.current_user = None


def current_user(request: Request):
    return getattr(request.state, "current_user", None)


def require_user(request: Request):
    user = current_user(request)
    if user is None:
        return RedirectResponse("/auth/login", status_code=303)

    return user


def require_permission(request: Request, permission: str):
    user = current_user(request)
    if not permission_registry.user_has_permission(user, permission):
        raise HTTPException(status_code=403, detail="Missing permission")

    return user
