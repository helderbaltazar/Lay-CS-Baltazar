import math

class PoissonDixonColes:
    def __init__(self, rho=-0.10, max_goals=7):
        self.rho = rho
        self.max_goals = max_goals

    def poisson_pmf(self, k, lam):
        if lam == 0:
            return 1.0 if k == 0 else 0.0
        return ((lam ** k) * math.exp(-lam)) / math.factorial(k)

    def dixon_coles_tau(self, x, y, lam_x, lam_y):
        if x == 0 and y == 0:
            return 1 - (lam_x * lam_y * self.rho)
        elif x == 0 and y == 1:
            return 1 + (lam_x * self.rho)
        elif x == 1 and y == 0:
            return 1 + (lam_y * self.rho)
        elif x == 1 and y == 1:
            return 1 - self.rho
        return 1.0

    def predict(self, lam_home, lam_away):
        matrix = {}
        total_prob = 0.0

        for h in range(self.max_goals + 1):
            for a in range(self.max_goals + 1):
                prob = self.poisson_pmf(h, lam_home) * self.poisson_pmf(a, lam_away)
                tau = self.dixon_coles_tau(h, a, lam_home, lam_away)
                adjusted_prob = prob * tau
                
                # Previne probabilidades negativas em lambdas extremos
                adjusted_prob = max(0.0, adjusted_prob)
                
                matrix[(h, a)] = adjusted_prob
                total_prob += adjusted_prob

        # Normaliza a matriz para somar exatamente 1.0
        if total_prob > 0:
            for key in matrix:
                matrix[key] /= total_prob

        return matrix

    def get_probabilities(self, lam_home, lam_away, targets):
        matrix = self.predict(lam_home, lam_away)
        results = {}
        for target in targets:
            h, a = map(int, target.split('-'))
            if (h, a) in matrix:
                results[target] = matrix[(h, a)]
            else:
                results[target] = 0.0
        return results

    def get_under_over_probabilities(self, lam_home, lam_away, limit=2.5):
        matrix = self.predict(lam_home, lam_away)
        under = 0.0
        for (h, a), prob in matrix.items():
            if (h + a) < limit:
                under += prob
        return {"under": under, "over": 1.0 - under}

    def get_btts_probabilities(self, lam_home, lam_away):
        matrix = self.predict(lam_home, lam_away)
        yes = 0.0
        for (h, a), prob in matrix.items():
            if h > 0 and a > 0:
                yes += prob
        return {"yes": yes, "no": 1.0 - yes}

    def get_match_odds(self, lam_home, lam_away):
        matrix = self.predict(lam_home, lam_away)
        home = draw = away = 0.0
        for (h, a), prob in matrix.items():
            if h > a:
                home += prob
            elif h == a:
                draw += prob
            else:
                away += prob
        return {"home": home, "draw": draw, "away": away}

    def get_extra_probabilities(self, lam_home, lam_away):
        matrix_ft = self.predict(lam_home, lam_away)
        lam_home_ht = lam_home * 0.45
        lam_away_ht = lam_away * 0.45
        matrix_ht = self.predict(lam_home_ht, lam_away_ht)
        
        results = {}
        # Under/Over FT
        u25 = sum(p for (h,a), p in matrix_ft.items() if h+a < 2.5)
        results["UNDER_2.5"] = u25
        results["OVER_2.5"] = 1.0 - u25
        
        results["UNDER_3.5"] = sum(p for (h,a), p in matrix_ft.items() if h+a < 3.5)
        results["UNDER_4.5"] = sum(p for (h,a), p in matrix_ft.items() if h+a < 4.5)
        
        # BTTS
        btts_no = sum(p for (h,a), p in matrix_ft.items() if h == 0 or a == 0)
        results["BTTS_YES"] = 1.0 - btts_no
        
        # Match Odds
        home = sum(p for (h,a), p in matrix_ft.items() if h > a)
        draw = sum(p for (h,a), p in matrix_ft.items() if h == a)
        results["BACK_HOME"] = home
        results["LAY_DRAW"] = 1.0 - draw
        
        # HT Unders
        results["UNDER_0.5_HT"] = matrix_ht.get((0,0), 0.0)
        results["UNDER_1.5_HT"] = sum(p for (h,a), p in matrix_ht.items() if h+a < 1.5)
        
        return results

    def blend_probability(self, poisson_prob, market_odd, poisson_weight=0.70):
        if not market_odd or market_odd <= 1.0:
            return poisson_prob
        market_prob = 1.0 / market_odd
        return (poisson_weight * poisson_prob) + ((1.0 - poisson_weight) * market_prob)

    def calculate_ev(self, blended_prob, market_odd):
        if not market_odd or market_odd <= 1.0:
            return 0.0
        return (blended_prob * market_odd) - 1.0

