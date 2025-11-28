from collections import defaultdict
import decimal
import json
import os

from abc import ABC, abstractmethod
from django.db.models import Sum, Count, Case, When, IntegerField

from django.conf import settings
from leaderboard.models import Draft, DraftPicks, Leaderboard, Player, PlayerPoints, SeasonSettings, TeamManagerAPP, WeeklyMatchups
from leaderboard.models import PlayerESPN, PlayerSLEEPER
        
class BaseClient(ABC):
    def __init__(self, season):
        self._set_platform()
        self._set_season(season)
        self._set_models()
        self.player_model_possibilities = [PlayerSLEEPER, PlayerESPN]

    def _set_season(self, season) -> str:
        self.season = season

    def set_league_id(self, league_id) -> str:
        if league_id:
            self.league_id = league_id
        else:
            self.league_id = self.get_id_api()

    @abstractmethod
    def _set_platform(self):
        pass

    @abstractmethod
    def _set_models(self):
        pass

    @abstractmethod
    def _set_draft_id(self):
        pass

    def get_team_manager(self, team_id):
        return self.manager_model.objects.get(team_id=team_id).team_manager

    @abstractmethod
    def get_id_api(self):
        pass

    @abstractmethod
    def get_league_api(self):
        pass

    @abstractmethod
    def get_season_settings(self):
        pass

    @abstractmethod
    def get_draft_api(self):
        pass

    @abstractmethod
    def get_draft_selections_api(self):
        pass

    def process_season_settings(self, league_id=None):
        self.set_league_id(league_id)
        self.save_season_settings(*self.get_season_settings())

    def save_season_settings(self, league_info, platform_league_info):
        season_settings = SeasonSettings(**league_info)
        season_settings.save()
        platform_league_info["season_settings"] = season_settings
        self.season_settings_model.objects.create(**platform_league_info)
    
    def process_managers(self, season_settings):
        league_id = self.season_settings_model.objects.filter(season_settings=season_settings).first().league_id
        self.set_league_id(league_id)
        self.save_managers(self.get_managers(), season_settings)

    def save_managers(self, roster_info, season_settings):
        leaderboards = []
        platform_teams = []
        for roster in roster_info:
            if not self.manager_model.objects.filter(team_id = roster["roster_id"]).exists():
                user_key = json.loads(os.environ.get("SLEEPER_USER_KEY", "{}"))
                name = user_key[str(roster["roster_id"])].split()
                first_name = name[0]
                last_name = f"{name[1]} {name[2]}" if len(name) > 2 else name[1]
                if not TeamManagerAPP.objects.filter(first_name=first_name, last_name=last_name).exists():
                    team_manager = TeamManagerAPP(
                            first_name = first_name,
                            last_name = last_name,
                            active = True,
                        )
                    team_manager.save()
                else:
                    team_manager = TeamManagerAPP.objects.get(first_name=first_name, last_name=last_name)
                platform_teams.append(
                    self.manager_model(
                        team_manager=team_manager,
                        team_id=roster["roster_id"],
                        user_id=roster["owner_id"] #might be able to get rid of
                    )
                )
            else:
                team_manager = self.get_team_manager(roster["roster_id"])
            leaderboards.append(Leaderboard(
                season_settings=season_settings,
                team=team_manager,
                #wins = 0,
                #losses = 0,
                #ties = 0,
                division = season_settings.division_mapping.get(str(roster["settings"]["division"]), "N/A"),
                seed = 12-roster["roster_id"], #need to fix
                standing = roster["roster_id"],
                division_standing = 1,
            )
            )
        if len(platform_teams) > 0:
            self.manager_model.objects.bulk_create(platform_teams)
        Leaderboard.objects.bulk_create(leaderboards)

    def process_draft(self, season_settings):
        self._set_draft_id(season_settings)
        draft_info = self.get_draft()
        draft = self.save_draft(draft_info, season_settings)
        self.save_draft_order(draft_info, season_settings)
        self.save_draft_selections(draft, self.get_draft_selections())

    def save_new_player(self, player_id, player_details):
        if self.player_model.objects.filter(external_player_id=player_id).exists():
            return self.player_model.objects.get(external_player_id=player_id).player
        else:
            first_name = player_details[player_id]["first_name"]
            last_name = player_details[player_id]["last_name"]
            position = player_details[player_id]["position"]
            if Player.objects.filter(first_name=first_name, last_name=last_name, position=position).exists():
                existing_players = Player.objects.filter(first_name=first_name, last_name=last_name, position=position).all()
                for model in self.player_model_possibilities:
                    if model != self.player_model:
                        for existing_player in existing_players:
                            if model.objects.filter(player=existing_player).exists():
                                self.player_model.objects.create(
                                    player=existing_player,
                                    external_player_id=player_id
                                )
                                return existing_player
            player = Player(
                first_name = first_name,
                last_name = last_name,
                position = position,
            )   
            player.save()
            self.player_model.objects.create(
                player=player,
                external_player_id=player_id
            )
            return player

    def save_draft(self, draft_info, season_settings):
        draft_info["season_settings"] = season_settings
        draft = Draft(**draft_info)
        draft.save()
        return draft
    
    def save_draft_order(self, draft_info, season_settings):
        for leaderboard in Leaderboard.objects.filter(season_settings=season_settings):
            leaderboard.draft_pick = draft_info["order"][leaderboard.team.teammanagersleeper_set.first().user_id]
            leaderboard.save()

    def save_draft_selections(self, draft, draft_selections):
        draft_picks = []
        with open(os.path.join(settings.BASE_DIR, "leaderboard", "tests", "sample.json")) as json_file:
            player_details = json.load(json_file)
        for selection in draft_selections:
            draft_picks.append(
                DraftPicks(
                    draft=draft,
                    team=self.get_team_manager(selection["roster_id"]),
                    player=self.save_new_player(selection["player_id"], player_details),
                    round_num=selection["round"] if not (self.season == 2023 and (selection["player_id"] == '1689' or selection["player_id"] == '5849')) else (10 if selection["player_id"] == '1689' else 12),
                    pick_num=selection["pick_no"] if not (self.season == 2023 and (selection["player_id"] == '1689' or selection["player_id"] == '5849')) else (119 if selection["player_id"] == '1689' else 144) 
                )
            )
        DraftPicks.objects.bulk_create(draft_picks)

    def process_week(self, season_settings, week):
        league_id = self.season_settings_model.objects.filter(season_settings=season_settings).first().league_id
        self.set_league_id(league_id) 
        week_matchups_info = self.get_matchups(season_settings.season, week)
        self.save_matchups(season_settings, week, week_matchups_info)
        self.save_team_scores(season_settings, week)
        self.save_week_results(season_settings, week)
        if int(week) < season_settings.playoff_week_start:
            self.save_regular_season_standings(season_settings)
            if int(week) == season_settings.playoff_week_start-1:
                division_winners = Leaderboard.objects.filter(
                    division_standing=1, season_settings_id=season_settings.pk
                ).all()
                for division_winner in division_winners:
                    division_winner.division_winner = True
                    division_winner.save()

    def save_player_scores(self, weeklymatchup, players_points, starters):
        player_points = []
        with open(os.path.join(settings.BASE_DIR, "leaderboard", "tests", "sample.json")) as json_file:
            player_details = json.load(json_file)
        for player_id in players_points.keys():
            player = self.save_new_player(player_id, player_details)
            player_points.append(
                PlayerPoints(
                    weeklymatchup=weeklymatchup,
                    player=player,
                    points=players_points[player_id],
                    starter=True if player_id in starters else False,
                    week = weeklymatchup.week,
                    season = weeklymatchup.season_settings.season,
                )
            )
        PlayerPoints.objects.bulk_create(player_points)
    
    def save_matchups(self, season_settings, week, week_matchups_info):
        games=[[] for _ in range(len(week_matchups_info)//2)]
        for matchup in week_matchups_info:
            if matchup["matchup_id"] != None:
                games[matchup["matchup_id"]-1].append(matchup["roster_id"])
        for matchup in week_matchups_info:
            if matchup["matchup_id"] != None:
                if matchup["matchup_id"] != None:
                    team_manager = self.get_team_manager(matchup["roster_id"])
                    opp_roster_id = games[matchup["matchup_id"]-1][0] if games[matchup["matchup_id"]-1][0] != matchup["roster_id"] else games[matchup["matchup_id"]-1][1]
                    team_manager_opp = self.get_team_manager(opp_roster_id)
                    weeklymatchup = WeeklyMatchups(
                        week=week,
                        season_settings=season_settings,
                        team=team_manager,
                        opp=team_manager_opp,
                        playoff=True if week >= season_settings.playoff_week_start else False
                        #roster=matchup.players, #might not need
                        #starters=matchup.starters, #might not need
                        )
                    weeklymatchup.save()
                    self.save_player_scores(weeklymatchup, matchup["players_points"], matchup["starters"])

    def save_team_scores(self, season_settings, week):
        weekly_matchups = WeeklyMatchups.objects.filter(week=week, season_settings=season_settings)
        scores = {}
        for matchup in weekly_matchups:
            team_starters = matchup.playerpoints_set.filter(starter=True)
            scores[matchup] = decimal.Decimal(0.00)
            for player in team_starters :
                scores[matchup] += player.points
            matchup.score = scores[matchup]
            matchup.save()
        
        if (week < season_settings.playoff_week_start):
            weeklywinner = max(scores, key=scores.get)
            weeklywinner.weekly_winner = True
            weeklywinner.save()

        #Calculate Season Leader in Points
        season_matchups = WeeklyMatchups.objects.filter(playoff=False, season_settings=season_settings.pk)
        scores = {}
        for matchup in season_matchups:
            if matchup not in scores:
                scores[matchup] = matchup.score
            else:
                scores[matchup] += matchup.score
        seasonwinner = max(scores, key=scores.get)
        season_teams = Leaderboard.objects.filter(season_settings=season_settings.pk)
        for team in season_teams:
            if seasonwinner.team == team.team:
                team.season_winner = True
            else:
                team.season_winner = False
            team.save()
    
    def save_week_results(self, season_settings, week):
        weekly_matchups = WeeklyMatchups.objects.filter(week=week, season_settings=season_settings.pk)
        for matchup in weekly_matchups:
            #lb = Leaderboard.objects.get(team=matchup.team, season_settings=matchup.season_settings)
            opp_matchup = WeeklyMatchups.objects.get(team=matchup.opp, opp=matchup.team, week=matchup.week, 
                                                     season_settings=matchup.season_settings)
            if matchup.score > opp_matchup.score:
                #lb.wins += 1
                matchup.result = "W"
            if matchup.score == opp_matchup.score:
                #lb.ties += 1
                matchup.result = "T"
            if matchup.score < opp_matchup.score:
                #lb.losses += 1
                matchup.result = "L"
            #lb.save()
            matchup.save()
    
    def save_regular_season_standings(self, season_settings):
        #print(season_settings.__dict__)

        # Get Season Stats
        standings = WeeklyMatchups.objects.filter(season_settings=season_settings.pk).values('team').annotate(
            pf=Sum('score'),
            #total_opp_score=Sum('opp__score'),  # Assuming 'opp' has a score field too
            wins=Count(Case(When(result='W', then=1), output_field=IntegerField())),
            ties=Count(Case(When(result='T', then=1), output_field=IntegerField())),
            losses=Count(Case(When(result='L', then=1), output_field=IntegerField()))
            )
        
        # Set up head to head record
        for standing in standings:
            head_to_head = {}
            games = WeeklyMatchups.objects.filter(season_settings=season_settings.pk, team=standing["team"])
            for game in games:
                if game.opp not in head_to_head:
                    head_to_head[game.opp.pk] = 0
                if game.result == 'W':
                    head_to_head[game.opp.pk] += 1
            standing["head_to_head"] = head_to_head
        
        # Find Out division Seeding First
        num_divisions = int(season_settings.league_settings["divisions"])
        if num_divisions and num_divisions > 1:
            # Break Up divisions 
            division_winners = []
            remaining_teams = []
            divisions = {}
            for standing in standings:
                #print(standing)
                leaderboard = Leaderboard.objects.filter(
                    team=standing['team'], season_settings_id=season_settings.pk
                ).first()
                
                # Add the leaderboard division info if the leaderboard object exists
                if leaderboard:
                    if leaderboard.division not in divisions:
                        divisions[leaderboard.division] = {}
                    divisions[leaderboard.division][standing["team"]] = standing
            
            for division_name, teams in divisions.items():
                # Step 1: Sort teams by total wins (descending order)
                sorted_teams = sorted(teams.keys(), key=lambda team: teams[team]['wins'], reverse=True)

                # Step 2: Identify groups of tied teams
                tied_groups = defaultdict(list)
                for team in sorted_teams:
                    tied_groups[teams[team]['wins']].append(team)

                # Step 3: Apply head-to-head tie-breaker within each tied group
                division_ranking = []

                for win_count, group in sorted(tied_groups.items(), reverse=True):
                    if len(group) > 1:  # Only apply tie-breakers if multiple teams have the same wins
                        # Compute head-to-head win count within the tied group
                        win_counts = {team: sum(teams[team]['head_to_head'].get(opponent, 0) for opponent in group) for team in group}
                        
                        # Step 3A: Sort by head-to-head wins
                        sorted_group = sorted(group, key=lambda team: win_counts[team], reverse=True)

                        # Step 3B: Check if there's still a tie after head-to-head wins
                        head_to_head_values = list(win_counts.values())
                        if len(set(head_to_head_values)) == 1:  # All have the same head-to-head wins
                            # Step 4: Use point differential as tie-breaker
                            sorted_group = sorted(group, key=lambda team: teams[team]['pf'], reverse=True)

                        division_ranking.extend(sorted_group)
                    else:
                        division_ranking.extend(group)

                # Step 5: Print the division ranking
                #print("Division ranking:", division_ranking)
                for division_place, division_team in enumerate(division_ranking):
                    leaderboard = Leaderboard.objects.filter(
                        team=division_team, season_settings_id=season_settings.pk
                    ).first()
                    leaderboard.division_standing = division_place+1
                    leaderboard.save()
                winner = division_ranking.pop(0)
                division_winners.append(teams[winner])
                teams.pop(winner)

                #print(teams)

                #TODO- FIX REMAINING TEAMS
                for team, team_data in teams.items():
                    remaining_teams.append(team_data)
            standings = remaining_teams

        # Sort Remaining Teams
        #print(standings)
        #print(division_winners)
        sorted_standings = sorted(standings, key=lambda standing: (standing['wins'], standing['pf']), reverse=True)
        if division_winners:
            sorted_division_winners = sorted(division_winners, key=lambda standing: (standing['wins'], standing['pf']), reverse=True)
            sorted_division_winners.extend(sorted_standings)
            sorted_standings = sorted_division_winners
        for place, team_data in enumerate(sorted_standings):
            leaderboard = Leaderboard.objects.filter(
                    team=team_data["team"], season_settings_id=season_settings.pk
                ).first()
            leaderboard.seed = place+1
            leaderboard.save()
