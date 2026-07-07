from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    root: Path
    templates_dir: Path
    static_dir: Path


class PathManager:
    def __init__(self) -> None:
        root = Path(__file__).resolve().parent.parent

        self.paths = AppPaths(
            root=root,
            templates_dir=root / "templates",
            static_dir=root / "static",
        )


path_manager = PathManager()