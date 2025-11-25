from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet

from leaderboard.models import Leaderboard, PlayerPoints, SeasonSettings, TeamOwnerAPP, WeeklyMatchups
from leaderboard.views.leaderboard.serializers import LeaderboardSerializer

from django.db import connection

from django.db.models import Prefetch, Sum, OuterRef, Subquery
from django.db.models import Sum, Max, Case, When, Count, F, Q, Value, BooleanField, CharField, IntegerField, DecimalField
from django.db.models.functions import Rank,DenseRank
from django.db.models.expressions import Window


# Create your views here.

class LeaderboardViewSet(ModelViewSet):

    # Define the base queryset
    queryset = Leaderboard.objects

    queryset = queryset.select_related('team', 'season_settings').prefetch_related(Prefetch('team__weeklymatchups_set', to_attr='weeklymatchups_list'), 
                                                                                   Prefetch('team__weeklymatchups__weeklywinner_set', to_attr='weeklywinner_list'))
    
    subquery_opp = WeeklyMatchups.objects.filter(week=OuterRef('week'), team=OuterRef('team__weeklymatchups__opp'), opp=OuterRef('team')).values('score')[:1]

    queryset = queryset.annotate(week=F('team__weeklymatchups__week'),
                                 season=F('season_settings__season'),
                                 team_score=F('team__weeklymatchups__score'),
                                 opp_score = Subquery(subquery_opp),
                                 outcome=Case(
                                    When(team_score__gt=F('opp_score'), then=Value('W')),
                                    When(team_score__lt=F('opp_score'), then=Value('L')),
                                    default=Value('T'),
                                    output_field=CharField(),
                                    ),
                                 pf=Sum('team_score'), 
                                 pa=Sum('opp_score'),
                                 wins=Count('outcome', filter=Case(When(outcome='W', then=True), default=False)),
                                 losses=Count('outcome', filter=Case(When(outcome='L', then=True), default=False)),
                                 ties=Count('outcome', filter=Case(When(outcome='T', then=True), default=False)),
                                 weeks_won=Count(F('team__weeklymatchups__weeklywinner'), filter=Case(When(team__weeklymatchups=F('team__weeklymatchups__weeklywinner__weeklymatchup'), then=True), default=False)),  
                                )
    
    # Order the queryset
    queryset = queryset.values("team", "team__first_name", "team__last_name", "season", "pf", "pa", "wins", "losses", "ties", "weeks_won")

    serializer_class = LeaderboardSerializer
