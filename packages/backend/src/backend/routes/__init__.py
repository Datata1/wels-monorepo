from fastapi import APIRouter, HTTPException

from backend.models import DEMO_MATCHES, DEMO_TEAMS, Match, MatchEvent, TeamOverview

router = APIRouter(prefix="/api/v1", tags=["api"])


@router.get("/matches", response_model=list[Match])
async def list_matches():
    """List all recorded handball matches."""
    return DEMO_MATCHES


@router.get("/matches/{match_id}", response_model=Match)
async def get_match(match_id: int):
    """Get full details for a specific match."""
    for match in DEMO_MATCHES:
        if match.id == match_id:
            return match
    raise HTTPException(status_code=404, detail="Match not found")


@router.get("/matches/{match_id}/events", response_model=list[MatchEvent])
async def get_match_events(match_id: int):
    """Get the event timeline for a match."""
    for match in DEMO_MATCHES:
        if match.id == match_id:
            return match.events
    raise HTTPException(status_code=404, detail="Match not found")


@router.get("/teams", response_model=list[TeamOverview])
async def list_teams():
    """List all teams with their standings overview."""
    return DEMO_TEAMS
