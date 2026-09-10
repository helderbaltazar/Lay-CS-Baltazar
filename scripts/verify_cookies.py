import os
import sys
import json

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
