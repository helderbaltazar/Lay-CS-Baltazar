import argparse
from web.app import app
from scheduler import start_scheduler
import config

__version__ = "1.0.0"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan-only", action="store_true", help="Rodar scanner de hoje")
    parser.add_argument("--resolve-only", action="store_true", help="Rodar resolver de ontem")
    args = parser.parse_args()
    
    if args.scan_only:
        from scheduler import run_daily_scan
        run_daily_scan()
    elif args.resolve_only:
        from scheduler import run_daily_resolve
        run_daily_resolve()
    else:
        print(f"Iniciando Lay CS Automation v{__version__}")
        print("Iniciando scheduler em background...")
        scheduler = start_scheduler()
        try:
            print(f"Iniciando servidor web na porta {config.PORT}...")
            # Nao usa modo debug para producao, conforme regra de seguranca
            app.run(host="127.0.0.1", port=config.PORT, debug=False)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
