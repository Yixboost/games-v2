# Auth And Permissions

Core owns login, sessions, users, roles, and permission checks.

Plugins can read user info through `context.auth`:

```python
user = context.auth.current_user(request)
is_logged_in = context.auth.is_logged_in(request)
is_admin = context.auth.has_role(request, "admin")
can_view = context.auth.has_permission(request, "profile.view_own")
```

Templates receive `current_user` automatically:

```jinja2
{% if current_user %}
  {{ current_user.username or current_user.name }}
{% endif %}
```

Users are stored in the `users` table. OAuth login fills fields like username, email, provider, subject, picture URL, and role.
