from leaderboard.views.data.connection import BaseClient

#from espn_api.football import League


class EspnClient(BaseClient):
    def _set_platform(self) -> str:
        return "espn"
    
    def _set_league_identifier(self) -> str:
        return 

    def set_season_settings(self):
       #LEAGUE = League(league_id=os.environ['ESPN_ID'], year=self.season, espn_s2=os.environ['ESPN_S2'], swid=os.environ['ESPN_SWID'])
       return