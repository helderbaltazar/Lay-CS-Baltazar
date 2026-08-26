import os
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
