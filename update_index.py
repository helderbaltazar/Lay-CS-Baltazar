import os

with open('web/templates/index.html', 'r') as f:
    idx = f.read()

old_click = "onclick=\"openDeepAnalysis('{{ m.home }}', '{{ m.away }}', '{{ m.league }}')\""
new_click = "onclick=\"openDeepAnalysis('{{ m.home }}', '{{ m.away }}', '{{ m.league }}', '{{ m.fixture_id }}')\""
idx = idx.replace(old_click, new_click)

old_js_def = "function openDeepAnalysis(h, a, l) {"
new_js_def = "function openDeepAnalysis(h, a, l, fid) {"
idx = idx.replace(old_js_def, new_js_def)

old_fetch = "fetch(`/api/analysis?home=${encodeURIComponent(h)}&away=${encodeURIComponent(a)}&league=${encodeURIComponent(l)}`)"
new_fetch = "fetch(`/api/analysis?home=${encodeURIComponent(h)}&away=${encodeURIComponent(a)}&league=${encodeURIComponent(l)}&fixture_id=${fid}`)"
idx = idx.replace(old_fetch, new_fetch)

with open('web/templates/index.html', 'w') as f:
    f.write(idx)
