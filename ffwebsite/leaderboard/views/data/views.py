from datetime import date, datetime
from enum import Enum
from django.conf import settings
from pymongo import ASCENDING, UpdateOne
from leaderboard.tasks import HasAPIToken
from leaderboard.views.data.espn_connection import EspnClient
from leaderboard.views.data.sleeper_connection import SleeperClient
from leaderboard.models import Draft, Leaderboard, SeasonSettings, WeeklyMatchups

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

def to_json_safe(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, list):
        return [to_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {k: to_json_safe(v) for k, v in value.items()}
    return value

def get_client(platform, season):
    match platform:
        case "sleeper":
            return SleeperClient(season)
        case "espn":
            return EspnClient(season)
        case _:
            return None

class PopulateNewSeasonView(APIView):
    permission_classes = [HasAPIToken]

    def post(self, request, *args, **kwargs):
        platform = request.data.get("platform")
        season = request.data.get("season")
        if not platform:
            return Response(
                {"error": "Missing 'platform' in request body"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if SeasonSettings.objects.filter(season = season).exists():
            return Response(
                {"error": f"'season': {season} in request body is already populated in SeasonSettings table in database"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        client = get_client(platform, season)
        if not client:
            return Response(
                {"error": "'platform' in request body is not a valid platform: 'espn', 'sleeper'"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        client.process_season_settings()  

        result = f"Season Settings for {season} are populated!"

        return Response({"message": result}, status=status.HTTP_201_CREATED)
    
class PopulateNewTeamsView(APIView):
    permission_classes = [HasAPIToken]

    def post(self, request, *args, **kwargs):
        season = request.data.get("season")
        if not season:
            return Response(
                {"error": "Missing season in request body"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            season_settings = SeasonSettings.objects.get(season=season)
            if season_settings:
                if Leaderboard.objects.filter(season_settings=season_settings).exists():
                    return Response(
                    {"error": f"Teams are already populated for the {season} season"},
                    status=status.HTTP_400_BAD_REQUEST,
                    )
                client = get_client(season_settings.platform, season_settings.season)
                client.process_managers(season_settings)
            else:
                return Response(
                {"error": f"No season_settings associated with {season}"},
                status=status.HTTP_400_BAD_REQUEST,
                )
            
        result = f"Managers for {season} are populated!"

        return Response({"message": result}, status=status.HTTP_201_CREATED)

class PopulateNewDraftView(APIView):
    permission_classes = [HasAPIToken]

    def post(self, request, *args, **kwargs):
        season = request.data.get("season")
        if not season:
            return Response(
                {"error": "Missing 'season' in request body"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            season_settings = SeasonSettings.objects.get(season=season)
            if Draft.objects.filter(season_settings=season_settings).exists():
                return Response(
                    {"error": f"'season': {season} in request body is already populated in Draft table in database"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                if not Leaderboard.objects.filter(season_settings=season_settings).exists():
                    return Response(
                    {"error": f"Teams are not yet populated for the {season} season"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
                client = get_client(season_settings.platform, season_settings.season)
                client.process_draft(season_settings)

        result = f"Draft for {season} is populated!"

        return Response({"message": result}, status=status.HTTP_201_CREATED)
    
class PopulateNewMatchupsView(APIView):
    permission_classes = [HasAPIToken]

    def post(self, request, *args, **kwargs):
        season = request.data.get("season")
        week = int(request.data.get("week"))
        if not season or not week:
            return Response(
                {"error": "Include 'season' and 'week' in request body"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            if int(season) > 2025:
                return Response(
                                {"error": f"Ensure week <= 2025"},
                                status=status.HTTP_400_BAD_REQUEST,
                                )
            season_settings = SeasonSettings.objects.get(season=season)
            if not Leaderboard.objects.filter(season_settings=season_settings).exists():
                return Response(
                {"error": f"Teams are not populated for the {season} season"},
                status=status.HTTP_400_BAD_REQUEST,
                )
            if week > 17 or week < 1: # > value should be dynamic from db (playoff_start_week+3?)
                return Response(
                                {"error": f"Ensure week <= 17"},
                                status=status.HTTP_400_BAD_REQUEST,
                                )
            else:
                if WeeklyMatchups.objects.filter(season_settings=season_settings, week=week).exists():
                    return Response(
                                {"error": f"Ensure there is no matchup data for the current week in this season"},
                                status=status.HTTP_400_BAD_REQUEST,
                                )
                else:
                    client = get_client(season_settings.platform, season_settings.season)
                    client.process_week(season_settings, week)
                    result = f"Matchups for week {week} of the {season} season are populated!"

            return Response({"message": result}, status=status.HTTP_201_CREATED)
        
class PopulatePlayerCollection(APIView):
    permission_classes = [HasAPIToken]

    def post(self, request, *args, **kwargs):
        db = settings.MONGO_DB              
        players_collection = db["players"]

        db.drop_collection("players")

        client = get_client("sleeper", "2023")

        players = client.get_players_api()

        operations = []

        for p in players.keys():
            player_data = to_json_safe(players[p].__dict__)
            
            doc = {
                "_id": player_data["player_id"],
                **player_data
            }

            operations.append(
                UpdateOne({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
            )

        players_collection.bulk_write(operations)

        result = f"Player data updated successfully."
        return Response({"message": result}, status=status.HTTP_201_CREATED)