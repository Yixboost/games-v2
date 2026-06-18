from datetime import datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader, pass_context

from core.config import settings
from core.hooks import hook_registry

templates = Jinja2Templates(directory=str(settings.templates_dir))
_active_theme = None


def register_template_dir(template_dir: Path | str) -> None:
    loader = FileSystemLoader(str(template_dir))
    current_loader = templates.env.loader

    if isinstance(current_loader, ChoiceLoader):
        current_loader.loaders.append(loader)
        return

    templates.env.loader = ChoiceLoader([current_loader, loader])


def set_template_dirs(template_dirs: list[Path | str]) -> None:
    templates.env.loader = ChoiceLoader(
        [FileSystemLoader(str(template_dir)) for template_dir in template_dirs]
    )


def set_active_theme(theme) -> None:
    global _active_theme
    _active_theme = theme
    templates.env.globals["current_theme"] = theme


def theme_asset(path: str) -> str:
    return f"/theme-assets/{path.lstrip('/')}"


def render_template(template_name: str, context: dict) -> str:
    template = templates.env.get_template(template_name)
    return template.render(**context)


@pass_context
def render_hook(jinja_context, hook_name: str) -> str:
    return hook_registry.render(hook_name, dict(jinja_context))


templates.env.globals["hook"] = render_hook
templates.env.globals["theme_asset"] = theme_asset
templates.env.globals["current_theme"] = _active_theme


def base_context(request=None, **extra):
    context = {
        "current_year": datetime.now().year,
        "app_name": settings.app_name,
        "current_theme": _active_theme,
        "current_user": getattr(request.state, "current_user", None) if request else None,
    }
    context.update(extra)
    return context
