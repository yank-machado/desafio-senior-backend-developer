from fastapi import APIRouter, Depends, HTTPException, status, Body, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
import os
import logging
from typing import Optional
from uuid import UUID
from dotenv import load_dotenv
from datetime import timedelta

from infrastucture.api.dtos.user_dtos import (
    UserCreate, UserLogin, TokenResponse, 
    MFASetupResponse, MFAVerifyRequest, MFAVerifyResponse,
    MFALoginRequest
)
from infrastucture.database.session import get_db
from infrastucture.database.models import UserModel
from infrastucture.repositories.user_repository import SQLAlchemyUserRepository
from infrastucture.security.password import BCryptPasswordHasher
from infrastucture.security.token import JWTTokenService
from infrastucture.security.mfa import PyOTPMFAService
from infrastucture.security.dependencies import get_current_user
from core.use_cases.user_use_cases import (
    RegisterUserUseCase, LoginUserUseCase, 
    SetupMFAUseCase, VerifyMFAUseCase, DisableMFAUseCase, 
    LoginWithMFAUseCase, LoginFirstStepUseCase
)
from core.exceptions.user_exceptions import (
    UserAlreadyExistsError, InvalidCredentialsError, 
    MFARequiredError, InvalidMFACodeError, MFAAlreadyEnabledError, MFANotEnabledError
)
from core.entities.user import User

logger = logging.getLogger(__name__)

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        logger.info(f"Iniciando registro para: {user_data.email}")
        
        user_repository = SQLAlchemyUserRepository(db)
        password_hasher = BCryptPasswordHasher()
        token_service = JWTTokenService()
        
        register_use_case = RegisterUserUseCase(user_repository, password_hasher)
        
        user = await register_use_case.execute(user_data.email, user_data.password)
        logger.info(f"Usuário registrado: ID={user.id}")
        
        expires_delta = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = token_service.create_access_token(
            data=token_data,
            expires_delta=expires_delta
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    except UserAlreadyExistsError as e:
        logger.warning(f"Conflito - Usuário já existe: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro no registro: {str(e)}")
        
        error_type = type(e).__name__
        error_msg = str(e)
        
        if "asyncpg" in error_type.lower() or "connection" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro de conexão com o banco de dados: {error_msg}"
            )
        elif "sqlalchemy" in error_type.lower():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro na operação do banco de dados: {error_msg}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro interno do servidor: {error_msg}"
            )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    try:
        logger.info(f"Tentativa de login: {login_data.email}")
        
        user_repository = SQLAlchemyUserRepository(db)
        password_hasher = BCryptPasswordHasher()
        token_service = JWTTokenService()
        
        login_use_case = LoginUserUseCase(
            user_repository, 
            password_hasher, 
            token_service, 
            int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        )
        
        login_result = await login_use_case.execute(login_data.email, login_data.password)
        logger.info(f"Login bem-sucedido: {login_data.email}")
        
        return login_result
    
    except InvalidCredentialsError:
        logger.warning(f"Credenciais inválidas: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    username: str = Form(...),
    password: str = Form(...),
    grant_type: str = Form("password", pattern="^password$"),
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
    scope: str = Form(""),
    db: AsyncSession = Depends(get_db)
):
    try:
        logger.info(f"Tentativa de obtenção de token para: {username}")
        
        if grant_type != "password":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O tipo de autenticação deve ser 'password'",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user_repository = SQLAlchemyUserRepository(db)
        password_hasher = BCryptPasswordHasher()
        token_service = JWTTokenService()
        
        login_use_case = LoginUserUseCase(
            user_repository, 
            password_hasher, 
            token_service, 
            int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        )
        
        try:
            login_result = await login_use_case.execute(username, password)
            logger.info(f"Token gerado com sucesso para: {username}")
            return login_result
        except MFARequiredError:
            logger.info(f"MFA requerido para: {username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Autenticação MFA é necessária",
                headers={"X-MFA-Required": "true"}
            )
    
    except InvalidCredentialsError:
        logger.warning(f"Credenciais inválidas para: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro durante login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        logger.info(f"Iniciando configuração MFA: {current_user.id}")
        
        if current_user.mfa_enabled:
            logger.warning(f"MFA já habilitado: {current_user.id}")
            raise MFAAlreadyEnabledError()
        
        mfa_service = PyOTPMFAService(issuer_name="Carteira Digital")
        user_repository = SQLAlchemyUserRepository(db)
        
        setup_use_case = SetupMFAUseCase(user_repository, mfa_service)
        setup_info = await setup_use_case.execute(current_user.id)
        
        logger.info(f"Configuração MFA iniciada: {current_user.id}")
        return setup_info
    
    except MFAAlreadyEnabledError:
        logger.warning(f"MFA já habilitado: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA já está habilitado para este usuário"
        )
    except Exception as e:
        logger.error(f"Erro ao configurar MFA: {str(e)}")
        
        if "greenlet_spawn has not been called" in str(e):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno na configuração do MFA. Por favor, tente novamente."
            )
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao configurar MFA: {str(e)}"
        )


@router.post("/mfa/verify", response_model=MFAVerifyResponse)
async def verify_mfa(
    verify_data: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        logger.info(f"Verificando código MFA: {current_user.id}")
        
        mfa_service = PyOTPMFAService()
        user_repository = SQLAlchemyUserRepository(db)
        
        verify_use_case = VerifyMFAUseCase(user_repository, mfa_service)
        await verify_use_case.execute(current_user.id, verify_data.code)
        
        logger.info(f"MFA verificado com sucesso: {current_user.id}")
        return MFAVerifyResponse(
            verified=True,
            message="MFA habilitado com sucesso"
        )
    
    except MFANotEnabledError:
        logger.warning(f"MFA não configurado: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA não foi configurado para este usuário"
        )
    except InvalidMFACodeError:
        logger.warning(f"Código MFA inválido: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código MFA inválido"
        )
    except Exception as e:
        logger.error(f"Erro ao verificar MFA: {str(e)}")
        
        if "greenlet_spawn has not been called" in str(e):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno na verificação do MFA. Por favor, tente novamente."
            )
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar MFA: {str(e)}"
        )


@router.post("/mfa/disable", response_model=dict)
async def disable_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        logger.info(f"Desabilitando MFA: {current_user.id}")
        
        user_repository = SQLAlchemyUserRepository(db)
        
        disable_use_case = DisableMFAUseCase(user_repository)
        await disable_use_case.execute(current_user.id)
        
        logger.info(f"MFA desabilitado: {current_user.id}")
        return {"message": "MFA desabilitado com sucesso"}
    
    except MFANotEnabledError:
        logger.warning(f"MFA não habilitado: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA não está habilitado para este usuário"
        )
    except Exception as e:
        logger.error(f"Erro ao desabilitar MFA: {str(e)}")
        
        if "greenlet_spawn has not been called" in str(e):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao desabilitar MFA. Por favor, tente novamente."
            )
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao desabilitar MFA: {str(e)}"
        )


@router.post("/mfa/login", response_model=TokenResponse)
async def login_with_mfa(
    login_data: MFALoginRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        logger.info(f"Tentativa de login MFA: {login_data.email}")
        
        user_repository = SQLAlchemyUserRepository(db)
        password_hasher = BCryptPasswordHasher()
        token_service = JWTTokenService()
        mfa_service = PyOTPMFAService()
        
        login_mfa_use_case = LoginWithMFAUseCase(
            user_repository,
            password_hasher,
            token_service,
            mfa_service,
            int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        )
        
        login_result = await login_mfa_use_case.execute(
            login_data.email, 
            login_data.password, 
            login_data.mfa_code
        )
        
        logger.info(f"Login MFA bem-sucedido: {login_data.email}")
        return login_result
    
    except InvalidCredentialsError:
        logger.warning(f"Credenciais inválidas: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )
    except MFANotEnabledError as e:
        logger.warning(f"MFA não habilitado: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidMFACodeError:
        logger.warning(f"Código MFA inválido: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código MFA inválido"
        )
    except Exception as e:
        logger.error(f"Erro ao realizar login MFA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao realizar login MFA: {str(e)}"
        )


@router.post("/check-mfa", response_model=dict)
async def check_mfa_status(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    try:
        logger.info(f"Verificando status MFA: {login_data.email}")
        
        user_repository = SQLAlchemyUserRepository(db)
        password_hasher = BCryptPasswordHasher()
        
        first_step_use_case = LoginFirstStepUseCase(user_repository, password_hasher)
        
        try:
            user_id = await first_step_use_case.execute(login_data.email, login_data.password)
            logger.info(f"MFA habilitado: {login_data.email}")
            return {
                "mfa_required": True,
                "user_id": str(user_id)
            }
        except MFARequiredError as mfa_error:
            logger.info(f"MFA requerido: {login_data.email}")
            return {
                "mfa_required": True,
                "user_id": str(mfa_error.user_id)
            }
        except InvalidCredentialsError:
            logger.warning(f"Credenciais inválidas: {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas"
            )
    
    except Exception as e:
        logger.error(f"Erro ao verificar status MFA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar status MFA: {str(e)}"
        )
