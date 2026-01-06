from collections import defaultdict
import decimal
import json
import os

from abc import ABC, abstractmethod
from django.db.models import Sum, Count, Case, When, IntegerField

from leaderboard.models import Draft, DraftPicks, ExhibitionWeeklyMatchups, Leaderboard, Player, PlayerPoints, SeasonSettings, TeamManagerAPP, WeeklyMatchups
from leaderboard.models import PlayerESPN, PlayerSLEEPER
        
class BaseClient(ABC):
    def __init__(self, season, mongodb):
        self._set_platform()
        self._set_season(season)
        self._set_mongodb(mongodb)
        self._set_models()
        self.player_model_possibilities = [PlayerSLEEPER, PlayerESPN]

    def _set_season(self, season):
        self.season = season

    def _set_mongodb(self, mongodb):
        self.mongodb = mongodb

    def set_league_id(self, league_id) -> str:
        if league_id:
            self.league_id = league_id
        else:
            self.league_id = self.get_league_id()

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
        for i, roster in enumerate(roster_info):
            if not self.manager_model.objects.filter(team_id = roster["roster_id"]).exists():
                if not TeamManagerAPP.objects.filter(first_name=roster["first_name"], last_name=roster["last_name"]).exists():
                    team_manager = TeamManagerAPP(
                            first_name = roster["first_name"],
                            last_name = roster["last_name"],
                            active = True,
                        )
                    team_manager.save()
                else:
                    team_manager = TeamManagerAPP.objects.get(first_name=roster["first_name"], last_name=roster["last_name"])
                
                if "owner_id" in roster.keys():
                    platform_model = self.manager_model(
                        team_manager=team_manager,
                        team_id=roster["roster_id"],
                        user_id=roster["owner_id"] #might be able to get rid of
                    )
                else:
                    platform_model = self.manager_model(
                        team_manager=team_manager,
                        team_id=roster["roster_id"],
                    )
                platform_teams.append(platform_model)
            else:
                team_manager = self.get_team_manager(roster["roster_id"])
            leaderboards.append(Leaderboard(
                season_settings=season_settings,
                team=team_manager,
                #wins = 0,
                #losses = 0,
                #ties = 0,
                division = season_settings.division_mapping.get(str(roster["settings"]["division"]), "N/A") if "settings" in roster.keys() else "N/A",
                seed = i+1, #need to fix
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

    def save_new_player(self, player_id):
        if self.player_model.objects.filter(external_player_id=player_id).exists():
            return self.player_model.objects.get(external_player_id=player_id).player
        else:
            player_details = self.mongodb["players"].find_one({self.mongo_id: player_id})
            first_name = player_details["first_name"]
            last_name = player_details["last_name"]
            position = player_details["position"]
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
        for key, value in draft_info["order"].items():
            team_manager =self.get_team_manager(key)
            leaderboard = Leaderboard.objects.get(season_settings=season_settings, team=team_manager)
            leaderboard.draft_pick = value
            leaderboard.save()

    def save_draft_selections(self, draft, draft_selections):
        draft_picks = []
        for selection in draft_selections:
            draft_picks.append(
                DraftPicks(
                    draft=draft,
                    team=self.get_team_manager(selection["roster_id"]),
                    player=self.save_new_player(selection["player_id"]),
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
                self.save_season_leader_pf(season_settings)
                self.save_division_winners(season_settings)
                self.save_standing_non_playoff(season_settings)
        else:
             self.save_standing_playoff(season_settings, week)

    def save_player_scores(self, weeklymatchup, players_points, starters, is_exhibition):
        player_points = []
        for player_id in players_points.keys():
            player = self.save_new_player(player_id)
            player_points.append(
                PlayerPoints(
                    weeklymatchup=None if is_exhibition else weeklymatchup,
                    exhibtion=weeklymatchup if is_exhibition else None,
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
                    if week >= season_settings.playoff_week_start and Leaderboard.objects.get(season_settings=season_settings, team=team_manager).standing:
                        weeklymatchup = ExhibitionWeeklyMatchups(
                            week=week,
                            season_settings=season_settings,
                            team=team_manager,
                            opp=team_manager_opp,
                            playoff=True if week >= season_settings.playoff_week_start else False
                            )
                        is_exhibition = True
                    else:
                        weeklymatchup = WeeklyMatchups(
                            week=week,
                            season_settings=season_settings,
                            team=team_manager,
                            opp=team_manager_opp,
                            playoff=True if week >= season_settings.playoff_week_start else False
                            #roster=matchup.players, #might not need
                            #starters=matchup.starters, #might not need
                            )
                        is_exhibition = False
                    weeklymatchup.save()
                    self.save_player_scores(weeklymatchup, matchup["players_points"], matchup["starters"], is_exhibition)

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

    def save_season_leader_pf(self, season_settings):
        season_matchups = WeeklyMatchups.objects.filter(playoff=False, season_settings=season_settings.pk)
        scores = {}
        for matchup in season_matchups:
            if matchup.team not in scores:
                scores[matchup.team] = matchup.score
            else:
                scores[matchup.team] += matchup.score
        seasonwinner = max(scores, key=scores.get)
        season_teams = Leaderboard.objects.filter(season_settings=season_settings.pk)
        for team in season_teams:
            if seasonwinner == team.team:
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

    def save_division_winners(self, season_settings):
        division_winners = Leaderboard.objects.filter(
                    division_standing=1, season_settings_id=season_settings.pk
                ).all()
        for division_winner in division_winners:
            division_winner.division_winner = True
            division_winner.save()
    
    def save_standing_non_playoff(self, season_settings):
        non_playoff_teams = Leaderboard.objects.filter(
                    seed__gt=6, season_settings_id=season_settings.pk #TODO-make # playoff teams dynamic
                ).all()
        for non_playoff_team in non_playoff_teams:
            non_playoff_team.standing = non_playoff_team.seed
            non_playoff_team.save()

    def save_standing_playoff(self, season_settings, week):
        playoff_teams = Leaderboard.objects.filter(
                    standing=None, season_settings_id=season_settings.pk
                ).order_by('-seed').values_list('team_id', flat=True)
        if len(playoff_teams) == 4:
            previous_playoff_teams = Leaderboard.objects.filter(
                                standing__lte=6, standing__gte=5, season_settings_id=season_settings.pk
                            ).order_by('-seed').values_list('team_id', flat=True) #maybe change this to get all playoff teams from previous week and remove the current
            previous_playoff_losing_teams = WeeklyMatchups.objects.filter(
                                    team_id__in=previous_playoff_teams, 
                                    week=week-1, 
                                    season_settings_id=season_settings.pk, 
                                    result="L"
                                    ).values_list('team_id', flat=True)
            if set(previous_playoff_teams) != set(previous_playoff_losing_teams):
                self.save_championship_standings(season_settings, week, playoff_teams)  
        else: 
            playoff_losing_teams = WeeklyMatchups.objects.filter(
                                    team_id__in=playoff_teams, 
                                    week=week, 
                                    season_settings_id=season_settings.pk, 
                                    result="L"
                                    ).values_list('team_id', flat=True)
            place = len(playoff_teams)
            for playoff_team in playoff_teams:
                if playoff_team in playoff_losing_teams:
                    playoff_losing_team = Leaderboard.objects.get(standing=None, season_settings_id=season_settings.pk, team=playoff_team)
                    playoff_losing_team.standing = place
                    playoff_losing_team.save()
                    place -= 1
    
    def save_championship_standings(self, season_settings, week, playoff_teams):
        championship_teams = WeeklyMatchups.objects.filter(
                                    team_id__in=playoff_teams, 
                                    week=week-1, 
                                    season_settings_id=season_settings.pk, 
                                    result="W"
                                    ).values_list('team_id', flat=True)
        third_place_teams = WeeklyMatchups.objects.filter(
                            team_id__in=playoff_teams, 
                            week=week-1, 
                            season_settings_id=season_settings.pk, 
                            result="L"
                            ).values_list('team_id', flat=True)
        results = WeeklyMatchups.objects.filter(
                            team_id__in=playoff_teams, 
                            week=week, 
                            season_settings_id=season_settings.pk, 
                            ).values_list('team_id', 'result', flat=False)
        for team_info in results:
            if team_info[0] in third_place_teams:
                if team_info[1] == 'W':
                    place = 3
                if team_info[1] == 'L':
                    place = 4
            if team_info[0] in championship_teams:
                if team_info[1] == 'W':
                    place = 1
                if team_info[1] == 'L':
                    place = 2
            playoff_team = Leaderboard.objects.get(standing=None, season_settings_id=season_settings.pk, team=team_info[0])
            playoff_team.standing = place
            playoff_team.save()

    def compute_head_to_head(self, teams, tied_group):
        games_played = {}

        for team in tied_group:
            total_games = 0
            for opponent in tied_group:
                if opponent == team:
                    continue

                record = teams[team]['head_to_head'].get(opponent)
                if record:
                    total_games += sum(record)

            games_played[team] = total_games

        if len(set(games_played.values())) != 1:
            return [tied_group]
        else:
            # Compute head-to-head win count within the tied group
            head_to_head_wins = {team: sum([teams[team]['head_to_head'].get(opponent, [0,0,0])[0] for opponent in tied_group]) for team in tied_group}

            head_to_head_groups = defaultdict(list)
            for team, wins in head_to_head_wins.items():
                head_to_head_groups[wins].append(team)

            # Sort groups by descending wins
            sorted_groups = [
                head_to_head_groups[wins]
                for wins in sorted(head_to_head_groups.keys(), reverse=True)
            ]
            return sorted_groups

    def save_division_standings(self, season_settings, standings, tiebreak):
        division_leaders = {}
        divisions = {}
        # Break teams up into divisions 
        for standing in standings.values():
            leaderboard = Leaderboard.objects.filter(
                team=standing['team'], season_settings_id=season_settings.pk
            ).first()
            
            if leaderboard:
                if leaderboard.division not in divisions:
                    divisions[leaderboard.division] = {}
                divisions[leaderboard.division][standing["team"]] = standing
        
        # Sort through divisions
        for _division_name, division_teams in divisions.items():
            division_ranking = []
            division_win_counts = {team: sum([division_teams[team]['head_to_head'].get(division_opp, [0,0,0])[0] for division_opp in division_teams]) for team in division_teams}
            division_ranking.extend(self.get_seeding(division_teams, tiebreak, division_win_counts))
            for division_place, division_team in enumerate(division_ranking):
                leaderboard = Leaderboard.objects.filter(
                    team=division_team, season_settings_id=season_settings.pk
                ).first()
                leaderboard.division_standing = division_place+1
                leaderboard.save()
            leader = division_ranking.pop(0)
            division_leaders[leader] = division_teams[leader]
        return division_leaders

    def get_seeding(self, teams, tiebreak, division=None):
        final_standing = []
        if tiebreak == "head_to_head":
            # Step 1: Sort teams by total wins (descending order)
            sorted_teams = sorted(teams.keys(), key=lambda team: teams[team]['wins'], reverse=True)

            # Step 2: Identify groups of teams tied with same amount of win
            win_groups = defaultdict(list)
            for team in sorted_teams:
                win_groups[teams[team]['wins']].append(team)
            
            # Step 3: Check if there is a tie between teams with the same numer of wins
            for _win_count, group in sorted(win_groups.items(), reverse=True):
                sorted_group = []
                if len(group) > 1:  # Only apply tie-breakers if multiple teams have the same wins
                    # Compute head-to-head win count within the tied group
                    sorted_head_to_head = self.compute_head_to_head(teams, group)
                    # Step 3B: Check if there's still a tie after head-to-head wins
                    for head_to_head_rank in sorted_head_to_head:
                        if len(head_to_head_rank) == 1:
                            sorted_group.extend(head_to_head_rank)
                        else:
                            head_to_head_group = {tied_team: teams[tied_team] for tied_team in head_to_head_rank}
                            if division:
                                division_wins = {team: division[team] for team in division if team in head_to_head_group}
                                # Use division wins as tie-breaker
                                sorted_sub_group = sorted(head_to_head_group, key=lambda team: division_wins[team], reverse=True)
                                # Step 3C: Check if there's still a tie after division wins
                                division_win_counts_values = list(division_wins.values())
                                if len(set(division_win_counts_values)) == 1:
                                    sorted_group.extend(self.get_seeding({tied_team: teams[tied_team] for tied_team in sorted_sub_group}, "pf"))
                                else:
                                    sorted_group.extend(sorted_sub_group)
                            else:
                                sorted_group.extend(self.get_seeding(head_to_head_group, "pf"))
                else:
                    sorted_group = group 
                final_standing.extend(sorted_group)
        else:
            final_standing.extend(sorted(teams.keys(), key=lambda team: (teams[team]['wins'], teams[team]["pf"]), reverse=True))
        return final_standing

    def save_regular_season_standings(self, season_settings):
        # Get Season Stats
        standings = WeeklyMatchups.objects.filter(season_settings=season_settings.pk, playoff=False).values('team').annotate(
            pf=Sum('score'),
            #total_opp_score=Sum('opp__score'),  # Assuming 'opp' has a score field too
            wins=Count(Case(When(result='W', then=1), output_field=IntegerField())),
            ties=Count(Case(When(result='T', then=1), output_field=IntegerField())),
            losses=Count(Case(When(result='L', then=1), output_field=IntegerField()))
            )
        final_seeding = []
        num_divisions = int(season_settings.league_settings["divisions"])
        if int(season_settings.season) < 2024:
            division_tiebreak = "head_to_head"
            seeding_tiebreak = "head_to_head"
            wildcard_tiebreak = "head_to_head"
        if int(season_settings.season) == 2024:
            division_tiebreak = "head_to_head"
            seeding_tiebreak = "head_to_head"
            wildcard_tiebreak = "pf"
        else:
            division_tiebreak = "head_to_head"
            seeding_tiebreak = "pf"
            wildcard_tiebreak = "pf"

            
        
        if any([division_tiebreak, seeding_tiebreak, wildcard_tiebreak])=="head_to_head" or num_divisions > 1:
            # Set up head to head record
            for standing in standings:
                head_to_head = {}
                games = WeeklyMatchups.objects.filter(season_settings=season_settings.pk, team=standing["team"])
                for game in games:
                    if game.opp.pk not in head_to_head:
                        head_to_head[game.opp.pk] = [0,0,0]
                    if game.result == 'W':
                        head_to_head[game.opp.pk][0] += 1
                    if game.result == 'L':
                        head_to_head[game.opp.pk][1] += 1
                    if game.result == 'T':
                        head_to_head[game.opp.pk][2] += 1
                standing["head_to_head"] = head_to_head

        standings = {team_info["team"]: team_info for team_info in standings}
        if num_divisions and num_divisions > 1:
            # Find Out division Seeding First
            division_leaders = self.save_division_standings(season_settings, standings, division_tiebreak)
            final_seeding.extend(self.get_seeding(division_leaders, seeding_tiebreak))
            standings = {team: standings[team] for team in standings if team not in division_leaders.keys()}

        final_seeding.extend(self.get_seeding(standings, wildcard_tiebreak))
        for place, team in enumerate(final_seeding):
            leaderboard = Leaderboard.objects.filter(
                    team=team, season_settings_id=season_settings.pk
                ).first()
            leaderboard.seed = place+1
            if num_divisions < 2:
                leaderboard.division_standing = place+1
            leaderboard.save()
