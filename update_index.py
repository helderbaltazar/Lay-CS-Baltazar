with open("web/templates/index.html", "r") as f:
    c = f.read()

c = c.replace(
    '🤖 APROVADO ({{ m.ai_confidence }}% Confiança)',
    '🤖 APROVADO (Score: {{ "%.1f"|format(m.power_score) if m.power_score else 0 }})'
)
c = c.replace(
    '⛔ VETADO ({{ m.ai_confidence }}% Confiança)',
    '⛔ VETADO (Score: {{ "%.1f"|format(m.power_score) if m.power_score else 0 }})'
)

with open("web/templates/index.html", "w") as f:
    f.write(c)

print("index.html atualizado")
