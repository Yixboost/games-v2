from datetime import datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader, pass_context

from core.config import settings
from core.hooks import hook_registry

templates = Jinja2Templates(directory=str(settings.templates_dir))


def register_template_dir(template_dir: Path | str) -> None:
    loader = FileSystemLoader(str(template_dir))
    current_loader = templates.env.loader

    if isinstance(current_loader, ChoiceLoader):
        current_loader.loaders.append(loader)
        return

    templates.env.loader = ChoiceLoader([current_loader, loader])


def render_template(template_name: str, context: dict) -> str:
    template = templates.env.get_template(template_name)
    return template.render(**context)


@pass_context
def render_hook(jinja_context, hook_name: str) -> str:
    return hook_registry.render(hook_name, dict(jinja_context))


templates.env.globals["hook"] = render_hook


def base_context(request=None, **extra):
    context = {
        "current_year": datetime.now().year,
        "app_name": settings.app_name,
        "current_user": getattr(request.state, "current_user", None) if request else None,
    }
    context.update(extra)
    return context
