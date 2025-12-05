import os
from django.conf import settings
from django.test import TestCase
from unittest.mock import patch

from django.urls import reverse

from leaderboard.tests.utils import create_mock_players_api_return

class PopulatePlayerCollectionViewTests(TestCase):
    def setUp(self):
        self.auth = settings.API_AUTH_TOKEN

    def tearDown(self):
        self.env_patcher.stop()

    @patch("leaderboard.views.data.sleeper_connection.SleeperClient.get_players_api")
    def test_populate_player_collection(self, mock_sleeperclient_get_players_api=None):
        mock_sleeperclient_get_players_api.return_value = create_mock_players_api_return()

        data = {}

        response = self.client.post(reverse("populate_player_collection"), data=data, HTTP_AUTHORIZATION=self.auth)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"message": f"Player data updated successfully."})