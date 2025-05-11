from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
import os
from uuid import UUID
from dotenv import load_dotenv

from infrastucture.database.session import get_db
from infrastucture.repositories.user_repository import SQLAlchemyUserRepository
from core.use_cases.user_use_cases import GetUserUseCase
from core.exceptions.user_exceptions import UserNotFoundError

load_dotenv()

# Configurando o OAuth2 com tokenUrl relativo ao prefixo da API
api_v1_prefix = os.getenv("API_V1_STR", "/api/v1")
if not api_v1_prefix.startswith("/"):
    api_v1_prefix = f"/{api_v1_prefix}"

# Esquema OAuth2 para autenticação via senha (sem client credentials)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{api_v1_prefix}/auth/token",
    auto_error=True
)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """
    Dependência para obter o usuário atual a partir do token JWT.
    Não requer client_id ou client_secret, apenas o token de acesso.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            os.getenv("SECRET_KEY"), 
            algorithms=[os.getenv("ALGORITHM", "HS256")]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_repository = SQLAlchemyUserRepository(db)
    get_user_use_case = GetUserUseCase(user_repository)
    
    try:
        user = await get_user_use_case.execute(UUID(user_id))
        if not user.is_active:
            raise credentials_exception
        return user
    except (UserNotFoundError, ValueError):
        raise credentials_exception