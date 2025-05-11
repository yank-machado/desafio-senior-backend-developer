import subprocess
import os
from datetime import datetime

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"{Colors.HEADER}{Colors.BOLD}[{timestamp}] {text}{Colors.ENDC}")

def print_info(text):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"{Colors.BLUE}[{timestamp}] {text}{Colors.ENDC}")

def print_success(text):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"{Colors.GREEN}[{timestamp}] {text}{Colors.ENDC}")

def print_warning(text):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"{Colors.YELLOW}[{timestamp}] {text}{Colors.ENDC}")

def print_error(text):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"{Colors.RED}[{timestamp}] {text}{Colors.ENDC}")

def check_docker():
    print_info("Verificando status do Docker...")
    try:
        subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print_success("Docker está rodando!")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("Docker não está rodando ou não está instalado!")
        return False 