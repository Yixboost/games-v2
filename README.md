# games-v2

Open-source rewrite of Yixboost Games

## App structure

- `main.py` is the thin FastAPI entrypoint.
- `core/` owns the application factory, settings, database, cache, shared routes, template hooks, registries, error handlers, and plugin loader.
- `plugins/` contains built-in and future plugins. Plugin templates live inside each plugin at `plugins/<plugin>/templates/<plugin>/`.
- `plugins/game_loader/` is the built-in plugin that registers the homepage, game detail route, and `/api/v1/games`.
- `plugins/search/` registers `/search` and injects a navbar search form through the `navbar_actions` hook.

Run locally with:

```bash
python3 -m uvicorn main:app --reload
```
