# games-v2

Open-source rewrite of Yixboost Games

## App structure

- `main.py` is the thin FastAPI entrypoint.
- `core/` owns the application factory, settings, database, cache, shared routes, template hooks, registries, error handlers, and plugin loader.
- `plugins/` contains built-in and future plugins. Plugin templates live inside each plugin at `plugins/<plugin>/templates/<plugin>/`.
- `plugins/game_loader/` is the built-in plugin that registers the homepage, game detail route, and `/api/v1/games`.
- `plugins/search/` registers `/search` and injects a navbar search form through the `navbar_actions` hook.
- `custom_plugins/` and `custom_themes/` are reserved for local extensions.
- `themes/default/` provides the default page structure through `layouts/base.html`.
- `wiki/` contains short guides for config, plugins, auth, database requirements, and themes.

Run locally with:

```bash
python3 -m uvicorn main:app --reload
```

## OAuth login

Copy `config.example.json` to `config.json`, fill in the OAuth client details, and set the provider's redirect URI to:

```text
http://127.0.0.1:8000/auth/callback
```

The core supports OpenID Connect discovery through `oauth.well_known_url`. Users are created or updated in the `users` table after login.
