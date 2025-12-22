import json

#from rest_framework.fields import CharField, DateField, FloatField, IntegerField, ListField
from django.forms import FloatField
from rest_framework.serializers import ModelSerializer, ReadOnlyField, CharField, DecimalField, IntegerField, SerializerMethodField
from leaderboard.views.weekly_matchups.serializers import WeeklyMatchupsSerializer


from leaderboard.models import Leaderboard

from django.db import connection, reset_queries
from django.db.models import Sum

class LeaderboardSerializer(ModelSerializer):
    team_id = CharField(source='team__id')
    first_name = CharField(source='team__first_name')
    last_name = CharField(source='team__last_name')
    full_name = SerializerMethodField()
    division = CharField()
    division_standing = IntegerField()
    wins = IntegerField()
    losses = IntegerField()
    ties = IntegerField()
    pf = DecimalField(max_digits=8, decimal_places=2)
    pa = DecimalField(max_digits=8, decimal_places=2)
    seed = IntegerField()
    standing = IntegerField()
    weeks_won = IntegerField()
    draft_pick = IntegerField()
    test = SerializerMethodField()

    class Meta:
        model = Leaderboard
        fields = ['team_id', 'first_name', 'last_name', 'full_name', 'division', 'division_standing', 'wins', 'losses', 'ties', 'pf', 'pa', 'seed', 'weeks_won', 'standing', 'draft_pick', 'test']
    
    def get_full_name(self, obj):
        return f"{obj['team__first_name']} {obj['team__last_name']}"

    def get_test(self, obj):
        #print('Queries performed:', len(connection.queries))
        q = len(connection.queries)
        return q
    
class AllTimeLeaderboardSerializer(ModelSerializer):
    team_id = CharField(source='team__id')
    first_name = CharField(source='team__first_name')
    last_name = CharField(source='team__last_name')
    full_name = SerializerMethodField()
    avgseed = DecimalField(max_digits=3, decimal_places=1)
    avgstanding = DecimalField(max_digits=3, decimal_places=1)
    avgdraft_pick = DecimalField(max_digits=3, decimal_places=1)
    championships = IntegerField()
    seasons_won = IntegerField()
    divisions_won = IntegerField()
    weeks_won = IntegerField()

    class Meta:
        model = Leaderboard
        fields = [
                   'team_id',
                   'first_name',
                   'last_name', 
                   'full_name',
                   'avgseed', 
                   'avgstanding', 
                   'avgdraft_pick',
                   'championships',
                   'seasons_won',
                   'divisions_won',
                   'weeks_won',
                   ]
    
    def get_full_name(self, obj):
        return f"{obj['team__first_name']} {obj['team__last_name']}"
    