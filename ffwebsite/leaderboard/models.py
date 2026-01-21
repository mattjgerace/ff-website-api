from django.db.models import Model
from django.db.models.fields import CharField,IntegerField, BooleanField, DecimalField
from django.db.models import JSONField, ForeignKey, CASCADE, OneToOneField, ManyToManyField
from django.contrib.postgres.fields import ArrayField

class TeamManagerAPP(Model):
    first_name = CharField()
    last_name = CharField()
    active = BooleanField()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class TeamManagerESPN(Model):
    team_manager = ForeignKey(TeamManagerAPP, on_delete=CASCADE)
    team_id = CharField(unique=True)

class TeamManagerSLEEPER(Model):
    team_manager = ForeignKey(TeamManagerAPP, on_delete=CASCADE)
    team_id = CharField(unique=True)

class Player(Model):
    first_name = CharField()
    last_name = CharField()
    position = CharField()

class PlayerSLEEPER(Model):
    player = ForeignKey(Player, on_delete=CASCADE)
    external_player_id = CharField(unique=True)

class PlayerESPN(Model):
    player = ForeignKey(Player, on_delete=CASCADE)
    external_player_id = CharField(unique=True)

class SeasonSettings(Model):
    season = IntegerField(unique=True) #Specifies the year in which the season took place
    platform = CharField() #Specifies which platform the season was played on
    playoff_week_start = IntegerField() 
    division_mapping = JSONField() #Specifies the division naming
    league_settings = JSONField() #Specifies the league's rules for the season
    scoring_settings = JSONField() #Specifies the league's scoring rules for the season
    roster_settings = ArrayField(CharField()) #Specifies the league's roster configuration for the season

    @property
    def platform_season_settings(self):
        match self.platform:
            case "sleeper":
                return self.seasonsettingssleeper_set.first()
            case "espn":
                return self.seasonsettingsespn_set.first()
            
class SeasonSettingsESPN(Model):
    season_settings = ForeignKey(SeasonSettings, on_delete=CASCADE)
    league_id = CharField()


class SeasonSettingsSLEEPER(Model):
    season_settings = ForeignKey(SeasonSettings, on_delete=CASCADE)
    league_id = CharField()
    draft_id = CharField()
    bracket_id = CharField()

class Draft(Model):
    season_settings = OneToOneField(SeasonSettings, on_delete=CASCADE)
    date = IntegerField(null=True)
    draft_type = CharField(null=True)
    draft_settings = JSONField(null=True) #can these be not null?
    order = JSONField(null=True) #might not need

class Playoff(Model):
    season_settings = OneToOneField(SeasonSettings, on_delete=CASCADE)
    playoff_teams = IntegerField()
    #reseed = BooleanField()

    #Adding these now for now
    #champion = ForeignKey(TeamManagerAPP, on_delete=CASCADE)
    #second = ForeignKey(TeamManagerAPP, on_delete=CASCADE)
    #third = ForeignKey(TeamManagerAPP, on_delete=CASCADE)
    #fourth = ForeignKey(TeamManagerAPP, on_delete=CASCADE)

class DraftPicks(Model):
    draft = ForeignKey(Draft, on_delete=CASCADE)
    team = ForeignKey(TeamManagerAPP, on_delete=CASCADE)
    player = ForeignKey(Player, on_delete=CASCADE)
    round_num = IntegerField()
    pick_num = IntegerField()

class WeeklyMatchups(Model):
    season_settings = ForeignKey(SeasonSettings, on_delete=CASCADE)
    week = IntegerField()
    team = ForeignKey(TeamManagerAPP, on_delete=CASCADE)
    opp = ForeignKey(TeamManagerAPP, on_delete=CASCADE, related_name='opponent') #opp team id--this could be repetitive ...
    score = DecimalField(max_digits=5, decimal_places=2, null=True)
    result = CharField()
    weekly_winner = BooleanField(default=False)
    playoff = BooleanField(default=False)
    
    #matchup = IntegerField() # ID representing the matchup
    #roster = ArrayField(CharField()) # Player id's #don't don't need
    #starters = ArrayField(CharField()) # Player id's #probably don't need

class ExhibitionWeeklyMatchups(Model):
    season_settings = ForeignKey(SeasonSettings, on_delete=CASCADE)
    week = IntegerField()
    team = ForeignKey(TeamManagerAPP, on_delete=CASCADE)
    opp = ForeignKey(TeamManagerAPP, null=True, on_delete=CASCADE, related_name='exhibition_opponent')
    score = DecimalField(max_digits=5, decimal_places=2, null=True)
    result = CharField()
    weekly_winner = BooleanField(default=False)
    playoff = BooleanField(default=False)

class PlayerPoints(Model):
    weeklymatchup = ForeignKey(WeeklyMatchups, null=True, on_delete=CASCADE)
    exhibtion = ForeignKey(ExhibitionWeeklyMatchups, default=None, null=True, on_delete=CASCADE)
    player = ForeignKey(Player, on_delete=CASCADE)
    points = DecimalField(max_digits=5, decimal_places=2)
    starter = BooleanField()
    week = IntegerField()
    season = IntegerField()
    nfl_team = CharField(null=True)
    injury_status = CharField(null=True)

class Leaderboard(Model):
    team = ForeignKey(TeamManagerAPP, on_delete=CASCADE)
    season_settings = ForeignKey(SeasonSettings, on_delete=CASCADE)
    # wins = IntegerField()
    # losses = IntegerField()
    # ties = IntegerField()
    standing = IntegerField(null=True)
    division = CharField(null=True)
    division_standing = IntegerField(null=True)
    seed = IntegerField(null=True)
    draft_pick = IntegerField(null=True)
    season_winner = BooleanField(default=False)
    division_winner = BooleanField(default=False)
    roster_id = CharField(default=None, null=True)