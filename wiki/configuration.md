# Configuration

Copy `config.example.json` to `config.json`.

`config.json` is ignored by git because it can contain OAuth secrets.

Useful fields:

```json
{
  "active_theme": "default",
  "custom_plugins_dir": "custom_plugins",
  "custom_themes_dir": "custom_themes",
  "session": {
    "secret": "replace-this"
  },
  "oauth": {
    "enabled": true,
    "well_known_url": "https://provider.example/.well-known/openid-configuration"
  }
}
```

Environment variables can override the same values, such as `GAMES_THEME`, `SESSION_SECRET`, `OAUTH_CLIENT_ID`, and `OAUTH_CLIENT_SECRET`.
