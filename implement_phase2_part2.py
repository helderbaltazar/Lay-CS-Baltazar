import os

# 1. Update config.py to load new vars
with open('config.py', 'r') as f:
    config_content = f.read()

new_config = """
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
BANKROLL = float(os.getenv('BANKROLL', '1000.0'))
MAX_LIABILITY = float(os.getenv('MAX_LIABILITY', '2.0')) # Em %
"""
if "TELEGRAM_BOT_TOKEN" not in config_content:
    config_content += new_config
    with open('config.py', 'w') as f:
        f.write(config_content)
    print("Variáveis de configuração atualizadas.")

# 2. Update .env.example
with open('.env.example', 'a') as f:
    f.write("\n# Fase 2 Configs\nTELEGRAM_BOT_TOKEN=seu_token_aqui\nTELEGRAM_CHAT_ID=seu_chat_id_aqui\nBANKROLL=1000.0\nMAX_LIABILITY=2.0\n")

# 3. Create notifications/telegram.py
os.makedirs('notifications', exist_ok=True)
telegram_code = """import requests
import config

def send_message(text):
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        return False
        
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': config.TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }
    try:
        r = requests.post(url, json=payload, timeout=5)
        return r.status_code == 200
    except Exception as e:
        print(f"Erro ao enviar mensagem Telegram: {e}")
        return False

def send_document(file_path, caption=""):
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        return False
        
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': config.TELEGRAM_CHAT_ID, 'caption': caption}
            r = requests.post(url, files=files, data=data, timeout=10)
            return r.status_code == 200
    except Exception as e:
        print(f"Erro ao enviar documento Telegram: {e}")
        return False
"""
with open('notifications/telegram.py', 'w') as f:
    f.write(telegram_code)
print("Módulo Telegram criado.")

# 4. Create database/backup.py
backup_code = """import os
import datetime
from notifications.telegram import send_document

def run_backup():
    db_path = 'data_store/database.sqlite3'
    if not os.path.exists(db_path):
        print("Banco de dados não encontrado para backup.")
        return False
        
    now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    caption = f"📦 Backup Automático Lay CS - {now_str}"
    
    success = send_document(db_path, caption)
    if success:
        print(f"Backup enviado via Telegram com sucesso em {now_str}.")
    else:
        print("Falha ao enviar backup.")
    return success
"""
with open('database/backup.py', 'w') as f:
    f.write(backup_code)
print("Módulo de Backup criado.")

