"""Domain models for handball match analytics."""

from pydantic import BaseModel


class PlayerStats(BaseModel):
    name: str
    goals: int
    assists: int
    saves: int
    turnovers: int
    minutes_played: int


class MatchEvent(BaseModel):
    minute: int
    event_type: str  # "goal", "save", "turnover", "timeout", "substitution"
    team: str
    player: str
    description: str


class Match(BaseModel):
    id: int
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    date: str
    venue: str
    status: str  # "completed", "live", "upcoming"
    events: list[MatchEvent] = []
    home_players: list[PlayerStats] = []
    away_players: list[PlayerStats] = []


class TeamOverview(BaseModel):
    name: str
    wins: int
    losses: int
    draws: int
    goals_scored: int
    goals_conceded: int


DEMO_MATCHES: list[Match] = [
    Match(
        id=1,
        home_team="THW Kiel",
        away_team="SG Flensburg-Handewitt",
        home_score=28,
        away_score=25,
        date="2026-03-20",
        venue="Wunderino Arena",
        status="completed",
        events=[
            MatchEvent(
                minute=3,
                event_type="goal",
                team="THW Kiel",
                player="Niklas Ekberg",
                description="Left wing shot from 7m",
            ),
            MatchEvent(
                minute=5,
                event_type="save",
                team="THW Kiel",
                player="Niklas Landin",
                description="Blocked fast break attempt",
            ),
            MatchEvent(
                minute=12,
                event_type="goal",
                team="SG Flensburg-Handewitt",
                player="Jim Gottfridsson",
                description="Breakthrough from center back",
            ),
            MatchEvent(
                minute=18,
                event_type="turnover",
                team="SG Flensburg-Handewitt",
                player="Lasse Svan",
                description="Bad pass intercepted",
            ),
            MatchEvent(
                minute=25,
                event_type="timeout",
                team="SG Flensburg-Handewitt",
                player="Coach",
                description="Team timeout called",
            ),
            MatchEvent(
                minute=30,
                event_type="goal",
                team="THW Kiel",
                player="Sander Sagosen",
                description="Spin shot from 9m",
            ),
        ],
        home_players=[
            PlayerStats(
                name="Sander Sagosen",
                goals=8,
                assists=4,
                saves=0,
                turnovers=2,
                minutes_played=55,
            ),
            PlayerStats(
                name="Niklas Ekberg",
                goals=6,
                assists=2,
                saves=0,
                turnovers=1,
                minutes_played=48,
            ),
            PlayerStats(
                name="Niklas Landin",
                goals=0,
                assists=0,
                saves=14,
                turnovers=0,
                minutes_played=60,
            ),
        ],
        away_players=[
            PlayerStats(
                name="Jim Gottfridsson",
                goals=7,
                assists=5,
                saves=0,
                turnovers=3,
                minutes_played=58,
            ),
            PlayerStats(
                name="Lasse Svan",
                goals=5,
                assists=1,
                saves=0,
                turnovers=2,
                minutes_played=50,
            ),
            PlayerStats(
                name="Benjamin Buric",
                goals=0,
                assists=0,
                saves=11,
                turnovers=0,
                minutes_played=60,
            ),
        ],
    ),
    Match(
        id=2,
        home_team="SC Magdeburg",
        away_team="Füchse Berlin",
        home_score=31,
        away_score=29,
        date="2026-03-22",
        venue="GETEC Arena",
        status="completed",
        events=[
            MatchEvent(
                minute=2,
                event_type="goal",
                team="SC Magdeburg",
                player="Omar Ingi Magnusson",
                description="Fast break goal",
            ),
            MatchEvent(
                minute=7,
                event_type="goal",
                team="Füchse Berlin",
                player="Mathias Gidsel",
                description="Kempa trick from right side",
            ),
            MatchEvent(
                minute=15,
                event_type="save",
                team="SC Magdeburg",
                player="Sergey Hernandez",
                description="Penalty save",
            ),
        ],
        home_players=[
            PlayerStats(
                name="Omar Ingi Magnusson",
                goals=9,
                assists=3,
                saves=0,
                turnovers=1,
                minutes_played=58,
            ),
            PlayerStats(
                name="Gisli Kristjansson",
                goals=6,
                assists=6,
                saves=0,
                turnovers=2,
                minutes_played=55,
            ),
            PlayerStats(
                name="Sergey Hernandez",
                goals=0,
                assists=0,
                saves=16,
                turnovers=0,
                minutes_played=60,
            ),
        ],
        away_players=[
            PlayerStats(
                name="Mathias Gidsel",
                goals=10,
                assists=4,
                saves=0,
                turnovers=2,
                minutes_played=60,
            ),
            PlayerStats(
                name="Hans Lindberg",
                goals=7,
                assists=1,
                saves=0,
                turnovers=1,
                minutes_played=45,
            ),
            PlayerStats(
                name="Dejan Milosavljev",
                goals=0,
                assists=0,
                saves=12,
                turnovers=0,
                minutes_played=60,
            ),
        ],
    ),
    Match(
        id=3,
        home_team="Rhein-Neckar Löwen",
        away_team="MT Melsungen",
        home_score=0,
        away_score=0,
        date="2026-03-28",
        venue="SAP Arena",
        status="upcoming",
        events=[],
        home_players=[],
        away_players=[],
    ),
]

DEMO_TEAMS: list[TeamOverview] = [
    TeamOverview(
        name="THW Kiel",
        wins=18,
        losses=3,
        draws=1,
        goals_scored=612,
        goals_conceded=540,
    ),
    TeamOverview(
        name="SC Magdeburg",
        wins=17,
        losses=4,
        draws=1,
        goals_scored=635,
        goals_conceded=558,
    ),
    TeamOverview(
        name="SG Flensburg-Handewitt",
        wins=15,
        losses=5,
        draws=2,
        goals_scored=598,
        goals_conceded=555,
    ),
    TeamOverview(
        name="Füchse Berlin",
        wins=14,
        losses=6,
        draws=2,
        goals_scored=580,
        goals_conceded=548,
    ),
    TeamOverview(
        name="Rhein-Neckar Löwen",
        wins=12,
        losses=8,
        draws=2,
        goals_scored=556,
        goals_conceded=542,
    ),
    TeamOverview(
        name="MT Melsungen",
        wins=10,
        losses=10,
        draws=2,
        goals_scored=530,
        goals_conceded=535,
    ),
]
