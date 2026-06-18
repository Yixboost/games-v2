# Plugin Database Requirements

Plugins can require extra tables or columns. The core creates them when the plugin loads.

Declare requirements in `plugin.json`:

```json
{
  "name": "ratings",
  "version": "1.0.0",
  "depends": ["game_loader"],
  "database": {
    "tables": {
      "game_ratings": {
        "id": "INTEGER PRIMARY KEY",
        "game_id": "INTEGER NOT NULL",
        "user_id": "INTEGER NOT NULL",
        "rating": "INTEGER NOT NULL"
      }
    },
    "columns": {
      "games": {
        "rating_count": "INTEGER NOT NULL DEFAULT 0"
      }
    }
  }
}
```

Plugins can also request schema from code:

```python
context.database.require_columns("games", {
    "play_count": "INTEGER NOT NULL DEFAULT 0"
})
```

Only simple SQLite schema creation is supported right now. Full migrations can be added later per plugin.
