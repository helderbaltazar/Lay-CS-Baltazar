import os
import requests
import datetime
import psycopg2

def send_telegram(msg):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": msg})

def check():
    db_url = os.getenv("DATABASE_URL")
    if not db_url: return
    
    today = datetime.datetime.utcnow().date()
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM matches WHERE DATE(date) = %s", (today,))
        count = cur.fetchone()[0]
        
        if count == 0:
            send_telegram(f"🚨 DEAD MAN'S SWITCH 🚨\nNenhuma partida foi processada ou injetada hoje ({today}) no banco de dados! A pipeline principal pode estar quebrada de forma silenciosa.")
        else:
            print(f"Health OK: {count} partidas no banco hoje.")
            
        cur.close()
        conn.close()
    except Exception as e:
        send_telegram(f"🚨 DEAD MAN'S SWITCH 🚨\nFalha ao checar saúde do banco de dados Lay CS: {e}")

if __name__ == "__main__":
    check()
