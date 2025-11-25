import json

from rest_framework.fields import CharField, DecimalField, DateField, FloatField, IntegerField, ListField
from rest_framework.serializers import ModelSerializer, ReadOnlyField, SerializerMethodField, BooleanField

from leaderboard.models import WeeklyMatchups, TeamManagerAPP

class TeamManagerAPPSerializer(ModelSerializer):
    
    class Meta:
        model = TeamManagerAPP
        fields = '__all__'

class WeeklyMatchupsSerializer(ModelSerializer):
    #team = TeamManagerAPPSerializer()
    team_id = CharField(source='team__id')
    first_name = CharField(source='team__first_name')
    last_name = CharField(source='team__last_name')
    season = IntegerField()
    week = IntegerField()
    score = DecimalField(max_digits=5, decimal_places=2)
    opp_score = DecimalField(max_digits=5, decimal_places=2)
    wins = IntegerField()
    losses = IntegerField()
    ties = IntegerField()
    playoff = BooleanField()
    #weeks_won = IntegerField()

    class Meta:
        model = WeeklyMatchups
        fields = [
                    "team_id",
                    "first_name",
                    "last_name",
                    "season",
                    "week",
                    "score",
                    "opp_score",
                    "wins",
                    "losses",
                    "ties",
                    "playoff",
                ]
        
class AllTimeSerializer(ModelSerializer):
     #team = TeamManagerAPPSerializer()
    team_id = CharField(source='team__id')
    first_name = CharField(source='team__first_name')
    last_name = CharField(source='team__last_name')
    season = IntegerField()
    score = DecimalField(max_digits=5, decimal_places=2)
    opp_score = DecimalField(max_digits=5, decimal_places=2)
    wins = IntegerField()
    losses = IntegerField()
    ties = IntegerField()
    #weeks_won = IntegerField()

    class Meta:
        model = WeeklyMatchups
        fields = [
                    "team_id", 
                    "first_name",
                    "last_name",
                    "season",
                    "score",
                    "opp_score",
                    "wins",
                    "losses",
                    "ties",
                ]
        
class PointsSerializer(ModelSerializer):
    #team = TeamManagerAPPSerializer()
    first_name = CharField(source='team__first_name')
    last_name = CharField(source='team__last_name')
    full_name = SerializerMethodField()
    opp_first_name = CharField(source='opp__first_name')
    opp_last_name = CharField(source='opp__last_name')
    opp_full_name = SerializerMethodField()
    pf = DecimalField(max_digits=8, decimal_places=2)
    week = IntegerField()
    season = IntegerField(source='season_settings__season')
    #weeks_won = IntegerField()

    class Meta:
        model = WeeklyMatchups
        fields = [
                    "first_name",
                    "last_name",
                    "full_name",
                    "opp_first_name",
                    "opp_last_name",
                    "opp_full_name",
                    "pf",
                    "week",
                    "season",
                ]
        
    def get_full_name(self, obj):
        return f"{obj['team__first_name']} {obj['team__last_name']}"
    
    def get_opp_full_name(self, obj):
        return f"{obj['opp__first_name']} {obj['opp__last_name']}"
    

class RecordsSerializer(ModelSerializer):
    #team = TeamManagerAPPSerializer()
    first_name = CharField(source='team__first_name')
    last_name = CharField(source='team__last_name')
    full_name = SerializerMethodField()
    pf = DecimalField(max_digits=8, decimal_places=2)
    season = IntegerField(source='season_settings__season')
    #weeks_won = IntegerField()

    class Meta:
        model = WeeklyMatchups
        fields = [
                    "first_name",
                    "last_name",
                    "full_name",
                    "pf",
                    "season",
                ]
        
    def get_full_name(self, obj):
        return f"{obj['team__first_name']} {obj['team__last_name']}"
    
    def get_opp_full_name(self, obj):
        return f"{obj['opp__first_name']} {obj['opp__last_name']}"