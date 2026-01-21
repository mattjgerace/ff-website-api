import json
import os
from leaderboard.models import PlayerESPN, SeasonSettingsESPN, TeamManagerESPN
from leaderboard.views.data.connection import BaseClient

from espn_api.football import League


class EspnClient(BaseClient):
    def _set_platform(self):
        self.platform = "espn"
        self.mongo_id = "espn_id"
    
    def _set_models(self):
        self.manager_model = TeamManagerESPN
        self.season_settings_model = SeasonSettingsESPN
        self.player_model = PlayerESPN

    def _set_draft_id(self, draft_id=None):
        pass

    def get_draft_api(self):
        pass 
    
    def get_draft_selections_api(self):
        pass
    
    def get_id_api(self):
        pass
    
    def get_league_id(self):
        return os.environ['ESPN_ID']

    def get_league_api(self):
        return League(league_id=os.environ['ESPN_ID'], year=int(self.season), espn_s2=os.environ['ESPN_S2'], swid=os.environ['ESPN_SWID'])
    
    def get_season_settings(self):
        LEAGUE = self.get_league_api()

        positions = ["QB", "RB", "WR", "TE", "QB/WR/TE", "RB/WR/TE", "RB/WR", "FLEX", "K", "D/ST", "P", "HC", "BE"]
        roster_settings = []
        position_slot_counts = LEAGUE.settings.position_slot_counts
        for position in positions:
            if position_slot_counts.get(position, None):
                if position == "BE":
                    roster_settings.extend(["BN"] * position_slot_counts[position])
                elif position == "RB/WR/TE":
                    roster_settings.extend(["FLEX"] * position_slot_counts[position])
                elif position == "D/ST":
                    roster_settings.extend(["DEF"] * position_slot_counts[position])
                else:
                    roster_settings.extend([position] * position_slot_counts[position])

        league_settings = LEAGUE.settings.__dict__  
        league_results = {
                "season": LEAGUE.year,
                "platform": self.platform,
                "league_settings": league_settings, #TODO --might need to fix
                "roster_settings": roster_settings,
                "scoring_settings": LEAGUE.settings.scoring_format,
                "playoff_week_start": LEAGUE.settings.reg_season_count+1,
                "division_mapping": LEAGUE.settings.division_map,
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
            team_info["team_id"] = team.owners[0]["id"]
            team_info["roster_id"] = team.team_id
            roster_results.append(team_info)
        return roster_results
    
    def get_draft(self):
        LEAGUE = self.get_league_api()
        draft_results = {
            "date": None,
            "draft_type": None,
            "draft_settings": None,
            "order": {},
        }
        for pick, selection in enumerate(LEAGUE.draft):
            if selection.round_num == 1:
                draft_results["order"][selection.team.owners[0]["id"]] = selection.round_pick
        return draft_results
    
    def get_draft_selections(self):
        LEAGUE = self.get_league_api()
        draft_selection_results = []
        for pick, selection in enumerate(LEAGUE.draft):
            player_info = LEAGUE.player_info(playerId=selection.playerId)
            delimiter = " "
            name = player_info.name.split(delimiter)
            draft_selection = selection.__dict__
            draft_selection["pick_no"] = pick+1
            draft_selection["round"] = selection.round_num
            draft_selection["picked_by"] = selection.team.owners[0]["id"]
            draft_selection["roster_id"] = selection.team.team_id
            draft_selection["player_id"] = int(draft_selection["playerId"])
            draft_selection["first_name"] = name[0]
            draft_selection["last_name"] = delimiter.join(name[1:])
            draft_selection["position"] = player_info.position
            draft_selection_results.append(draft_selection)
        return draft_selection_results