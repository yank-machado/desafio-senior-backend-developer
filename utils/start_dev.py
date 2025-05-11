import asyncio
import os
import signal
import subprocess
import sys
import time
from utils import print_header, print_info, print_success, print_warning, print_error, check_docker

def check_env_file():
    print_info("Verificando arquivo .env...")
    
    if not os.path.exists(".env"):
        print_warning("Arquivo .env não encontrado!")
        
        if os.path.exists(".env.example"):
            print_info("Copiando .env.example para .env...")
            with open(".env.example", "r") as example:
                with open(".env", "w") as env:
                    env.write(example.read())
            print_success("Arquivo .env criado a partir do .env.example")
        else:
            print_error("Nenhum arquivo .env.example encontrado!")
            print_info("Criando arquivo .env básico...")
            
            with open(".env", "w") as env:
                env.write("""# Configurações de Banco de Dados
DB_USER=carteira
DB_PASSWORD=carteira123
DB_HOST=localhost
DB_PORT=5432
DB_NAME=carteira_db

# Configurações de Segurança
SECRET_KEY=supersecretkey
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configurações da API
API_V1_STR=/api/v1
DEBUG=True

# Configurações do Google OAuth
GOOGLE_CLIENT_ID=seu_google_client_id
GOOGLE_CLIENT_SECRET=seu_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/oauth/google/callback

# Configurações do Facebook OAuth
FACEBOOK_CLIENT_ID=seu_facebook_client_id
FACEBOOK_CLIENT_SECRET=seu_facebook_client_secret
FACEBOOK_REDIRECT_URI=http://localhost:8000/api/v1/oauth/facebook/callback

# URL de redirecionamento frontend após autenticação
FRONTEND_REDIRECT_URL=http://localhost:3000/auth/callback
""")
            print_success("Arquivo .env básico criado!")
    else:
        print_success("Arquivo .env encontrado!")
        
        with open(".env", "r") as env_file:
            env_content = env_file.read()
            
        missing_configs = []
        oauth_configs = [
            "GOOGLE_CLIENT_ID", 
            "GOOGLE_CLIENT_SECRET", 
            "GOOGLE_REDIRECT_URI",
            "FACEBOOK_CLIENT_ID", 
            "FACEBOOK_CLIENT_SECRET", 
            "FACEBOOK_REDIRECT_URI",
            "FRONTEND_REDIRECT_URL"
        ]
        
        for config in oauth_configs:
            if config not in env_content:
                missing_configs.append(config)
        
        if missing_configs:
            print_warning(f"Configurações OAuth faltando no arquivo .env: {', '.join(missing_configs)}")
            print_info("Adicionando configurações OAuth faltantes ao arquivo .env...")
            
            with open(".env", "a") as env_file:
                env_file.write("\n\n# Configurações OAuth adicionadas automaticamente\n")
                
                if "GOOGLE_CLIENT_ID" not in env_content:
                    env_file.write("GOOGLE_CLIENT_ID=seu_google_client_id\n")
                if "GOOGLE_CLIENT_SECRET" not in env_content:
                    env_file.write("GOOGLE_CLIENT_SECRET=seu_google_client_secret\n")
                if "GOOGLE_REDIRECT_URI" not in env_content:
                    env_file.write("GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/oauth/google/callback\n")
                
                if "FACEBOOK_CLIENT_ID" not in env_content:
                    env_file.write("FACEBOOK_CLIENT_ID=seu_facebook_client_id\n")
                if "FACEBOOK_CLIENT_SECRET" not in env_content:
                    env_file.write("FACEBOOK_CLIENT_SECRET=seu_facebook_client_secret\n")
                if "FACEBOOK_REDIRECT_URI" not in env_content:
                    env_file.write("FACEBOOK_REDIRECT_URI=http://localhost:8000/api/v1/oauth/facebook/callback\n")
                
                if "FRONTEND_REDIRECT_URL" not in env_content:
                    env_file.write("FRONTEND_REDIRECT_URL=http://localhost:3000/auth/callback\n")
            
            print_success("Configurações OAuth adicionadas ao arquivo .env!")

def start_database():
    print_header("Iniciando banco de dados PostgreSQL...")
    try:
        subprocess.run(["docker-compose", "up", "-d", "db"], check=True)
        print_success("Banco de dados PostgreSQL iniciado!")
        
        print_info("Aguardando inicialização do banco de dados...")
        time.sleep(5)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Erro ao iniciar o banco de dados: {e}")
        return False

async def init_database():
    print_header("Inicializando estrutura do banco de dados...")
    try:
        env = os.environ.copy()
        current_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env["PYTHONPATH"] = current_path
        
        subprocess.run([sys.executable, "infrastucture/database/init_db.py"], env=env, check=True)
        print_success("Estrutura do banco de dados inicializada com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Erro ao inicializar estrutura do banco de dados: {e}")
        return False

def start_api():
    print_header("Iniciando API Carteira Digital...")
    try:
        env = os.environ.copy()
        current_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env["PYTHONPATH"] = current_path
        
        api_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            env=env
        )
        
        print_success("API iniciada com sucesso em http://localhost:8000")
        print_info("Documentação disponível em http://localhost:8000/docs")
        
        return api_process
    except Exception as e:
        print_error(f"Erro ao iniciar API: {e}")
        return None

async def main():
    print_header("=== Iniciando ambiente de desenvolvimento da Carteira Digital ===")
    
    check_env_file()
    
    docker_running = check_docker()
    
    if docker_running:
        db_started = start_database()
    else:
        print_warning("Usando configurações de banco de dados existentes (verifique o arquivo .env)")
        db_started = True
    
    if db_started:
        db_initialized = await init_database()
    else:
        print_error("Pulando inicialização do banco de dados devido a erros anteriores.")
        db_initialized = False
    
    api_process = None
    if db_initialized:
        api_process = start_api()
    else:
        print_warning("Tentando iniciar API mesmo com problemas no banco de dados...")
        api_process = start_api()
    
    if api_process:
        def signal_handler(sig, frame):
            print_header("\nDesligando serviços...")
            if api_process:
                print_info("Finalizando API...")
                api_process.terminate()
                api_process.wait()
            
            if docker_running:
                print_info("Mantendo o banco de dados em execução...")
            
            print_success("Ambiente de desenvolvimento finalizado!")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        print_header("Pressione Ctrl+C para encerrar os serviços")
        
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_header("\nPrograma interrompido pelo usuário") 