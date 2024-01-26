from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet
from ffwebsite.leaderboard.views.weekly_matchups.serializers import WeeklyMatchupsSerializer

from leaderboard.models import WeeklyMatchups
from leaderboard.views.season_settings.serializers import WeeklyMatchupsSerializer

# Create your views here.

class WeeklyMatchupsViewSet(ModelViewSet):
    queryset = WeeklyMatchups.objects.all()
    serializer_class = WeeklyMatchupsSerializer

