import subprocess
import os
import urllib.request
import urllib.parse
import json

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({'chat_id': TELEGRAM_CHAT_ID, 'text': text}).encode('utf-8')
    try:
        urllib.request.urlopen(url, data=data, timeout=5)
    except:
        pass

print("Starting Gunicorn via wrapper...")
port = os.getenv("PORT", "10000")
cmd = ["gunicorn", "--bind", f"0.0.0.0:{port}", "web.app:app"]
try:
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    logs = []
    for line in process.stdout:
        print(line, end="")
        logs.append(line)
        if len(logs) > 50:
            logs.pop(0)
    process.wait()
    error_msg = "".join(logs)
    send_telegram(f"🚨 Render Deploy Crash:\n\n{error_msg[-4000:]}")
except Exception as e:
    send_telegram(f"🚨 Wrapper falhou: {str(e)}")
