from web.app import app
import traceback

app.config['TESTING'] = True
client = app.test_client()

try:
    print('Testing / ...')
    resp = client.get('/')
    print('Status / :', resp.status_code)
    if resp.status_code != 200:
        print(resp.data.decode('utf-8'))
except Exception as e:
    traceback.print_exc()

try:
    print('\nTesting /history ...')
    resp = client.get('/history')
    print('Status /history :', resp.status_code)
    if resp.status_code != 200:
        print(resp.data.decode('utf-8'))
except Exception as e:
    traceback.print_exc()
