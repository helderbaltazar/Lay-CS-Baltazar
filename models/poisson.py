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
