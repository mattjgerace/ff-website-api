from django.http import JsonResponse

from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
#from ffwebsite.leaderboard.views.weekly_matchups.serializers import WeeklyMatchupsSerializer

from leaderboard.tasks import HasAPIToken
from leaderboard.models import WeeklyMatchups
from leaderboard.views.weekly_matchups.serializers import AllTimeSerializer, PointsSerializer, RecordsSerializer, WeeklyMatchupsSerializer
from django_filters.rest_framework import DjangoFilterBackend


from django.db.models import Prefetch, Sum, OuterRef, Subquery
from django.db.models import Sum, Max, Case, When, Count, F, Q, Value, BooleanField, CharField, IntegerField, DecimalField

from django_filters import rest_framework as filters


class WeeklyMatchupsFilter(filters.FilterSet):
    permission_classes = [HasAPIToken]
    season = filters.NumberFilter(field_name="season_settings__season", lookup_expr='exact')
    lower_week = filters.NumberFilter(field_name="week", lookup_expr='gte')
    higher_week = filters.NumberFilter(field_name="week", lookup_expr='lte')

    class Meta:
        model = WeeklyMatchups
        fields = ['week', 'playoff']

class WeeklyMatchupsViewSet(ModelViewSet):
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = WeeklyMatchupsFilter
    serializer_class = WeeklyMatchupsSerializer

    queryset = WeeklyMatchups.objects

    # week = self.request.query_params.get('week', None)
    # season = self.request.query_params.get('season_settings__season', None)
    # playoff = self.request.query_params.get('playoff', None)

    # if season is not None:
    #     queryset = queryset.filter(season_settings__season=season)
    # if week is not None:
    #     queryset = queryset.filter(week__lte=week)
    # if playoff is not None:
    #     queryset = queryset.filter(playoff=bool(int(playoff)))
    

    queryset =  queryset.select_related('team', 'season_settings')
    
    subquery_opp = WeeklyMatchups.objects.filter(week=OuterRef('week'), team=OuterRef('opp'), opp=OuterRef('team')).values('score')[:1]

    queryset = queryset.annotate(season=F('season_settings__season'),
                                opp_score=Subquery(subquery_opp),
                                wins=Count(F('result'), filter=Case(When(result="W", then=True), default=False)),
                                losses=Count(F('result'), filter=Case(When(result="L", then=True), default=False)),
                                ties=Count(F('result'), filter=Case(When(result="T", then=True), default=False))  
                                )
    
    queryset = queryset.values("team__id", 
                            "team__first_name",
                            "team__last_name",
                            "season",
                            "week",
                            "score",
                            "opp_score",
                            "wins",
                            "losses",
                            "ties",
                            "playoff",
                            )
        

        # for q in queryset:
        #     print(q["team"], q["team__first_name"], q["team__last_name"], q["season"], q["pf"], q["pa"], q["wins"], q["losses"], q["ties"])

    @action(methods=['get'], detail=False, url_path='all-time', url_name='all-time')
    def all_time(self, _request):
        qs = WeeklyMatchups.objects
        qs =  qs.select_related('team', 'season_settings')
    
        subquery_opp = WeeklyMatchups.objects.filter(season=OuterRef('season'), team=OuterRef('opp'), opp=OuterRef('team')).values('score')[:1]

        qs = qs.annotate(season=F('season_settings__season'),
                                    opp_score=Subquery(subquery_opp),
                                    wins=Count(F('result'), filter=Case(When(result="W", then=True), default=False)),
                                    losses=Count(F('result'), filter=Case(When(result="L", then=True), default=False)),
                                    ties=Count(F('result'), filter=Case(When(result="T", then=True), default=False))  
                                    )
        
        qs = qs.values(
                        "team__id", 
                        "team__first_name",
                        "team__last_name",
                        "season",
                        "score",
                        "opp_score",
                        "wins",
                        "losses",
                        "ties",
                    )
        return JsonResponse(AllTimeSerializer(qs, many=True).data, safe=False)  

    # @action(methods=['get'], detail=False, url_path='records/top-years', url_name='records-top-years')
    # def top_years(self, _request):
    #     qs = WeeklyMatchups.objects
    #     qs = qs.select_related('team', 'season_settings').values(
    #                 "team_id", 
    #                 "team__first_name",
    #                 "team__last_name",
    #                 "season_settings__season",
    #             ).annotate(
    #                 pf=Sum(F('score')),
    #             ).order_by('-pf')[:15]
    #     return JsonResponse(RecordsSerializer(qs, many=True).data, safe=False)
    
    @action(methods=['get'], detail=False, url_path='records/top-years', url_name='records-top-years')
    def top_years(self, _request):
        qs = WeeklyMatchups.objects
        playoff = self.request.query_params.get('playoff', None)
        ppg = self.request.query_params.get('ppg', None)
        if bool(playoff) == True:
            qs = qs.filter(playoff=playoff)
        qs = qs.select_related('team', 'season_settings').values(
                    "team_id", 
                    "team__first_name",
                    "team__last_name",
                    "season_settings__season",
                )
        
        if bool(ppg) == True:
            qs = qs.annotate(
                        pf=Sum(F('score'))/Count(F('id')),
                    )
        else:
            qs = qs.annotate(
                        pf=Sum(F('score')),
                    )
        
        qs = qs.order_by('-pf')[:15]

        return JsonResponse(RecordsSerializer(qs, many=True).data, safe=False)

    @action(methods=['get'], detail=False, url_path='records/top-scores', url_name='records-top-scores')
    def top_scores(self, _request):
        qs = WeeklyMatchups.objects
        season = self.request.query_params.get('season_settings__season', None)
        if season is not None:
            qs = qs.filter(season_settings__season=season)
        qs = qs.select_related('team', 'opp', 'season_settings').values("team", 
                               "team__first_name",
                               "team__last_name",
                               "opp__first_name",
                               "opp__last_name",
                               "score",
                               "week",
                               "season_settings__season"
                               ).annotate(
                                   pf=(F('score'))
                               ).order_by('-score')[:50]
        return JsonResponse(PointsSerializer(qs, many=True).data, safe=False)