from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Settings:
    app_name: str = "Yixboost Games"
    database_url: str = "sqlite:///data/database.db"
    data_dir: Path = Path("data")
    static_dir: Path = Path("static")
    templates_dir: Path = Path("templates")
    builtin_plugins: tuple[str, ...] = (
        "plugins.game_loader",
        "plugins.search",
        "plugins.issues"
    )
    external_plugin_packages: tuple[str, ...] = field(default_factory=tuple)
    session_cookie_name: str = "games_session"
    session_secret: str = "change-me-in-config"
    oauth_enabled: bool = False
    oauth_provider_name: str = "openid"
    oauth_client_id: str = ""
    oauth_client_secret: str = ""
    oauth_scope: str = "openid profile email"
    oauth_redirect_uri: str = ""
    oauth_well_known_url: str = ""
    oauth_authorization_endpoint: str = ""
    oauth_token_endpoint: str = ""
    oauth_userinfo_endpoint: str = ""


def _load_config_file() -> dict[str, Any]:
    config_path = Path(os.environ.get("GAMES_CONFIG", "config.json"))
    if not config_path.exists():
        return {}

    with config_path.open() as config_file:
        return json.load(config_file)


def _get_nested(data: dict[str, Any], path: tuple[str, ...], default: Any = None) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]

    return current


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default

    return value.lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    config = _load_config_file()
    oauth = _get_nested(config, ("oauth",), {})
    session = _get_nested(config, ("session",), {})

    return Settings(
        app_name=os.environ.get("GAMES_APP_NAME", config.get("app_name", Settings.app_name)),
        database_url=os.environ.get("DATABASE_URL", config.get("database_url", Settings.database_url)),
        data_dir=Path(os.environ.get("GAMES_DATA_DIR", config.get("data_dir", str(Settings.data_dir)))),
        session_cookie_name=os.environ.get("SESSION_COOKIE_NAME", session.get("cookie_name", Settings.session_cookie_name)),
        session_secret=os.environ.get("SESSION_SECRET", session.get("secret", Settings.session_secret)),
        oauth_enabled=_env_bool("OAUTH_ENABLED", bool(oauth.get("enabled", Settings.oauth_enabled))),
        oauth_provider_name=os.environ.get("OAUTH_PROVIDER_NAME", oauth.get("provider_name", Settings.oauth_provider_name)),
        oauth_client_id=os.environ.get("OAUTH_CLIENT_ID", oauth.get("client_id", Settings.oauth_client_id)),
        oauth_client_secret=os.environ.get("OAUTH_CLIENT_SECRET", oauth.get("client_secret", Settings.oauth_client_secret)),
        oauth_scope=os.environ.get("OAUTH_SCOPE", oauth.get("scope", Settings.oauth_scope)),
        oauth_redirect_uri=os.environ.get("OAUTH_REDIRECT_URI", oauth.get("redirect_uri", Settings.oauth_redirect_uri)),
        oauth_well_known_url=os.environ.get("OAUTH_WELL_KNOWN_URL", oauth.get("well_known_url", Settings.oauth_well_known_url)),
        oauth_authorization_endpoint=os.environ.get(
            "OAUTH_AUTHORIZATION_ENDPOINT",
            oauth.get("authorization_endpoint", Settings.oauth_authorization_endpoint),
        ),
        oauth_token_endpoint=os.environ.get("OAUTH_TOKEN_ENDPOINT", oauth.get("token_endpoint", Settings.oauth_token_endpoint)),
        oauth_userinfo_endpoint=os.environ.get("OAUTH_USERINFO_ENDPOINT", oauth.get("userinfo_endpoint", Settings.oauth_userinfo_endpoint)),
    )


settings = load_settings()
