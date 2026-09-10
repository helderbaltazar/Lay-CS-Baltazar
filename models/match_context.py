from typing import TypedDict, Optional

class MatchContext(TypedDict):
    fixture_id: int
    home_team: str
    away_team: str
    match_odd: Optional[float]
    btts_odd: Optional[float]
    h2h_home: Optional[float]
    h2h_away: Optional[float]
    must_win: Optional[bool]
    odds_source: Optional[str]
