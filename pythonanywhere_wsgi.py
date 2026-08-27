import sys
import os

# Adicione o caminho do projeto ao sys.path
project_home = '/home/SEU_USUARIO/Lay-CS-Baltazar'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Carregar variáveis de ambiente do .env, caso não estejam no painel
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Importar o app do Flask
from web.app import app as application
