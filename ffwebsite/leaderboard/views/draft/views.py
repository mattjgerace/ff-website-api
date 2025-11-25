from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet

from leaderboard.tasks import HasAPIToken
from leaderboard.models import Draft, DraftPicks
from leaderboard.views.draft.serializers import DraftSerializer
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend

# Create your views here.

class DraftViewSet(ModelViewSet):
    permission_classes = [HasAPIToken]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['season_settings__season']
    queryset = Draft.objects.all().prefetch_related(Prefetch('draftpicks_set', queryset=DraftPicks.objects.order_by('pick_num'))).prefetch_related('draftpicks_set__player', 'draftpicks_set__team')
    serializer_class = DraftSerializer