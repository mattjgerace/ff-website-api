import json

from rest_framework.fields import CharField, DateField, FloatField, IntegerField, ListField
from rest_framework.serializers import ModelSerializer, ReadOnlyField

from leaderboard.models import SeasonSettings

class SeasonSettingsSerializer(ModelSerializer):
    
    class Meta:
        model = SeasonSettings
        fields = '__all__'
