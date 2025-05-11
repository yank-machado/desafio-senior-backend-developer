import subprocess
import sys
from utils import print_header, print_info, print_success, print_error, check_docker

def stop_all_services():
    print_header("Parando todos os serviços Docker...")
    try:
        subprocess.run(["docker-compose", "down"], check=True)
        print_success("Todos os serviços foram parados com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Erro ao parar os serviços: {e}")
        return False

def stop_database():
    print_header("Parando o serviço de banco de dados...")
    try:
        subprocess.run(["docker-compose", "stop", "db"], check=True)
        print_success("Banco de dados parado com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Erro ao parar o banco de dados: {e}")
        return False

def main():
    print_header("=== Utilitário para parar serviços da Carteira Digital ===")
    
    if not check_docker():
        print_error("Não é possível parar os serviços sem o Docker em execução.")
        sys.exit(1)
    
    print_info("Escolha uma opção:")
    print("1. Parar todos os serviços (docker-compose down)")
    print("2. Parar apenas o banco de dados (docker-compose stop db)")
    print("3. Sair sem fazer nada")
    
    choice = input("\nOpção [1-3]: ")
    
    if choice == "1":
        stop_all_services()
    elif choice == "2":
        stop_database()
    elif choice == "3":
        print_info("Nenhuma ação realizada.")
    else:
        print_error("Opção inválida!")
    
    print_header("=== Operação concluída ===")

if __name__ == "__main__":
    main() 