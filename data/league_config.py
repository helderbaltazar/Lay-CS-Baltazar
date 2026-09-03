MAIN_LEAGUES = {
    39: {"name": "Premier League", "country": "England", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    140: {"name": "La Liga", "country": "Spain", "flag": "🇪🇸"},
    135: {"name": "Serie A", "country": "Italy", "flag": "🇮🇹"},
    78: {"name": "Bundesliga", "country": "Germany", "flag": "🇩🇪"},
    61: {"name": "Ligue 1", "country": "France", "flag": "🇫🇷"},
    94: {"name": "Primeira Liga", "country": "Portugal", "flag": "🇵🇹"},
    88: {"name": "Eredivisie", "country": "Netherlands", "flag": "🇳🇱"},
    144: {"name": "Jupiler Pro League", "country": "Belgium", "flag": "🇧🇪"},
    203: {"name": "Super Lig", "country": "Turkey", "flag": "🇹🇷"},
    307: {"name": "Saudi Pro League", "country": "Saudi Arabia", "flag": "🇸🇦"},
    71: {"name": "Brasileirão Série A", "country": "Brazil", "flag": "🇧🇷"},
    72: {"name": "Brasileirão Série B", "country": "Brazil", "flag": "🇧🇷"},
    128: {"name": "Liga Profesional", "country": "Argentina", "flag": "🇦🇷"},
    262: {"name": "Liga MX", "country": "Mexico", "flag": "🇲🇽"},
    253: {"name": "MLS", "country": "USA", "flag": "🇺🇸"},
    2: {"name": "Champions League", "country": "Europe", "flag": "🇪🇺"},
    3: {"name": "Europa League", "country": "Europe", "flag": "🇪🇺"},
    848: {"name": "Conference League", "country": "Europe", "flag": "🇪🇺"},
    13: {"name": "Copa Libertadores", "country": "South America", "flag": "🌎"},
    11: {"name": "Copa Sudamericana", "country": "South America", "flag": "🌎"},
    73: {"name": "Copa do Brasil", "country": "Brazil", "flag": "🇧🇷"},
    1: {"name": "World Cup", "country": "World", "flag": "🌍"},
    15: {"name": "Copa America", "country": "South America", "flag": "🌎"}
}

LEAGUE_AVERAGES = {
    307: (1.45, 1.10),
    140: (1.50, 1.15),
    72: (1.25, 1.00),
    71: (1.35, 1.10),
    73: (1.30, 1.05),
    13: (1.40, 1.10),
    2: (1.50, 1.15),
    88: (1.60, 1.20),
    39: (1.55, 1.20),
    135: (1.35, 1.15),
    78: (1.65, 1.25),
    61: (1.40, 1.15),
    94: (1.50, 1.10),
    144: (1.45, 1.15),
    203: (1.50, 1.15),
    128: (1.25, 1.05),
    262: (1.45, 1.15),
    253: (1.55, 1.20),
    3: (1.45, 1.15),
    848: (1.40, 1.10),
    11: (1.35, 1.05),
    1: (1.40, 1.10),
    15: (1.30, 1.05)
}

DOMESTIC_LEAGUE_MAP = {
    # Cruzeiro and Atletico em copas (e.g. Copa do Brasil)
    135: 71,
    1062: 71
}

def get_league_avg(league_id):
    return LEAGUE_AVERAGES.get(league_id, (1.40, 1.10))
