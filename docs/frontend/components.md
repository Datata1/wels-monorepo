# Frontend Components

The frontend uses Jinja2 macros as reusable UI components, similar to React's component model. All components live in `templates/components/macros.html`.

## Usage

Import components in any template:

```jinja
{% from "components/macros.html" import match_card, status_badge %}
```

## Available Components

### `page_header(title, subtitle)`

Page-level header with title and description text.

```jinja
{{ page_header("Dashboard", "Recent matches and upcoming fixtures.") }}
```

### `section_heading(text)`

Blue section subheading.

```jinja
{{ section_heading("Matches") }}
```

### `status_badge(status)`

Colored pill badge for match status. Accepts `"completed"`, `"live"`, or `"upcoming"`.

```jinja
{{ status_badge("live") }}
```

| Status | Style |
|--------|-------|
| `completed` | Green |
| `live` | Red, pulsing |
| `upcoming` | Gray |

### `match_card(match)`

Full match card with teams, score, status badge, and details button. Expects a match dict with `home_team`, `away_team`, `home_score`, `away_score`, `date`, `venue`, `status`, and `id`.

```jinja
{{ match_card(match) }}
```

### `event_icon(event_type)`

Colored circular icon for match events.

| Type | Icon | Color |
|------|------|-------|
| `goal` | ⚽ | Green |
| `save` | 🧤 | Blue |
| `turnover` | ⚠ | Yellow |
| `timeout` | ⏸ | Gray |
| other | 🔄 | Purple |

### `event_timeline_item(event)`

Full timeline row with minute, icon, player, team, and description.

```jinja
{% for event in match.events %}
    {{ event_timeline_item(event) }}
{% endfor %}
```

### `player_stats_table(players, team_name)`

Stats table with columns for Player, G (goals), A (assists), S (saves), TO (turnovers).

```jinja
{{ player_stats_table(match.home_players, match.home_team) }}
```

### `goal_diff(scored, conceded)`

Color-coded goal difference: green for positive, red for negative, gray for zero.

```jinja
{{ goal_diff(team.goals_scored, team.goals_conceded) }}
```
