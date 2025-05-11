from datetime import timedelta, datetime, timezone
from uuid import UUID
from typing import Dict, Any, Optional
import logging

from core.entities.user import User
from core.exceptions.user_exceptions import (
    UserNotFoundError, UserAlreadyExistsError, InvalidCredentialsError,
    MFARequiredError, InvalidMFACodeError, MFAAlreadyEnabledError, MFANotEnabledError
)
from core.interfaces.repositories import UserRepository
from core.interfaces.security import PasswordHasher, TokenService, MFAService

logger = logging.getLogger(__name__)


class RegisterUserUseCase:
    def __init__(self, user_repository: UserRepository, password_hasher: PasswordHasher):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
    
    async def execute(self, email: str, password: str) -> User:
        try:
            existing_user = await self.user_repository.get_by_email(email)
            
            if existing_user:
                logger.warning(f"Tentativa de registro com email já existente: {email}")
                raise UserAlreadyExistsError()
            
            hashed_password = self.password_hasher.hash_password(password)
            
            new_user = User(
                email=email,
                hashed_password=hashed_password,
                is_active=True,
                is_admin=False,
                created_at=datetime.now(timezone.utc)
            )
            
            created_user = await self.user_repository.create(new_user)
            logger.info(f"Usuário criado com sucesso. ID: {created_user.id}")
            return created_user
                
        except UserAlreadyExistsError:
            raise
        except Exception as e:
            logger.error(f"Erro durante registro: {str(e)}")
            raise


class LoginUserUseCase:
    def __init__(
        self, 
        user_repository: UserRepository, 
        password_hasher: PasswordHasher,
        token_service: TokenService,
        access_token_expire_minutes: int
    ):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.access_token_expire_minutes = access_token_expire_minutes
    
    async def execute(self, email: str, password: str) -> dict:
        try:
            user = await self.user_repository.get_by_email(email)
            
            if not user:
                logger.warning(f"Usuário não encontrado: {email}")
                raise InvalidCredentialsError()
            
            if not self.password_hasher.verify_password(password, user.hashed_password):
                logger.warning(f"Senha incorreta: {email}")
                raise InvalidCredentialsError()
            
            expires_delta = timedelta(minutes=self.access_token_expire_minutes)
            token_data = {"sub": str(user.id), "email": user.email}
            
            access_token = self.token_service.create_access_token(
                data=token_data, 
                expires_delta=expires_delta
            )
            
            logger.info(f"Login bem-sucedido: {email}")
            
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
                
        except InvalidCredentialsError:
            raise
        except Exception as e:
            logger.error(f"Erro durante login: {str(e)}")
            raise


class GetUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID) -> User:
        try:
            user = await self.user_repository.get_by_id(user_id)
            
            if not user:
                logger.warning(f"Usuário não encontrado: {user_id}")
                raise UserNotFoundError()
            
            return user
            
        except UserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erro ao buscar usuário: {str(e)}")
            raise


class SetupMFAUseCase:
    def __init__(self, user_repository: UserRepository, mfa_service: MFAService):
        self.user_repository = user_repository
        self.mfa_service = mfa_service
    
    async def execute(self, user_id: UUID) -> dict:
        try:
            user = await self.user_repository.get_by_id(user_id)
            
            if not user:
                logger.warning(f"Usuário não encontrado: {user_id}")
                raise UserNotFoundError()
            
            if user.mfa_enabled:
                logger.warning(f"MFA já habilitado: {user_id}")
                raise MFAAlreadyEnabledError()
            
            mfa_setup_info = await self.mfa_service.setup_mfa(user.email)
            
            user.mfa_secret = mfa_setup_info["secret"]
            await self.user_repository.update(user)
            
            logger.info(f"MFA configurado: {user_id}")
            return mfa_setup_info
                
        except (UserNotFoundError, MFAAlreadyEnabledError):
            raise
        except Exception as e:
            logger.error(f"Erro ao configurar MFA: {str(e)}")
            raise


class VerifyMFAUseCase:
    def __init__(self, user_repository: UserRepository, mfa_service: MFAService):
        self.user_repository = user_repository
        self.mfa_service = mfa_service
    
    async def execute(self, user_id: UUID, code: str) -> bool:
        try:
            user = await self.user_repository.get_by_id(user_id)
            
            if not user:
                logger.warning(f"Usuário não encontrado: {user_id}")
                raise UserNotFoundError()
            
            if not user.mfa_secret:
                logger.warning(f"MFA não configurado: {user_id}")
                raise MFANotEnabledError()
            
            is_valid = await self.mfa_service.verify_code(user.mfa_secret, code)
            
            if not is_valid:
                logger.warning(f"Código MFA inválido: {user_id}")
                raise InvalidMFACodeError()
            
            if not user.mfa_enabled:
                user.mfa_enabled = True
                await self.user_repository.update(user)
                logger.info(f"MFA habilitado: {user_id}")
            
            return True
                
        except (UserNotFoundError, MFANotEnabledError, InvalidMFACodeError):
            raise
        except Exception as e:
            logger.error(f"Erro ao verificar MFA: {str(e)}")
            raise


class DisableMFAUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID) -> bool:
        try:
            user = await self.user_repository.get_by_id(user_id)
            
            if not user:
                logger.warning(f"Usuário não encontrado: {user_id}")
                raise UserNotFoundError()
            
            if not user.mfa_enabled:
                logger.warning(f"MFA não está habilitado: {user_id}")
                raise MFANotEnabledError()
            
            user.mfa_enabled = False
            user.mfa_secret = None
            await self.user_repository.update(user)
            
            logger.info(f"MFA desabilitado: {user_id}")
            return True
                
        except (UserNotFoundError, MFANotEnabledError):
            raise
        except Exception as e:
            logger.error(f"Erro ao desabilitar MFA: {str(e)}")
            raise


class LoginWithMFAUseCase:
    def __init__(
        self, 
        user_repository: UserRepository, 
        password_hasher: PasswordHasher,
        token_service: TokenService,
        mfa_service: MFAService,
        access_token_expire_minutes: int
    ):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.mfa_service = mfa_service
        self.access_token_expire_minutes = access_token_expire_minutes
    
    async def execute(self, email: str, password: str, mfa_code: str) -> dict:
        try:
            user = await self.user_repository.get_by_email(email)
            
            if not user:
                logger.warning(f"Usuário não encontrado: {email}")
                raise InvalidCredentialsError()
            
            if not self.password_hasher.verify_password(password, user.hashed_password):
                logger.warning(f"Senha incorreta: {email}")
                raise InvalidCredentialsError()
            
            if not user.mfa_enabled or not user.mfa_secret:
                logger.warning(f"MFA não habilitado: {email}")
                raise MFANotEnabledError()
            
            is_valid = await self.mfa_service.verify_code(user.mfa_secret, mfa_code)
            
            if not is_valid:
                logger.warning(f"Código MFA inválido: {email}")
                raise InvalidMFACodeError()
            
            expires_delta = timedelta(minutes=self.access_token_expire_minutes)
            token_data = {"sub": str(user.id), "email": user.email}
            
            access_token = self.token_service.create_access_token(
                data=token_data, 
                expires_delta=expires_delta
            )
            
            logger.info(f"Login com MFA bem-sucedido: {email}")
            
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
                
        except (InvalidCredentialsError, MFANotEnabledError, InvalidMFACodeError):
            raise
        except Exception as e:
            logger.error(f"Erro durante login com MFA: {str(e)}")
            raise


class LoginFirstStepUseCase:
    def __init__(
        self, 
        user_repository: UserRepository, 
        password_hasher: PasswordHasher
    ):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
    
    async def execute(self, email: str, password: str) -> UUID:
        try:
            user = await self.user_repository.get_by_email(email)
            
            if not user:
                logger.warning(f"Usuário não encontrado: {email}")
                raise InvalidCredentialsError()
            
            if not self.password_hasher.verify_password(password, user.hashed_password):
                logger.warning(f"Senha incorreta: {email}")
                raise InvalidCredentialsError()
            
            if user.mfa_enabled:
                logger.info(f"MFA requerido: {email}")
                raise MFARequiredError(user.id)
            
            logger.info(f"Primeira etapa do login bem-sucedida: {email}")
            return user.id
                
        except (InvalidCredentialsError, MFARequiredError):
            raise
        except Exception as e:
            logger.error(f"Erro durante primeira etapa do login: {str(e)}")
            raise