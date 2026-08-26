with open('tests/unit/test_scanner.py', 'r') as f:
    content = f.read()

old_mock = """    results = [
        {'fixture_id': 1, 'probabilities': {'0-1': 0.10}},
        {'fixture_id': 2, 'probabilities': {'0-1': 0.05}}
    ]"""
    
new_mock = """    results = [
        {'fixture_id': 1, 'date': '2026-08-25', 'status': 'NS', 'league': 'L', 'home': 'A', 'away': 'B', 'lambda_home': 1, 'lambda_away': 1, 'probabilities': {'0-1': 0.10}},
        {'fixture_id': 2, 'date': '2026-08-25', 'status': 'NS', 'league': 'L', 'home': 'C', 'away': 'D', 'lambda_home': 1, 'lambda_away': 1, 'probabilities': {'0-1': 0.05}}
    ]"""

if old_mock in content:
    content = content.replace(old_mock, new_mock)
    with open('tests/unit/test_scanner.py', 'w') as f:
        f.write(content)
    print("Mock in test_scanner.py fixed.")
else:
    print("Could not find the old mock.")
