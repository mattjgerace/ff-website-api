import json

from rest_framework.fields import CharField, DateField, FloatField, IntegerField, ListField
from rest_framework.serializers import ModelSerializer, ReadOnlyField, HyperlinkedRelatedField

from leaderboard.models import SeasonSettings

class SeasonSettingsSerializer(ModelSerializer):
    draft = HyperlinkedRelatedField(
        many=False,
        read_only=True,
        view_name='draft-detail'
    )
    
    class Meta:
        model = SeasonSettings
        fields = '__all__'
