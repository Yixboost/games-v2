from dataclasses import dataclass
import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from core.auth import login_user, logout_user
from core.config import settings
from core.user_service import user_service

router = APIRouter(prefix="/auth", tags=["Auth"])
OAUTH_STATE_TTL_SECONDS = 600


@dataclass(frozen=True)
class OpenIDProviderMetadata:
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str


def get_provider_metadata() -> OpenIDProviderMetadata:
    authorization_endpoint = settings.oauth_authorization_endpoint
    token_endpoint = settings.oauth_token_endpoint
    userinfo_endpoint = settings.oauth_userinfo_endpoint

    if settings.oauth_well_known_url:
        response = requests.get(settings.oauth_well_known_url, timeout=10)
        response.raise_for_status()
        metadata = response.json()
        authorization_endpoint = authorization_endpoint or metadata["authorization_endpoint"]
        token_endpoint = token_endpoint or metadata["token_endpoint"]
        userinfo_endpoint = userinfo_endpoint or metadata["userinfo_endpoint"]

    if not authorization_endpoint or not token_endpoint or not userinfo_endpoint:
        raise RuntimeError("OAuth provider endpoints are not configured.")

    return OpenIDProviderMetadata(
        authorization_endpoint=authorization_endpoint,
        token_endpoint=token_endpoint,
        userinfo_endpoint=userinfo_endpoint,
    )


def _redirect_uri(request: Request) -> str:
    if settings.oauth_redirect_uri:
        return settings.oauth_redirect_uri

    return str(request.url_for("oauth_callback"))


def _sign_state(data: dict[str, Any]) -> str:
    payload = base64.urlsafe_b64encode(
        json.dumps(data, separators=(",", ":")).encode()
    ).decode()
    signature = hmac.new(
        settings.session_secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}.{signature}"


def _verify_state(state: str) -> dict[str, Any] | None:
    if not state or "." not in state:
        return None

    payload, signature = state.rsplit(".", 1)
    expected = hmac.new(
        settings.session_secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        return None

    try:
        data = json.loads(base64.urlsafe_b64decode(payload.encode()))
    except (ValueError, json.JSONDecodeError):
        return None

    issued_at = data.get("iat")
    if not isinstance(issued_at, int):
        return None

    if time.time() - issued_at > OAUTH_STATE_TTL_SECONDS:
        return None

    return data


@router.get("/login")
async def oauth_login(request: Request):
    if not settings.oauth_enabled:
        raise HTTPException(status_code=503, detail="OAuth login is not configured.")

    metadata = get_provider_metadata()
    state_nonce = secrets.token_urlsafe(32)
    state = _sign_state(
        {
            "nonce": state_nonce,
            "iat": int(time.time()),
        }
    )
    request.state.session["oauth_state"] = state_nonce
    request.state.session_modified = True

    params = {
        "response_type": "code",
        "client_id": settings.oauth_client_id,
        "redirect_uri": _redirect_uri(request),
        "scope": settings.oauth_scope,
        "state": state,
    }

    return RedirectResponse(
        f"{metadata.authorization_endpoint}?{urlencode(params)}",
        status_code=303,
    )


@router.get("/callback", name="oauth_callback")
async def oauth_callback(request: Request, code: str = "", state: str = ""):
    if not settings.oauth_enabled:
        raise HTTPException(status_code=503, detail="OAuth login is not configured.")

    expected_nonce = request.state.session.pop("oauth_state", None)
    request.state.session_modified = True

    state_data = _verify_state(state)
    state_nonce = state_data.get("nonce") if state_data else None

    if not state_nonce:
        raise HTTPException(status_code=400, detail="Invalid OAuth state.")

    if expected_nonce and not secrets.compare_digest(expected_nonce, state_nonce):
        raise HTTPException(status_code=400, detail="Invalid OAuth state.")

    metadata = get_provider_metadata()
    token_response = requests.post(
        metadata.token_endpoint,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": _redirect_uri(request),
            "client_id": settings.oauth_client_id,
            "client_secret": settings.oauth_client_secret,
        },
        headers={"Accept": "application/json"},
        timeout=10,
    )
    token_response.raise_for_status()
    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="OAuth provider did not return an access token.")

    userinfo_response = requests.get(
        metadata.userinfo_endpoint,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        timeout=10,
    )
    userinfo_response.raise_for_status()
    userinfo = userinfo_response.json()

    subject = userinfo.get("sub")
    if not subject:
        raise HTTPException(status_code=400, detail="OAuth provider did not return a subject.")

    name = userinfo.get("name") or userinfo.get("preferred_username") or userinfo.get("email") or subject
    user = user_service.upsert_oauth_user(
        provider=settings.oauth_provider_name,
        subject=subject,
        name=name,
        username=userinfo.get("preferred_username") or name,
        email=userinfo.get("email"),
        profile_picture_url=userinfo.get("picture"),
    )
    login_user(request, user)

    return RedirectResponse("/profile", status_code=303)


@router.post("/logout")
@router.get("/logout")
async def logout(request: Request):
    logout_user(request)
    return RedirectResponse("/", status_code=303)
