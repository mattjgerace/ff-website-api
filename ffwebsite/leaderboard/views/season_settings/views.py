from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet

from leaderboard.tasks import HasAPIToken
from leaderboard.models import SeasonSettings
from leaderboard.views.season_settings.serializers import SeasonSettingsSerializer
from django_filters.rest_framework import DjangoFilterBackend

# Create your views here.

class SeasonSettingsViewSet(ModelViewSet):
    permission_classes = [HasAPIToken]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['season']
    queryset = SeasonSettings.objects.all()
    serializer_class = SeasonSettingsSerializer