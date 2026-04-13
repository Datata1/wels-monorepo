Add a new Jinja2 macro component to the WELS frontend. What to create: $ARGUMENTS

Read these files before writing anything:
1. `packages/frontend/src/frontend/templates/components/macros.html` — existing macros
2. `packages/frontend/src/frontend/static/css/style.css` — design tokens

## What to produce

1. **The macro** — add to `macros.html` following existing style:
   - Accept only the parameters this component genuinely needs
   - Use existing CSS design tokens via the token names (e.g. `var(--color-wels-accent)`) — do not hardcode hex values
   - Do not invent new CSS classes without adding them to style.css

2. **CSS additions** (if needed) — append to `style.css` using the token variables already defined in `:root`

3. **Usage example** — show how to import and call the macro in a template:
   ```jinja
   {% from "components/macros.html" import <macro_name> %}
   {{ <macro_name>(param="value") }}
   ```

Keep the macro simple. No JavaScript. No inline styles. HTMX attributes are fine if interactivity is part of the request.
