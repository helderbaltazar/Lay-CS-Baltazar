import math
from datetime import datetime

class LeagueFormElo:
    def __init__(self, half_life_days=30, k_factor=20):
        self.half_life_days = half_life_days
        self.k_factor = k_factor
        self.elo_ratings = {}
        self.decay_rate = math.log(2) / half_life_days
        
        # Exponential Smoothing para gols
        self.exp_goals_for = {}
        self.exp_goals_against = {}
        self.exp_games_played = {}

    def get_rating(self, team_id):
        return self.elo_ratings.get(team_id, 1500)

    def process_fixtures(self, fixtures, target_date=None):
        """Processa um array de fixtures passadas de uma liga"""
        if not target_date:
            target_date = datetime.now()
            
        for f in fixtures:
            home_id = f['teams']['home']['id']
            away_id = f['teams']['away']['id']
            
            # Inicializa caso n tenha
            if home_id not in self.elo_ratings: self.elo_ratings[home_id] = 1500
            if away_id not in self.elo_ratings: self.elo_ratings[away_id] = 1500
            
            if home_id not in self.exp_goals_for: 
                self.exp_goals_for[home_id] = 0.0
                self.exp_goals_against[home_id] = 0.0
                self.exp_games_played[home_id] = 0.0
            if away_id not in self.exp_goals_for:
                self.exp_goals_for[away_id] = 0.0
                self.exp_goals_against[away_id] = 0.0
                self.exp_games_played[away_id] = 0.0

            # Verifica se terminou
            if f['fixture']['status']['short'] not in ['FT', 'AET', 'PEN']:
                continue

            goals_home = f['goals']['home']
            goals_away = f['goals']['away']
            if goals_home is None or goals_away is None:
                continue

            # Elo Calculation
            r_home = self.elo_ratings[home_id] + 50 # home advantage
            r_away = self.elo_ratings[away_id]
            
            e_home = 1 / (1 + 10 ** ((r_away - r_home) / 400))
            e_away = 1 / (1 + 10 ** ((r_home - r_away) / 400))
            
            if goals_home > goals_away:
                s_home, s_away = 1.0, 0.0
            elif goals_home < goals_away:
                s_home, s_away = 0.0, 1.0
            else:
                s_home, s_away = 0.5, 0.5
                
            self.elo_ratings[home_id] += self.k_factor * (s_home - e_home)
            self.elo_ratings[away_id] += self.k_factor * (s_away - e_away)
            
            # Time Decay para Força (Gols Reais - Fase 3 híbrida)
            match_date = datetime.fromtimestamp(f['fixture']['timestamp'])
            days_diff = (target_date - match_date).days
            if days_diff < 0:
                days_diff = 0
            
            weight = math.exp(-self.decay_rate * days_diff)
            
            # Home
            self.exp_goals_for[home_id] += goals_home * weight
            self.exp_goals_against[home_id] += goals_away * weight
            self.exp_games_played[home_id] += weight
            
            # Away
            self.exp_goals_for[away_id] += goals_away * weight
            self.exp_goals_against[away_id] += goals_home * weight
            self.exp_games_played[away_id] += weight

    def get_team_factors(self, team_id, league_avg):
        """Retorna H_Attack e H_Defense ou A_Attack e A_Defense baseado no Exponential Smoothing"""
        played = self.exp_games_played.get(team_id, 0.0)
        
        # Fallback de segurança se não houver jogos
        if played < 0.1:
            return 1.0, 1.0, 1500
            
        gf_avg = self.exp_goals_for.get(team_id, 0.0) / played
        ga_avg = self.exp_goals_against.get(team_id, 0.0) / played
        
        avg_home, avg_away = league_avg
        league_total_avg = (avg_home + avg_away) / 2.0
        
        # Aproximação de força usando gols decaídos
        attack = gf_avg / league_total_avg
        defense = ga_avg / league_total_avg
        
        elo = self.get_rating(team_id)
        
        return attack, defense, elo

# Memória cacheada por tempo de execução para evitar recalcular Elo 380 vezes no mesmo run
_elo_instances = {}

def get_league_form_elo(league_id, season):
    cache_key = f"{league_id}_{season}"
    if cache_key in _elo_instances:
        return _elo_instances[cache_key]
        
    from data.api_football import get_league_fixtures
    fixtures = get_league_fixtures(league_id, season)
    
    elo = LeagueFormElo()
    if fixtures:
        elo.process_fixtures(fixtures)
        
    _elo_instances[cache_key] = elo
    return elo

