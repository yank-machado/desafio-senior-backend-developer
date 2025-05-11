import pytest
import pytest_asyncio
import asyncio
import os
from fastapi.testclient import TestClient
from httpx import AsyncClient
import uuid
from dotenv import load_dotenv
from sqlalchemy import text

from main import app
from infrastucture.database.base import engine, Base, async_session
from infrastucture.database.init_db import init_db

# Carregar variáveis de ambiente para testes
load_dotenv()

# Cliente de teste
client = TestClient(app)

# Dados para testes
test_user_email = f"test_{uuid.uuid4()}@example.com"
test_user_password = "Test@123456"

@pytest_asyncio.fixture(scope="module")
async def setup_database():
    """Configura o banco de dados para testes."""
    # Criar todas as tabelas
    async with engine.begin() as conn:
        # Limpar qualquer tabela existente
        await conn.execute(text("DROP TABLE IF EXISTS transport_cards CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS documents CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS documenttype CASCADE"))
        
        # Criar tabelas
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Limpar após os testes
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS transport_cards CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS documents CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        await conn.execute(text("DROP TYPE IF EXISTS documenttype CASCADE"))

@pytest.mark.skip("Teste que requer API rodando localmente")
@pytest.mark.asyncio
async def test_register_and_login_flow(setup_database):
    """Testa o fluxo completo de registro e login de usuário."""
    # Registrar um novo usuário
    base_url = "http://localhost:8000"
    async with AsyncClient(base_url=base_url) as ac:
        register_data = {
            "email": test_user_email,
            "password": test_user_password
        }
        
        # Usar o caminho absoluto em vez de variável de ambiente
        response = await ac.post("/api/v1/auth/register", json=register_data)
        
        # Verificar resposta de registro
        assert response.status_code == 201, f"Erro ao registrar usuário: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
        # Tentar registrar o mesmo usuário novamente (deve falhar)
        response = await ac.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 409, "Deveria falhar ao registrar usuário duplicado"
        
        # Fazer login com o usuário registrado
        login_data = {
            "email": test_user_email,
            "password": test_user_password
        }
        
        response = await ac.post("/api/v1/auth/login", json=login_data)
        # Verificar resposta de login
        assert response.status_code == 200, f"Erro ao fazer login: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
        # Fazer login com credenciais inválidas
        invalid_login_data = {
            "email": test_user_email,
            "password": "senha_errada"
        }
        
        response = await ac.post("/api/v1/auth/login", json=invalid_login_data)
        assert response.status_code == 401, "Login com senha incorreta deveria falhar"

@pytest.mark.skip("Teste que requer API rodando localmente")
@pytest.mark.asyncio
async def test_register_input_validation(setup_database):
    """Testa a validação de entrada dos dados de registro."""
    base_url = "http://localhost:8000"
    async with AsyncClient(base_url=base_url) as ac:
        # Email inválido
        invalid_email_data = {
            "email": "email_invalido",
            "password": test_user_password
        }
        
        # Usar o caminho absoluto em vez de variável de ambiente
        response = await ac.post("/api/v1/auth/register", json=invalid_email_data)
        assert response.status_code in [400, 422], "Registro com email inválido deveria falhar"
        
        # Senha muito curta
        short_password_data = {
            "email": f"outro_{uuid.uuid4()}@example.com",
            "password": "123"
        }
        
        response = await ac.post("/api/v1/auth/register", json=short_password_data)
        assert response.status_code in [400, 422], "Registro com senha muito curta deveria falhar"
        
        # Dados faltando
        missing_data = {
            "email": f"outro_{uuid.uuid4()}@example.com"
        }
        
        response = await ac.post("/api/v1/auth/register", json=missing_data)
        assert response.status_code in [400, 422], "Registro com dados faltando deveria falhar" 