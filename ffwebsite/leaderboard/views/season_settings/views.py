from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet

from leaderboard.models import SeasonSettings
from leaderboard.views.season_settings.serializers import SeasonSettingsSerializer

# Create your views here.

class SeasonSettingsViewSet(ModelViewSet):
    queryset = SeasonSettings.objects.all()
    serializer_class = SeasonSettingsSerializer