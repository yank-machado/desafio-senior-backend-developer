import asyncio
import pytest
import pytest_asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from httpx import AsyncClient

from main import app
from infrastucture.database.base import engine, Base, async_session
from infrastucture.database.init_db import init_db

# Carregar variáveis de ambiente para testes
load_dotenv()

# Configurações para testes
os.environ["TESTING"] = "True"
os.environ["DB_HOST"] = "localhost"

# Configurações para teste - Usar as mesmas credenciais do docker-compose.yml
DB_USER = "carteira"
DB_PASSWORD = "carteira123"
DB_HOST = "localhost"  # Usar localhost para testes locais
DB_PORT = "5432"
DB_NAME = "carteira_db"

CONNECTION_STRING = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

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

@pytest_asyncio.fixture
async def test_db_session():
    """Fornece uma sessão do banco de dados para testes."""
    # Usar a mesma conexão para todos os testes nessa sessão
    async with async_session() as session:
        yield session
        await session.rollback()  # Garantir rollback em vez de commit

@pytest.mark.skip("Teste que depende do banco de dados")
@pytest.mark.asyncio
async def test_database_connection(test_db_session):
    """Testa se a conexão com o banco de dados está funcionando."""
    # Testar conexão executando uma query simples
    result = await test_db_session.execute(text("SELECT 1"))
    value = result.scalar()
    assert value == 1, "A conexão com o banco de dados falhou"

@pytest.mark.skip("Teste que depende do banco de dados")
@pytest.mark.asyncio
async def test_database_tables(setup_database, test_db_session):
    """Testa se as tabelas principais existem no banco de dados."""
    # Verificar se as tabelas foram criadas corretamente
    await test_db_session.execute(text("SELECT 1 FROM users LIMIT 1"))
    await test_db_session.execute(text("SELECT 1 FROM documents LIMIT 1"))
    await test_db_session.execute(text("SELECT 1 FROM transport_cards LIMIT 1"))
    
    # Se chegamos aqui sem erro, o teste passa
    assert True, "Tabelas não foram criadas corretamente"

@pytest.mark.skip("Teste que depende do banco de dados")
@pytest.mark.asyncio
async def test_user_table_columns(setup_database, test_db_session):
    """Testa se a tabela de usuários possui todas as colunas esperadas."""
    result = await test_db_session.execute(
        text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users'
        """)
    )
    columns = [row[0] for row in result.fetchall()]
    expected_columns = [
        "id", "email", "hashed_password", "is_active",
        "is_admin", "created_at", "updated_at", "mfa_enabled", "mfa_secret"
    ]
    for column in expected_columns:
        assert column in columns, f"Coluna {column} não encontrada na tabela users"

@pytest.mark.skip("Teste que depende do banco de dados")
@pytest.mark.asyncio
async def test_db_connection():
    """Teste de conexão direta com o banco de dados."""
    # Abrir uma conexão
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
        
@pytest.mark.skip("Teste que depende do banco de dados")
@pytest.mark.asyncio
async def test_health_db_endpoint_integration():
    """Testa a integração do endpoint de health com o banco de dados."""
    # Fazer um teste direto no banco de dados para verificar a conexão
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1

@pytest.mark.skip("Não foi possível testar a função get_db diretamente")
@pytest.mark.asyncio
async def test_get_db_session():
    """Testa se a função get_db retorna uma sessão válida."""
    from infrastucture.database.session import get_db
    
    # Isso deve ser testado de forma diferente, usando um mock ou fixture especial
    # Este teste é apenas um placeholder
    assert True

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 