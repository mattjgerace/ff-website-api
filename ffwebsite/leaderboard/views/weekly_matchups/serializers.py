import json

from rest_framework.fields import CharField, DateField, FloatField, IntegerField, ListField
from rest_framework.serializers import ModelSerializer, ReadOnlyField

from leaderboard.models import WeeklyMatchups

class WeeklyMatchupsSerializer(ModelSerializer):
    
    class Meta:
        model = WeeklyMatchups
        fields = '__all__'