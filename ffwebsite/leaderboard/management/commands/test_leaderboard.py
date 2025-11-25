from leaderboard.models import Leaderboard
from django.core.management.base import BaseCommand

class Command(BaseCommand):

    def handle(self, *args, **options):
        for leaderboard in Leaderboard.objects.all():
            print(f"{leaderboard.team.first_name} {leaderboard.team.last_name}: {leaderboard.wins}-{leaderboard.losses}-{leaderboard.ties}--{leaderboard.pf}--{leaderboard.pa}--{leaderboard.dp}--{leaderboard.weeks_won}")