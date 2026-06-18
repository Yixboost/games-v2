# Plugins

A plugin lives in `plugins/<name>/` or `custom_plugins/<name>/`.

Minimum structure:

```text
plugins/example/
├── __init__.py
├── plugin.json
├── plugin.py
└── templates/
    └── example/
        └── page.html
```

`plugin.json`:

```json
{
  "name": "example",
  "version": "1.0.0",
  "description": "Example plugin",
  "depends": []
}
```

`plugin.py`:

```python
from fastapi import APIRouter


class Plugin:
    name = "example"

    def setup(self, app, context):
        router = APIRouter()
        app.include_router(router)
```

The `context` object exposes:

- `context.services`
- `context.events`
- `context.hooks`
- `context.permissions`
- `context.database`
- `context.auth`
