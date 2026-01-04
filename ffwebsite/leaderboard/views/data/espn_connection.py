import json
import os
from leaderboard.models import PlayerESPN, SeasonSettingsESPN, TeamManagerESPN
from leaderboard.views.data.connection import BaseClient

from espn_api.football import League


class EspnClient(BaseClient):
    def _set_platform(self):
        self.platform = "espn"
    
    def _set_models(self):
        self.manager_model = TeamManagerESPN
        self.season_settings_model = SeasonSettingsESPN
        self.player_model = PlayerESPN
    
    def get_league_id(self):
        return os.environ['ESPN_ID']

    def get_league_api(self):
        return League(league_id=os.environ['ESPN_ID'], year=self.season, espn_s2=os.environ['ESPN_S2'], swid=os.environ['ESPN_SWID'])
    
    def get_season_settings(self):
        LEAGUE = self.get_league_api()
        week_1_boxscore = LEAGUE.box_scores(1)[0]
        league_settings = LEAGUE.settings.__dict__  
        league_results = {
                "season": LEAGUE.year,
                "platform": self.platform,
                "league_settings": league_settings, #TODO --might need to fix
                "roster_settings": [player.slot_position if player.slot_position!='RB/WR/TE' else 'FLEX' for player in week_1_boxscore.home_lineup],
                "scoring_settings": LEAGUE.settings.scoring_format,
                "playoff_week_start": LEAGUE.settings.reg_season_count+1
        }
        platform_results = {
                "league_id": self.league_id,
        }
        return league_results, platform_results
    
    def get_managers(self):
        roster_results = []
        LEAGUE = self.get_league_api()
        user_first_key = json.loads(os.environ.get("ESPN_USER_FIRST_KEY", "{}"))
        user_last_key = json.loads(os.environ.get("ESPN_USER_LAST_KEY", "{}"))
        for team in LEAGUE.teams:
            team_info = {}
            first_name = team.owners[0]["firstName"].capitalize()
            last_name = team.owners[0]["lastName"].title()
            if first_name in user_first_key.keys():
                first_name = user_first_key[first_name]
            if last_name in user_last_key.keys():
                last_name = user_last_key[last_name]
            team_info["first_name"] = first_name
            team_info["last_name"] = last_name
            team_info["roster_id"] = team.team_id
            roster_results.append(team_info)
        return roster_results

    def set_season_settings(self):
       #LEAGUE = League(league_id=os.environ['ESPN_ID'], year=self.season, espn_s2=os.environ['ESPN_S2'], swid=os.environ['ESPN_SWID'])
       return