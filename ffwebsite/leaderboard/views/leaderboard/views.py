from django.http import JsonResponse
from django.shortcuts import render

from rest_framework.viewsets import ModelViewSet

from leaderboard.tasks import HasAPIToken
from leaderboard.models import Leaderboard, PlayerPoints, SeasonSettings, TeamManagerAPP, WeeklyMatchups
from leaderboard.views.leaderboard.serializers import AllTimeLeaderboardSerializer, LeaderboardSerializer

from django.db import connection

from django.db.models import Prefetch, Sum, OuterRef, Subquery
from django.db.models import Sum, Max, Case, When, Count, F, Avg, Q, Value, BooleanField, CharField, IntegerField, DecimalField
from django.db.models.functions import Rank,DenseRank
from django.db.models.expressions import Window
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action


class LeaderboardViewSet(ModelViewSet):
    permission_classes = [HasAPIToken]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['season_settings__season']
    queryset = Leaderboard.objects

    def get_queryset(self):
        queryset = super().get_queryset()
        season = self.request.query_params.get('season_settings__season', None)
        playoff = self.request.query_params.get('playoff', None)
        if season is not None:
            queryset = queryset.filter(season_settings__season=season)
        if playoff is not None:
            queryset = queryset.filter(seed__lte=6)

        queryset = queryset.select_related('team', 'season_settings').prefetch_related(Prefetch('team__weeklymatchups_set', to_attr='weeklymatchups_list'))
        
        subquery_team = WeeklyMatchups.objects.filter(week=OuterRef('week'), season_settings__season=OuterRef('season'), team=OuterRef('team'), opp=OuterRef('team__weeklymatchups__opp')).values('score')[:1]
        subquery_opp = WeeklyMatchups.objects.filter(week=OuterRef('week'), season_settings__season=OuterRef('season'), team=OuterRef('team__weeklymatchups__opp'), opp=OuterRef('team')).values('score')[:1]
        subquery_result = WeeklyMatchups.objects.filter(week=OuterRef('week'), season_settings__season=OuterRef('season'), team=OuterRef('team'), opp=OuterRef('team__weeklymatchups__opp')).values('result')[:1]
        subquery_ww = WeeklyMatchups.objects.filter(team=OuterRef('team'), season_settings__season=OuterRef('season')).values('team').annotate(
                      weeks_won=Count(F('weekly_winner'), filter=Case(When(weekly_winner=True, then=True), default=False))).values('weeks_won')[:1]
        
        #subquery_ww = WeeklyMatchups.objects.filter(week=OuterRef('week'), season_settings__season=OuterRef('season'), team=OuterRef('team'), opp=OuterRef('team__weeklymatchups__opp')).values('weekly_winner')[:1]
        
        # subquery_sw = WeeklyMatchups.objects.filter(season_settings__season=OuterRef('season')).values('team').annotate(
        #     pf=Sum('score'),
        #     max_pf=Max(F('pf')),
        #     seasons_won=Count(F('pf'), filter=Case(When(pf=F('max_pf'), then=True), default=False))
        # ).values('seasons_won').order_by('seasons_won')[:1]

        queryset = queryset.annotate(week=F('team__weeklymatchups__week'),
                                    season=F('season_settings__season'),
                                    team_score= Subquery(subquery_team),
                                    opp_score = Subquery(subquery_opp),
                                    pf=Sum('team_score'),
                                    pa=Sum('opp_score'),
                                    result=Subquery(subquery_result),
                                    wins=Count(F('result'), filter=Case(When(result="W", then=True), default=False)),
                                    losses=Count(F('result'), filter=Case(When(result="L", then=True), default=False)),
                                    ties=Count(F('result'), filter=Case(When(result="T", then=True), default=False)),
                                    weeks_won=Subquery(subquery_ww)

                                    #weekly_winner=Subquery(subquery_ww),
                                    #weeks_won=Count('weekly_winner', filter=Case(When(weekly_winner=True, then=True), default=False)),
                                    #seasons_won=Subquery(subquery_sw)
                                    )

        if playoff is None:
            queryset = queryset.order_by("seed")
        else:
            queryset = queryset.order_by("seed", "standing")
        
        queryset=queryset.values('team__id', 'season', 'team', "team__first_name", "team__last_name", "division", "division_standing", "pf", "pa", "wins", "losses", "ties", "seed", "weeks_won", "standing", "draft_pick")
        return queryset
    
    @action(methods=['get'], detail=False, url_path='all-time', url_name='all-time')
    def get_all_time(self, _request):
        queryset = Leaderboard.objects
        queryset = queryset.select_related('team').prefetch_related(Prefetch('team__weeklymatchups_set', to_attr='weeklymatchups_list'))
            
        subquery_team = WeeklyMatchups.objects.filter(team=OuterRef('team')).values('team').annotate(total_score=Sum(F('score'))).values('total_score')[:1]
        subquery_opp = WeeklyMatchups.objects.filter(opp=OuterRef('team')).values('opp').annotate(total_opp_score=Sum(F('score'))).values('total_opp_score')[:1]
        subquery_wins = WeeklyMatchups.objects.filter(team=OuterRef('team')).values('team').annotate(
            wins=Count(F('result'), filter=Case(When(result="W", then=True), default=False))
        ).values('wins')[:1]
        subquery_losses = WeeklyMatchups.objects.filter(team=OuterRef('team')).values('team').annotate(
            losses=Count(F('result'), filter=Case(When(result="L", then=True), default=False))
        ).values('losses')[:1]
        subquery_ties = WeeklyMatchups.objects.filter(team=OuterRef('team')).values('team').annotate(
            ties=Count(F('result'), filter=Case(When(result="T", then=True), default=False))
        ).values('ties')[:1]
        subquery_ww = WeeklyMatchups.objects.filter(team=OuterRef('team')).values('team').annotate(
            weeks_won=Count(F('weekly_winner'), filter=Case(When(weekly_winner=True, then=True), default=False))
        ).values('weeks_won')[:1]
        #subquery_seed =  Leaderboard.objects.filter(team=OuterRef('team')).values('seed')[:1]
        #subquery_standing = Leaderboard.objects.filter(team=OuterRef('team')).values('standing')[:1]

        queryset = queryset.values('team').distinct()
        
        queryset = queryset.annotate(
                                    pf=Subquery(subquery_team),
                                    pa=Subquery(subquery_opp),
                                    wins=Subquery(subquery_wins),
                                    losses=Subquery(subquery_losses),
                                    ties=Subquery(subquery_ties),
                                    avgseed=Avg(F('seed')),
                                    avgstanding=Avg(F('standing')),
                                    avgdraft_pick=Avg(F('draft_pick')),
                                    championships=Count(F('team'), filter=Case(When(standing=1, then=True), default=False)),
                                    weeks_won=Subquery(subquery_ww),
                                    seasons_won=Count(F('season_winner'), filter=Case(When(season_winner=True, then=True), default=False)),
                                    divisions_won=Count(F('division_winner'), filter=Case(When(division_winner=True, then=True), default=False))
                                    ).filter(team__active=True).order_by("-championships", "-wins", "avgstanding").values("team__id", "team__first_name", "team__last_name", "pf", "pa", "wins", "losses", "ties", "avgseed", "avgstanding", "avgdraft_pick", "championships", "seasons_won", "divisions_won", "weeks_won")
        return JsonResponse(AllTimeLeaderboardSerializer(queryset, many=True).data, safe=False)

    # # Define the base queryset
    # queryset = Leaderboard.objects

    

    
    
    # queryset = queryset.annotate(pf=Sum('team_score'), 
    #                              pa=Sum('opp_score'),
    #                              wins=Count(F('team__weeklymatchups__result'), filter=Case(When(team__weeklymatchups__result="W", then=True), default=False)),
    #                              losses=Count(F('team__weeklymatchups__result'), filter=Case(When(team__weeklymatchups__result="L", then=True), default=False)),
    #                              ties=Count(F('team__weeklymatchups__result'), filter=Case(When(team__weeklymatchups__result="T", then=True), default=False)),
    #                              weeks_won=Count(F('team__weeklymatchups__weeklywinner'), filter=Case(When(team__weeklymatchups=F('team__weeklymatchups__weeklywinner__weeklymatchup'), then=True), default=False)),
    #                              ).values('team', 'season', "team__first_name", "team__last_name", "pf", "pa", "wins", "losses", "ties", "seed", "weeks_won", "standing").distinct()
    
    # queryset = queryset.annotate(
    #                              championships=Count(F('team__weeklymatchups__weeklywinner'), filter=Case(When(team__weeklymatchups=F('team__weeklymatchups__weeklywinner__weeklymatchup'), then=True), default=False)),  
    #                             )
    
    # Order the queryset
    # queryset = queryset.values("team", 
    #                            "team__first_name",
    #                            "team__last_name",
    #                            "pf",
    #                            "pa",
    #                            "wins",
    #                            "losses",
    #                            "ties",
    #                            "seed",
    #                            "weeks_won",
    #                            "standing"
    #                            )

    serializer_class = LeaderboardSerializer

    '''
    for q in queryset:
        print(q["team"], q["team__first_name"], q["team__last_name"], q["season"], q["pf"], q["pa"], q["wins"], q["losses"], q["ties"], q["weeks_won"])
    '''