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

    queryset = queryset.select_related('team', 'season_settings').prefetch_related(Prefetch('team__weeklymatchups_set', to_attr='weeklymatchups_list'), Prefetch('team__opponent', to_attr='oppweeklymatchups_list'))

    subquery_team = WeeklyMatchups.objects.filter(id=OuterRef('team__weeklymatchups__id')).annotate(
                                            team_points=Sum(
                                                Case(
                                                    When(playerpoints__starter=True,  then=F('playerpoints__points')),
                                                    default=Value(0), output_field=DecimalField()
                                                )
                                            ),
    ).values('team_points')[:1]

    subquery_opp = WeeklyMatchups.objects.filter(team=OuterRef('team__weeklymatchups__opp'), opp=OuterRef('team'), week=OuterRef('week')).annotate(
                                            opp_points=Sum(
                                                Case(
                                                    When(playerpoints__starter=True,  then=F('playerpoints__points')),
                                                    default=Value(0), output_field=DecimalField()
                                                )
                                            ),
    ).values('opp_points')[:1]


    queryset = queryset.annotate(team_score=Subquery(subquery_team),
                                 week=F('team__weeklymatchups__week'),
                                 season=F('season_settings__season'),
                                 opp_score = Subquery(subquery_opp),
                                 outcome=Case(
                                    When(team_score__gt=F('opp_score'), then=Value('W')),
                                    When(team_score__lt=F('opp_score'), then=Value('L')),
                                    default=Value('T'),
                                    output_field=CharField(),
                                    ),
                                )

    max_score_subquery = queryset.filter(week=OuterRef('week')).order_by('-team_score').values('team_score')[:1]

    queryset = queryset.annotate(
        pf=Sum('team_score'), 
        pa=Sum('opp_score'),
        wins=Count('outcome', filter=Case(When(outcome='W', then=True), default=False)),
        losses=Count('outcome', filter=Case(When(outcome='L', then=True), default=False)),
        ties=Count('outcome', filter=Case(When(outcome='T', then=True), default=False)),
        has_highest_score=Case(
        When(team_score=Subquery(max_score_subquery), then=Value(True)),
        default=Value(False),
        output_field=BooleanField()
        ),
        weeks_won=Count('has_highest_score', filter=Case(When(has_highest_score=True, then=True), default=False)),
    )
    
    # Order the queryset
    queryset = queryset.values("team", "team__first_name", "team__last_name", "season", "pf", "pa", "wins", "losses", "ties", "weeks_won")

    serializer_class = LeaderboardSerializer