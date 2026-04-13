# Frontend Components

The frontend uses Jinja2 macros as reusable UI components. All components live in `templates/components/macros.html`.

## Usage

Import components in any template:

```jinja
{% from "components/macros.html" import page_header, section_heading %}
```

## Available Components

### `page_header(title, subtitle)`

Page-level header with title and description text.

```jinja
{{ page_header("Dashboard", "Welcome to WELS.") }}
```

### `section_heading(text)`

Blue section subheading.

```jinja
{{ section_heading("Matches") }}
```
