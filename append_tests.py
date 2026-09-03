with open('tests/web/test_ui.py', 'a') as f:
    f.write("""
def test_deep_analysis_modal_exists(client):
    from web.app import config
    import base64
    username = config.DASHBOARD_USERNAME
    password = config.DASHBOARD_PASSWORD
    token = base64.b64encode(f"{username}:{password}".encode('utf-8')).decode('utf-8')
    response = client.get('/', headers={'Authorization': f'Basic {token}'})
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert 'id="aiModal"' in html
    assert 'class="modal-overlay"' in html
    assert 'openDeepAnalysis' in html

def test_api_analysis_route(client):
    from web.app import config
    import base64
    username = config.DASHBOARD_USERNAME
    password = config.DASHBOARD_PASSWORD
    token = base64.b64encode(f"{username}:{password}".encode('utf-8')).decode('utf-8')
    response = client.get('/api/analysis?home=Palmeiras&away=Santos&league=Brasileirao', headers={'Authorization': f'Basic {token}'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'momentos_gols' in data
    assert 'placares_perigosos' in data
    assert 'motivacao' in data
    assert 'lesoes' in data
    assert 'analise_geral' in data
""")
