import pytest
import pytest_asyncio
import asyncio
import os
from dotenv import load_dotenv
from httpx import AsyncClient
import uuid

from main import app
from infrastucture.database.base import engine, async_session, Base
from infrastucture.database.models import UserModel
from sqlalchemy import text


# Carrega variáveis de ambiente
load_dotenv()

# Configurar variáveis de ambiente para testes
os.environ["TESTING"] = "True"
os.environ["DB_HOST"] = "localhost"

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
async def db_session():
    """Fornece uma sessão do banco de dados para testes."""
    async with async_session() as session:
        yield session
        await session.rollback()  # Garantir rollback em vez de commit

@pytest_asyncio.fixture
async def client():
    """Fornece um cliente HTTP para testes."""
    base_url = "http://localhost:8000"
    async with AsyncClient(base_url=base_url) as ac:
        yield ac

@pytest.mark.skip("Teste que depende do banco de dados")
@pytest.mark.asyncio
async def test_create_user_in_db(setup_database, db_session):
    """Testa a criação de um usuário diretamente no banco de dados."""
    # Dados do usuário de teste
    email = f"test_{uuid.uuid4()}@example.com"
    hashed_password = "hashedpassword123"
    
    # Criar usuário diretamente no banco
    user = UserModel(
        email=email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Verificar se o usuário foi criado
    result = await db_session.get(UserModel, user.id)
    assert result is not None
    assert result.email == email
    assert result.hashed_password == hashed_password 