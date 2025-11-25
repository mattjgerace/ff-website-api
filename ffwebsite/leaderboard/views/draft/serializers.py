import json

from rest_framework.fields import CharField, DateField, FloatField, IntegerField, ListField
from rest_framework.serializers import ModelSerializer, ReadOnlyField

from leaderboard.models import Draft, DraftPicks, Player, TeamManagerAPP

class PlayerSerializer(ModelSerializer):
    class Meta:
        model = Player
        fields = "__all__"

class TeamManagerAPPSerializer(ModelSerializer): #might be a better way to this
    class Meta:
        model = TeamManagerAPP
        fields = "__all__"

class DraftPicksSerializer(ModelSerializer):
    player = PlayerSerializer()
    team = TeamManagerAPPSerializer()
    class Meta:
        model = DraftPicks
        fields = '__all__'

class DraftSerializer(ModelSerializer):
    draftpicks_set = DraftPicksSerializer(many=True, read_only=True)
    class Meta:
        model = Draft
        fields = '__all__'