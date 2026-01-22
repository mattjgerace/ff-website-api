import json
import os
from django.conf import settings


def create_mock_league_id_return(league_id=None):
    return league_id if league_id else "1"

def create_mock_season_settings_return(platform, season, league_id):
    league_results = {
            "season": season,
            "platform": platform,
            "league_settings": {'divisions': 2},
            "division_mapping": {1: "Blue", 2: "Red"},
            "roster_settings": [],
            "scoring_settings": {},
            "playoff_week_start": 15,
    }
    platform_results = {}
    platform_results["league_id"] = league_id
    if platform == "sleeper":
        platform_results["draft_id"] = "1"
        platform_results["bracket_id"] = "1"
    return league_results, platform_results

def create_mock_rosters_return():
    roster_results = []
    for i in range(1, 13):
        roster_results.append({
            "roster_id": i,
            "team_id": i,
            "first_name": "test"+str(i),
            "last_name": "test"+str(i),
            "settings": {"division": i%2}
        })
    return roster_results

def create_mock_draft_return():
    draft_results = {
            "date": 1,
            "draft_type": None,
            "draft_settings": None,
            "order": {str(i): i for i in range(1, 13)},
    }
    return draft_results

def create_mock_draft_selections_return():
    draft_selection_results = []
    for i in range(1, 13):
        draft_selection_results.append({
            "roster_id": i,
            "player_id": str(662+i),
            "round": i,
            "pick_no": i
        })
    return draft_selection_results

def create_mock_matchups_return():
    week_matchups_results = []
    for i in range(1, 13):
        week_matchups_results.append({
            "matchup_id": abs(6-i) if abs(6-i) != 0 else 6,
            "roster_id": i,
            "players_points": {f"{i}0{j}": 10.00 for j in range(0, 10)},
            "starters": {f"{i}0{j}": True for j in range(0, 10)},
        })
    return week_matchups_results

def create_mock_players_api_return():
    with open(os.path.join(settings.BASE_DIR, "leaderboard", "tests", "sample.json")) as json_file:
            players = json.load(json_file)
    return players