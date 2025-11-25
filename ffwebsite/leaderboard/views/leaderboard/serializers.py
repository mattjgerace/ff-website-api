import json

#from rest_framework.fields import CharField, DateField, FloatField, IntegerField, ListField
from rest_framework.serializers import ModelSerializer, ReadOnlyField, CharField, DecimalField, IntegerField, SerializerMethodField
from leaderboard.views.weekly_matchups.serializers import WeeklyMatchupsSerializer


from leaderboard.models import Leaderboard

from django.db import connection, reset_queries
from django.db.models import Sum

class LeaderboardSerializer(ModelSerializer):
    first_name = CharField(source='team__first_name')
    last_name = CharField(source='team__last_name')
    wins = IntegerField()
    losses = IntegerField()
    ties = IntegerField()
    pf = DecimalField(max_digits=8, decimal_places=2)
    pa = DecimalField(max_digits=8, decimal_places=2)
    weeks_won = IntegerField()
    test = SerializerMethodField()

    class Meta:
        model = Leaderboard
        fields = ['first_name', 'last_name', 'wins', 'losses', 'ties', 'pf', 'pa', 'weeks_won', 'test']
    
    def get_test(self, obj):
        print('Queries performed:', len(connection.queries))
        q = len(connection.queries)
        reset_queries()
        return q
    