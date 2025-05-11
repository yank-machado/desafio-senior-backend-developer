import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
import uuid

from core.entities.user import User
from core.exceptions.user_exceptions import UserAlreadyExistsError, InvalidCredentialsError
from core.use_cases.user_use_cases import RegisterUserUseCase, LoginUserUseCase, GetUserUseCase

class TestRegisterUserUseCase:
    @pytest.fixture
    def user_repository_mock(self):
        repository = AsyncMock()
        # Por padrão, get_by_email retorna None (usuário não existe)
        repository.get_by_email.return_value = None
        # Por padrão, create retorna um usuário válido
        repository.create.return_value = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
            is_admin=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        return repository
    
    @pytest.fixture
    def password_hasher_mock(self):
        hasher = MagicMock()
        hasher.hash_password.return_value = "hashed_password"
        hasher.verify_password.return_value = True
        return hasher
    
    @pytest.mark.asyncio
    async def test_register_new_user_success(self, user_repository_mock, password_hasher_mock):
        """Testa se um novo usuário pode ser registrado com sucesso."""
        # Arrange
        use_case = RegisterUserUseCase(user_repository_mock, password_hasher_mock)
        email = "test@example.com"
        password = "test_password"
        
        # Act
        user = await use_case.execute(email, password)
        
        # Assert
        assert user is not None
        assert user.email == email
        assert user.is_active is True
        
        # Verificar se os métodos foram chamados corretamente
        user_repository_mock.get_by_email.assert_called_once_with(email)
        password_hasher_mock.hash_password.assert_called_once_with(password)
        user_repository_mock.create.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_register_existing_user_raises_error(self, user_repository_mock, password_hasher_mock):
        """Testa se um erro é lançado quando tentamos registrar um usuário que já existe."""
        # Arrange
        # Configurando o mock para simular usuário já existente
        existing_user = User(
            id=uuid.uuid4(),
            email="existing@example.com",
            hashed_password="hashed_password",
            is_active=True,
            is_admin=False
        )
        user_repository_mock.get_by_email.return_value = existing_user
        
        use_case = RegisterUserUseCase(user_repository_mock, password_hasher_mock)
        
        # Act & Assert
        with pytest.raises(UserAlreadyExistsError):
            await use_case.execute("existing@example.com", "password")
        
        # Verificar se os métodos foram chamados corretamente
        user_repository_mock.get_by_email.assert_called_once()
        password_hasher_mock.hash_password.assert_not_called()
        user_repository_mock.create.assert_not_called()

class TestLoginUserUseCase:
    @pytest.fixture
    def user_repository_mock(self):
        repository = AsyncMock()
        # Usuário válido para testes
        self.test_user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password="hashed_password",
            is_active=True,
            is_admin=False
        )
        repository.get_by_email.return_value = self.test_user
        return repository
    
    @pytest.fixture
    def password_hasher_mock(self):
        hasher = MagicMock()
        hasher.verify_password.return_value = True
        return hasher
    
    @pytest.fixture
    def token_service_mock(self):
        service = MagicMock()
        service.create_access_token.return_value = "test_token"
        return service
    
    @pytest.mark.asyncio
    async def test_login_valid_credentials(self, user_repository_mock, password_hasher_mock, token_service_mock):
        """Testa se um usuário pode fazer login com credenciais válidas."""
        # Arrange
        use_case = LoginUserUseCase(
            user_repository_mock, 
            password_hasher_mock, 
            token_service_mock, 
            30  # minutos de validade
        )
        
        # Act
        result = await use_case.execute("test@example.com", "correct_password")
        
        # Assert
        assert result is not None
        assert "access_token" in result
        assert result["access_token"] == "test_token"
        assert "token_type" in result
        assert result["token_type"] == "bearer"
        
        # Verificar chamadas de métodos
        user_repository_mock.get_by_email.assert_called_once_with("test@example.com")
        password_hasher_mock.verify_password.assert_called_once_with("correct_password", "hashed_password")
        token_service_mock.create_access_token.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_invalid_email(self, user_repository_mock, password_hasher_mock, token_service_mock):
        """Testa se um erro é lançado quando o email não existe no sistema."""
        # Arrange
        user_repository_mock.get_by_email.return_value = None
        use_case = LoginUserUseCase(
            user_repository_mock, 
            password_hasher_mock, 
            token_service_mock, 
            30
        )
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            await use_case.execute("wrong@example.com", "any_password")
        
        # Verificar chamadas de métodos
        user_repository_mock.get_by_email.assert_called_once_with("wrong@example.com")
        password_hasher_mock.verify_password.assert_not_called()
        token_service_mock.create_access_token.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, user_repository_mock, password_hasher_mock, token_service_mock):
        """Testa se um erro é lançado quando a senha está incorreta."""
        # Arrange
        password_hasher_mock.verify_password.return_value = False
        use_case = LoginUserUseCase(
            user_repository_mock, 
            password_hasher_mock, 
            token_service_mock, 
            30
        )
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsError):
            await use_case.execute("test@example.com", "wrong_password")
        
        # Verificar chamadas de métodos
        user_repository_mock.get_by_email.assert_called_once_with("test@example.com")
        password_hasher_mock.verify_password.assert_called_once()
        token_service_mock.create_access_token.assert_not_called() 