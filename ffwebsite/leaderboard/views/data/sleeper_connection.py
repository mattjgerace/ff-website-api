import json
import os
from sleeper.api import LeagueAPIClient, DraftAPIClient, PlayerAPIClient
from sleeper.enum import Sport

from leaderboard.models import PlayerSLEEPER, SeasonSettingsSLEEPER, TeamManagerSLEEPER
from leaderboard.views.data.connection import BaseClient

class SleeperClient(BaseClient):

    def _set_platform(self):
        self.platform = "sleeper"
        self.sport = Sport.NFL

    def _set_models(self):
        self.manager_model = TeamManagerSLEEPER
        self.season_settings_model = SeasonSettingsSLEEPER
        self.player_model = PlayerSLEEPER
    
    def _set_draft_id(self, season_settings):
        draft_id = season_settings.platform_season_settings.draft_id
        if draft_id:
            self.draft_id = draft_id
    
    def get_league_id(self):
        return self.get_id_api()

    def get_id_api(self):
        league_data = {league.name: league.league_id for league in LeagueAPIClient.get_user_leagues_for_year(user_id=os.environ['SLEEPER_USER_ID'], sport=self.sport, year=self.season)
                    if league.name == "LCDS '19"}
        return league_data["LCDS '19"]
    
    def get_league_api(self):
        return LeagueAPIClient.get_league(league_id=self.league_id)
    
    def get_rosters_api(self):
        return LeagueAPIClient.get_rosters(league_id=self.league_id)
    
    def get_draft_api(self):
        return DraftAPIClient.get_draft(draft_id=self.draft_id)
    
    def get_draft_selections_api(self):
        return DraftAPIClient.get_player_draft_picks(draft_id=self.draft_id, sport=Sport.NFL)
    
    def get_matchups_api(self, season, week):
        return LeagueAPIClient.get_matchups_for_week(league_id=self.league_id, week=week)
    
    def get_players_api(self):
        #return PlayerAPIClient.get_all_players(sport=Sport.NFL)
        return None

    def get_season_settings(self):
        league_info = self.get_league_api()
        league_settings = league_info.settings.__dict__
        league_settings["playoff_round_type_enum"] = league_settings["playoff_round_type_enum"].value
        division_mapping = {}
        if league_info.metadata.division_1:
            division_mapping["1"] = league_info.metadata.division_1
        if league_info.metadata.division_2:
            division_mapping["2"] = league_info.metadata.division_2
        if league_info.metadata.division_3:
            division_mapping["3"] = league_info.metadata.division_3
        if league_info.metadata.division_4:
            division_mapping["4"] = league_info.metadata.division_4
        if league_info.metadata.division_5:
            division_mapping["5"] = league_info.metadata.division_5
        league_results = {
                "season": league_info.season,
                "platform": self.platform,
                "league_settings": league_settings,
                "division_mapping": division_mapping,
                "roster_settings": [position.name for position in league_info.roster_positions],
                "scoring_settings": league_info.scoring_settings.__dict__,
                "playoff_week_start": league_settings["playoff_week_start"],
        }
        platform_results = {
                "league_id": self.league_id,
                "draft_id": league_info.draft_id,
                "bracket_id": league_info.bracket_id
        }
        return league_results, platform_results
    
    def get_managers(self):
        roster_info = self.get_rosters_api()
        roster_results = [roster.__dict__ for roster in roster_info]
        user_key = json.loads(os.environ.get("SLEEPER_USER_KEY", "{}"))
        for roster in roster_results:
            name = user_key[str(roster["roster_id"])].split()
            roster["settings"] = roster["settings"].__dict__
            roster["first_name"] = name[0]
            roster["last_name"] = f"{name[1]} {name[2]}" if len(name) > 2 else name[1]
        return roster_results
    
    def get_draft(self):
        draft_info = self.get_draft_api()
        draft_results = {
            "date": draft_info.start_time/1000,
            "draft_type": draft_info.type.value,
            "draft_settings": draft_info.settings.__dict__,
            "order": draft_info.draft_order,
        }
        return draft_results
    
    def get_draft_selections(self):
        draft_selections = self.get_draft_selections_api()
        return [selection.__dict__ for selection in draft_selections]
    
    def get_matchups(self, season, week):
        week_matchups = self.get_matchups_api(season, week)
        return [matchup.__dict__ for matchup in week_matchups]