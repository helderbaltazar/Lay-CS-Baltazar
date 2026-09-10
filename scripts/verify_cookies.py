import os
import sys
import json

# Garante que a raiz do projeto esteja no sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

def verify():
    from database.db import SessionLocal
    from database.models_db import SystemConfig
    
    db = SessionLocal()
    try:
        conf = db.query(SystemConfig).filter(SystemConfig.key == 'layback_cookies').first()
        if not conf or not conf.value or conf.value.strip() in ('', '[]', 'null'):
            print('❌ ERRO CRÍTICO: Nenhum cookie Layback encontrado no banco de dados!')
            sys.exit(1)
            
        cookies = json.loads(conf.value)
        if not isinstance(cookies, list) or len(cookies) == 0:
            print('❌ ERRO CRÍTICO: Cookies no banco estão vazios!')
            sys.exit(1)
            
        print(f'✅ Cookies Layback OK — {len(cookies)} cookies encontrados no banco.')
    finally:
        db.close()

if __name__ == '__main__':
    verify()
