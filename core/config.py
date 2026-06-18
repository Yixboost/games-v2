from dataclasses import dataclass, field
from pathlib import Path


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
    )
    external_plugin_packages: tuple[str, ...] = field(default_factory=tuple)


settings = Settings()
