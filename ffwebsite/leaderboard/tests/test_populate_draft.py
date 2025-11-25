import os
from django.conf import settings
from django.test import TestCase
from unittest.mock import patch

from django.urls import reverse

from leaderboard.tests.utils import create_mock_draft_return, create_mock_draft_selections_return, create_mock_league_id_return, create_mock_season_settings_return, create_mock_rosters_return
from leaderboard.models import SeasonSettings
from leaderboard.views.data.sleeper_connection import SleeperClient

class PopulateNewDraftViewTests(TestCase):
    def setUp(self):
        self.auth = settings.API_AUTH_TOKEN

        patcher_sleeper_id_api = patch("leaderboard.views.data.sleeper_connection.SleeperClient.get_id_api")
        self.mock_sleeper_id_api = patcher_sleeper_id_api.start()
        self.addCleanup(patcher_sleeper_id_api.stop)

        patcher_sleeper_league_api = patch("leaderboard.views.data.sleeper_connection.SleeperClient.get_season_settings")
        self.mock_sleeper_season_settings = patcher_sleeper_league_api.start()
        self.addCleanup(patcher_sleeper_league_api.stop)

        patcher_sleeper_league_api = patch("leaderboard.views.data.sleeper_connection.SleeperClient.get_managers")
        self.mock_sleeper_managers = patcher_sleeper_league_api.start()
        self.addCleanup(patcher_sleeper_league_api.stop)

    def set_data(self, platform, season, league_id):
        self.platform = platform
        self.season = season
        self.league_id = league_id
    
    def save_mock_season_settings(self, platform, season, league_id):
        self.set_data(platform, season, league_id)
        data = {"platform": self.platform, "season": self.season}
        self.mock_sleeper_id_api.return_value = create_mock_league_id_return(league_id)
        league_id = self.mock_sleeper_id_api.return_value
        self.mock_sleeper_season_settings.return_value = create_mock_season_settings_return(self.platform, self.season, league_id)
        self.client.post(reverse("populate_season"), data=data, HTTP_AUTHORIZATION=self.auth)

    def save_mock_managers(self, season):
        data = {"season": season}
        self.mock_sleeper_managers.return_value = create_mock_rosters_return()
        self.client.post(reverse("populate_teams"), data=data, HTTP_AUTHORIZATION=self.auth)

    @patch("leaderboard.views.data.sleeper_connection.SleeperClient.get_draft_selections")
    @patch("leaderboard.views.data.sleeper_connection.SleeperClient.get_draft")
    def test_new_draft(self, mock_sleeperclient_get_draft=None, mock_sleeperclient_get_draft_selections=None):
        self.save_mock_season_settings("sleeper", "2023", "1")
        self.save_mock_managers(self.season)
        mock_sleeperclient_get_draft.return_value = create_mock_draft_return()
        mock_sleeperclient_get_draft_selections.return_value = create_mock_draft_selections_return()

        data = {"season": self.season}

        response = self.client.post(reverse("populate_draft"), data=data, HTTP_AUTHORIZATION=self.auth)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"message": f"Draft for {self.season} is populated!"})