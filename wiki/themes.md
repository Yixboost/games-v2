# Themes

Themes control page structure.

The default theme lives in:

```text
themes/default/
├── theme.json
├── templates/
│   ├── layouts/
│   │   └── base.html
│   └── partials/
│       ├── navbar.html
│       └── footer.html
└── assets/
    ├── css/
    │   └── theme.css
    └── images/
```

Custom themes live in `custom_themes/<name>/`.

Set the active theme in `config.json`:

```json
{
  "active_theme": "default"
}
```

Feature templates should extend the theme layout:

```jinja2
{% extends "layouts/base.html" %}

{% block content %}
  <h1>Hello</h1>
{% endblock %}
```

Because theme template directories are loaded before plugin templates, a theme can override plugin templates by providing the same template path.

Theme assets are served from `/theme-assets`. In templates, prefer the helper:

```jinja2
<img src="{{ theme_asset('images/logo.png') }}" alt="">
```

CSS files can reference sibling theme assets with relative URLs:

```css
.hero {
  background-image: url("../images/hero.jpg");
}
```
