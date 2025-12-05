import os
from django.conf import settings
from django.test import TestCase
from unittest.mock import patch

from django.urls import reverse

from leaderboard.tests.utils import create_mock_league_id_return, create_mock_season_settings_return

class PopulateNewSeasonViewTests(TestCase):
    def setUp(self):
        self.auth = settings.API_AUTH_TOKEN
        #self.env_patcher=patch.dict(os.environ, {"ENVIRONMENT": "local"}, clear=False)
        #self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    @patch("leaderboard.views.data.sleeper_connection.SleeperClient.get_season_settings")
    @patch("leaderboard.views.data.sleeper_connection.SleeperClient.get_id_api")
    def test_new_sleeper_season(self, mock_sleeperclient_get_id_api=None, mock_sleeperclient_get_season_settings=None):
        platform = "sleeper"
        season = "2023"

        mock_sleeperclient_get_id_api.return_value = create_mock_league_id_return(league_id=None)
        league_id = mock_sleeperclient_get_id_api.return_value

        mock_sleeperclient_get_season_settings.return_value = create_mock_season_settings_return(platform, season, league_id)

        data = {"platform": platform, "season": season}

        response = self.client.post(reverse("populate_season"), data=data, HTTP_AUTHORIZATION=self.auth)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"message": f"Season Settings for {season} are populated!"})

    @patch("leaderboard.views.data.sleeper_connection.SleeperClient.get_id_api")
    def test_no_platform_new_season(self, mock_sleeperclient_get_id_api=None):
        season = "2023"

        mock_sleeperclient_get_id_api.return_value = create_mock_league_id_return(league_id=None)
        
        data = {"season": season}

        response = self.client.post(reverse("populate_season"), data=data, HTTP_AUTHORIZATION=self.auth)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"error": "Missing 'platform' in request body"})