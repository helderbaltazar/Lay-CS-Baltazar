import re

with open('analysis/ai_analyst.py', 'r') as f:
    content = f.read()
# Replace analyze_match with orchestrate_match in analyze_top_rankings
content = content.replace("analysis = cls.analyze_match(match, target_score, prob)", "analysis = cls.orchestrate_match(match, target_score, prob)")
with open('analysis/ai_analyst.py', 'w') as f:
    f.write(content)

with open('tests/unit/test_ai_analyst.py', 'r') as f:
    content = f.read()
content = content.replace("AIAnalyst.analyze_match(", "AIAnalyst.orchestrate_match(")
content = content.replace("assert 'Clima: Clear' in res['fator_critico']", "assert res['veredito'] == 'APROVADO'")
with open('tests/unit/test_ai_analyst.py', 'w') as f:
    f.write(content)

