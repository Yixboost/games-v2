import json
from dataclasses import dataclass
from pathlib import Path

from core.config import settings


@dataclass(frozen=True)
class Theme:
    name: str
    version: str
    path: Path
    templates_dir: Path
    assets_dir: Path


class ThemeManager:
    def find_theme(self, theme_name: str | None = None) -> Theme:
        name = theme_name or settings.active_theme

        for base_dir in (settings.custom_themes_dir, settings.themes_dir):
            theme_dir = base_dir / name
            manifest_path = theme_dir / "theme.json"

            if manifest_path.exists():
                with manifest_path.open() as manifest_file:
                    manifest = json.load(manifest_file)

                return Theme(
                    name=manifest["name"],
                    version=manifest["version"],
                    path=theme_dir,
                    templates_dir=theme_dir / "templates",
                    assets_dir=theme_dir / "assets",
                )

        raise RuntimeError(f"Theme '{name}' was not found.")


theme_manager = ThemeManager()
