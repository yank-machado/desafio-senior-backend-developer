import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.entities.user import User
from core.interfaces.repositories import UserRepository
from core.interfaces.security import PasswordHasher, TokenService
from infrastucture.api.routers.auth import router
from infrastucture.api.dtos.user_dtos import UserCreate, UserLogin


@pytest.fixture
def mock_user_repository():
    repository = AsyncMock(spec=UserRepository)
    return repository


@pytest.fixture
def mock_password_hasher():
    hasher = MagicMock(spec=PasswordHasher)
    hasher.hash_password.return_value = "hashed_password"
    hasher.verify_password.return_value = True
    return hasher


@pytest.fixture
def mock_token_service():
    service = MagicMock(spec=TokenService)
    service.create_access_token.return_value = "jwt_token"
    return service


@pytest.fixture
def sample_user():
    return User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_admin=False,
        created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def client(mock_user_repository, mock_password_hasher, mock_token_service):
    # Criar um app FastAPI para testar as rotas
    app = FastAPI()
    app.include_router(router)
    
    # Substituir as dependências por mocks
    async def override_get_db():
        yield None
    
    # Configurar os patches para os mocks
    with patch("infrastucture.api.routers.auth.SQLAlchemyUserRepository", return_value=mock_user_repository), \
         patch("infrastucture.api.routers.auth.BCryptPasswordHasher", return_value=mock_password_hasher), \
         patch("infrastucture.api.routers.auth.JWTTokenService", return_value=mock_token_service), \
         patch("infrastucture.api.routers.auth.get_db", side_effect=override_get_db):
        # Criar um cliente de teste
        client = TestClient(app)
        yield client


class TestAuthRouter:
    def test_register_success(self, client, mock_user_repository, sample_user, mock_token_service):
        # Configurar mocks
        mock_user_repository.get_by_email.return_value = None
        mock_user_repository.create.return_value = sample_user
        mock_token_service.create_access_token.return_value = "jwt_token"
        
        # Executar requisição
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": "password123"}
        )
        
        # Verificar resultado
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] == "jwt_token"
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
        # Verificar chamadas aos mocks
        # O método get_by_email é chamado duas vezes durante o fluxo de registro
        assert mock_user_repository.get_by_email.call_count == 2
        mock_user_repository.create.assert_called_once()

    def test_register_user_already_exists(self, client, mock_user_repository, sample_user):
        # Configurar mocks
        mock_user_repository.get_by_email.return_value = sample_user
        
        # Executar requisição
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": "password123"}
        )
        
        # Verificar resultado
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        
        # Verificar chamadas aos mocks
        mock_user_repository.get_by_email.assert_called_once_with("test@example.com")
        mock_user_repository.create.assert_not_called()

    def test_login_success(self, client, mock_user_repository, sample_user, mock_token_service):
        # Configurar mocks
        mock_user_repository.get_by_email.return_value = sample_user
        mock_token_service.create_access_token.return_value = "jwt_token"
        
        # Executar requisição
        response = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "password123"}
        )
        
        # Verificar resultado
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] == "jwt_token"
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
        # Verificar chamadas aos mocks
        mock_user_repository.get_by_email.assert_called_once_with("test@example.com")

    def test_login_invalid_credentials(self, client, mock_user_repository, mock_password_hasher):
        # Configurar mocks
        mock_user_repository.get_by_email.return_value = None
        
        # Executar requisição
        response = client.post(
            "/auth/login",
            json={"email": "wrong@example.com", "password": "password123"}
        )
        
        # Verificar resultado
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        
        # Verificar chamadas aos mocks
        mock_user_repository.get_by_email.assert_called_once_with("wrong@example.com") 