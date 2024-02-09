from django.db.models import Model
from django.db.models.fields import CharField,IntegerField, BooleanField, DecimalField
from django.db.models import JSONField, ForeignKey, CASCADE, Sum
from django.contrib.postgres.fields import ArrayField
from django_cryptography.fields import encrypt

from django.db import connection, reset_queries #delete later

class TeamOwnerAPP(Model):
    first_name = CharField(max_length=30)
    last_name = CharField(max_length=30)
    active = BooleanField()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class TeamOwnerESPN(Model):
    team_owner = ForeignKey(TeamOwnerAPP, on_delete=CASCADE)
    espn_team_id = IntegerField()

class TeamOwnerSLEEPER(Model):
    team_owner = ForeignKey(TeamOwnerAPP, on_delete=CASCADE)
    sleeper_team_id = encrypt(CharField())
    sleeper_roster_id = IntegerField()

#need to figure out how to keep track of team player is on
class Player(Model):
    first_name = CharField(max_length=30) #Player's First Name
    last_name = CharField(max_length=30) #Player's Last Name
    position = CharField(max_length=5) #Player's Position
    sleeper_player_id = CharField(null=True) #Sleeper ID
    espn_player_id = CharField(null=True) #ESPN ID

class Draft(Model): #Should this be results based mixin?
    date = IntegerField(null=True)
    draft_type = CharField(null=True)
    draft_settings = JSONField(null=True) #can these be not null?
    order = JSONField(null=True) #probably don't need

class DraftPicks(Model):
    draft = ForeignKey(Draft, on_delete=CASCADE) # Draft id
    team = ForeignKey(TeamOwnerAPP, on_delete=CASCADE)
    player = ForeignKey(Player, on_delete=CASCADE) # Player id
    round_num = IntegerField()
    pick_num = IntegerField()

class SeasonSettings(Model):
    season = IntegerField() #Specifies the year in which the season took place
    platform = CharField() #Specifies which platform the season was played on 
    league_settings = JSONField() #Specifies the league's rules for the season
    scoring_settings = JSONField() #Specifies the league's scoring rules for the season
    roster_settings = ArrayField(CharField()) #Specifies the league's roster configuration for the season
    draft = ForeignKey(Draft, on_delete=CASCADE, null=True) # Draft id

class SeasonSettingsSLEEPER(Model):
    season_settings = ForeignKey(SeasonSettings, on_delete=CASCADE)
    sleeper_league_id = encrypt(CharField())
    sleeper_draft_id = encrypt(CharField())
    sleeper_bracket_id = encrypt(CharField())

class WeeklyMatchups(Model):
    season_settings = ForeignKey(SeasonSettings, on_delete=CASCADE) # Season the game took place
    week = IntegerField() # Week the game took place
    team = ForeignKey(TeamOwnerAPP, on_delete=CASCADE) # team id
    opp = ForeignKey(TeamOwnerAPP, on_delete=CASCADE, related_name='opponent') # opp team id #this could be repetitive ...
    score = DecimalField(max_digits=5, decimal_places=2, null=True)
    #matchup = IntegerField() # ID representing the matchup
    #roster = ArrayField(CharField()) # Player id's #don't don't need
    #starters = ArrayField(CharField()) # Player id's#probably don't need

class WeeklyWinner(Model):
    weeklymatchup = ForeignKey(WeeklyMatchups, on_delete=CASCADE)

class PlayerPoints(Model):
    weeklymatchup = ForeignKey(WeeklyMatchups, on_delete=CASCADE) # Game information
    player = ForeignKey(Player, on_delete=CASCADE) # Player id
    points = DecimalField(max_digits=5, decimal_places=2) #Player Points
    starter = BooleanField() #Determines if Player Started

class Leaderboard(Model):
    team = ForeignKey(TeamOwnerAPP, on_delete=CASCADE) # Team id
    season_settings = ForeignKey(SeasonSettings, on_delete=CASCADE)

class YearlyWinner(Model):
    leaderboard = ForeignKey(Leaderboard, on_delete=CASCADE)
