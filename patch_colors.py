with open('analysis/scanner.py', 'r') as f:
    content = f.read()

old_pred = """            pred.probability = rec['probability']
            pred.rank = rec['rank']"""
            
new_pred = """            pred.probability = rec['probability']
            pred.rank = rec['rank']
            
            if match.status in ['FT', 'AET', 'PEN'] and match.real_score:
                pred.is_hit = (match.real_score != target)"""

content = content.replace(old_pred, new_pred)
with open('analysis/scanner.py', 'w') as f:
    f.write(content)

with open('web/app.py', 'r') as f:
    app_content = f.read()

old_app = """                    'real_score': m.real_score,
                    'probability': p.probability
                })"""
new_app = """                    'real_score': m.real_score,
                    'probability': p.probability,
                    'is_hit': p.is_hit
                })"""
app_content = app_content.replace(old_app, new_app)
with open('web/app.py', 'w') as f:
    f.write(app_content)

with open('web/templates/index.html', 'r') as f:
    html = f.read()

old_html = """                {% if m.status == 'FT' %}
                    {{ m.real_score }}
                {% else %}"""
new_html = """                {% if m.status == 'FT' %}
                    {% if m.is_hit == True %}
                        <span class="green">{{ m.real_score }} ✅ GREEN</span>
                    {% elif m.is_hit == False %}
                        <span class="red">{{ m.real_score }} ❌ RED</span>
                    {% else %}
                        {{ m.real_score }}
                    {% endif %}
                {% else %}"""
html = html.replace(old_html, new_html)
with open('web/templates/index.html', 'w') as f:
    f.write(html)

print("Patch applied.")
