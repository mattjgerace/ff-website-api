import json

#from rest_framework.fields import CharField, DateField, FloatField, IntegerField, ListField
from rest_framework.serializers import ModelSerializer, ReadOnlyField, CharField, IntegerField, SerializerMethodField
from leaderboard.views.weekly_matchups.serializers import WeeklyMatchupsSerializer


from leaderboard.models import Leaderboard

from django.db import connection, reset_queries
from django.db.models import Sum

class LeaderboardSerializer(ModelSerializer):
    wins = IntegerField()
    losses = IntegerField()
    ties = IntegerField()
    pf = IntegerField()
    pa = IntegerField()
    weeks_won = IntegerField()
    test = SerializerMethodField()

    class Meta:
        model = Leaderboard
        fields = ['wins', 'losses', 'ties', 'pf', 'pa', 'weeks_won', 'test']
    
    def get_test(self, obj):
        print('Queries performed:', len(connection.queries))
        q = len(connection.queries)
        reset_queries()
        return q
    