from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os
import logging
import httpx
from typing import Optional
from uuid import uuid4
from dotenv import load_dotenv
from urllib.parse import urlencode
import json

from infrastucture.database.session import get_db
from infrastucture.repositories.user_repository import SQLAlchemyUserRepository
from infrastucture.security.token import JWTTokenService
from core.use_cases.user_use_cases import RegisterUserUseCase
from infrastucture.security.password import BCryptPasswordHasher
from core.entities.user import AuthProvider
from infrastucture.api.dtos.user_dtos import OAuthUserInfo

logger = logging.getLogger(__name__)

load_dotenv()

router = APIRouter(prefix="/oauth", tags=["oauth"])

DEV_MODE = os.getenv("DEBUG", "False").lower() == "true"

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")

FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID", "")
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET", "")
FACEBOOK_REDIRECT_URI = os.getenv("FACEBOOK_REDIRECT_URI", "")

@router.get("/status")
async def check_oauth_status():
    google_status = {
        "configured": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI),
        "client_id": GOOGLE_CLIENT_ID[:10] + "..." if GOOGLE_CLIENT_ID else None,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "dev_mode": DEV_MODE
    }
    
    facebook_status = {
        "configured": bool(FACEBOOK_CLIENT_ID and FACEBOOK_CLIENT_SECRET and FACEBOOK_REDIRECT_URI),
        "client_id": FACEBOOK_CLIENT_ID[:10] + "..." if FACEBOOK_CLIENT_ID else None,
        "redirect_uri": FACEBOOK_REDIRECT_URI,
        "dev_mode": DEV_MODE
    }
    
    return {
        "google": google_status,
        "facebook": facebook_status
    }

@router.get("/demo-login")
async def demo_login(
    provider: str = "google",
    db: AsyncSession = Depends(get_db)
):
    if not DEV_MODE:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Rota de demonstração disponível apenas em modo de desenvolvimento"}
        )

    try:
        email = "usuario.teste@exemplo.com"
        picture = "https://ui-avatars.com/api/?name=Usuario+Teste&background=random"
        
        oauth_provider = AuthProvider.GOOGLE if provider.lower() == "google" else AuthProvider.FACEBOOK
        oauth_user_info = OAuthUserInfo(
            email=email,
            profile_picture=picture,
            provider=oauth_provider
        )
        
        return await process_oauth_user(oauth_user_info, db)
    
    except Exception as e:
        logger.error(f"Erro ao processar login demo: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Erro no servidor: {str(e)}"}
        )

async def process_oauth_user(
    oauth_user_info: OAuthUserInfo,
    db: AsyncSession
):
    try:
        user_repository = SQLAlchemyUserRepository(db)
        password_hasher = BCryptPasswordHasher()
        token_service = JWTTokenService()
        
        user = await user_repository.get_by_email(oauth_user_info.email)
        
        if not user:
            logger.info(f"Registrando novo usuário OAuth: {oauth_user_info.email}")
            
            random_password = str(uuid4())
            
            register_use_case = RegisterUserUseCase(user_repository, password_hasher)
            user = await register_use_case.execute(oauth_user_info.email, random_password)
            
            user.auth_provider = oauth_user_info.provider
            user.profile_picture = oauth_user_info.profile_picture
            await user_repository.update(user)
        else:
            if user.auth_provider != oauth_user_info.provider:
                logger.info(f"Atualizando provider: {oauth_user_info.email}")
                user.auth_provider = oauth_user_info.provider
                await user_repository.update(user)
            
            if oauth_user_info.profile_picture and user.profile_picture != oauth_user_info.profile_picture:
                logger.info(f"Atualizando foto de perfil: {oauth_user_info.email}")
                user.profile_picture = oauth_user_info.profile_picture
                await user_repository.update(user)
        
        token_data = {
            "sub": str(user.id),
            "email": user.email
        }
        
        access_token = token_service.create_access_token(
            data=token_data,
            expires_delta=None
        )
        
        logger.info(f"Login OAuth bem-sucedido: {oauth_user_info.email}")
        
        return JSONResponse(content={
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": str(user.id),
            "email": user.email,
            "provider": oauth_user_info.provider.value
        })
    
    except Exception as e:
        logger.error(f"Erro ao processar usuário OAuth: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Erro no servidor: {str(e)}"}
        )

@router.get("/google/login")
async def login_google():
    if DEV_MODE and (not GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID == "seu_google_client_id"):
        logger.warning("Usando modo de desenvolvimento sem credenciais Google")
        return RedirectResponse(url="/api/v1/oauth/demo-login?provider=google")
    
    if not GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID == "seu_google_client_id":
        logger.error(f"Google Client ID não configurado")
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content={"detail": "Autenticação Google não configurada. Configure GOOGLE_CLIENT_ID no arquivo .env"}
        )
    
    if not GOOGLE_REDIRECT_URI:
        logger.error("URI de redirecionamento Google não configurada")
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content={"detail": "URI de redirecionamento do Google não configurada. Configure GOOGLE_REDIRECT_URI no arquivo .env"}
        )
    
    state = str(uuid4())
    
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "state": state,
        "prompt": "select_account"
    }
    
    redirect_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
    logger.info(f"Redirecionando para autenticação Google")
    
    return RedirectResponse(url=redirect_url)

@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    if DEV_MODE and (not GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID == "seu_google_client_id"):
        logger.warning("Callback Google em modo de desenvolvimento sem credenciais")
        return RedirectResponse(url="/api/v1/oauth/demo-login?provider=google")
    
    if error:
        logger.error(f"Erro no callback Google: {error}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": f"Erro de autenticação: {error}"}
        )
    
    if not code:
        logger.error("Código de autorização Google ausente")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Código de autorização ausente"}
        )
    
    try:
        # Troca do código de autorização por token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            token_info = token_response.json()
        
        # Obter informações do usuário
        id_token = token_info.get("id_token")
        if not id_token:
            logger.error("Token de ID ausente na resposta do Google")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token de ID ausente")
        
        # Decodificar o token JWT
        parts = id_token.split(".")
        if len(parts) != 3:
            logger.error("Formato de token JWT inválido")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de token inválido")
        
        payload = parts[1]
        # Adicionar padding se necessário
        payload += "=" * ((4 - len(payload) % 4) % 4)
        import base64
        decoded_payload = base64.b64decode(payload.replace("-", "+").replace("_", "/"))
        user_info = json.loads(decoded_payload)
        
        # Extrair informações relevantes
        email = user_info.get("email")
        if not email:
            logger.error("Email não encontrado no token do Google")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email não encontrado")
        
        picture = user_info.get("picture", "")
        
        oauth_user_info = OAuthUserInfo(
            email=email,
            profile_picture=picture,
            provider=AuthProvider.GOOGLE
        )
        
        # Processar usuário e gerar token
        logger.info(f"Processando usuário Google: {email}")
        return await process_oauth_user(oauth_user_info, db)
    
    except Exception as e:
        logger.error(f"Erro ao processar callback Google: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Erro no servidor: {str(e)}"}
        )

@router.get("/facebook/login")
async def login_facebook():
    if DEV_MODE and (not FACEBOOK_CLIENT_ID or FACEBOOK_CLIENT_ID == "seu_facebook_client_id"):
        logger.warning("Usando modo de desenvolvimento sem credenciais Facebook")
        return RedirectResponse(url="/api/v1/oauth/demo-login?provider=facebook")
    
    if not FACEBOOK_CLIENT_ID or FACEBOOK_CLIENT_ID == "seu_facebook_client_id":
        logger.error("Facebook Client ID não configurado")
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content={"detail": "Autenticação Facebook não configurada. Configure FACEBOOK_CLIENT_ID no arquivo .env"}
        )
    
    if not FACEBOOK_REDIRECT_URI:
        logger.error("URI de redirecionamento Facebook não configurada")
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content={"detail": "URI de redirecionamento do Facebook não configurada. Configure FACEBOOK_REDIRECT_URI no arquivo .env"}
        )
    
    state = str(uuid4())
    
    params = {
        "client_id": FACEBOOK_CLIENT_ID,
        "redirect_uri": FACEBOOK_REDIRECT_URI,
        "state": state,
        "scope": "email",
        "response_type": "code"
    }
    
    redirect_url = f"https://www.facebook.com/v14.0/dialog/oauth?{urlencode(params)}"
    logger.info("Redirecionando para autenticação Facebook")
    
    return RedirectResponse(url=redirect_url)

@router.get("/facebook/callback")
async def facebook_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    if DEV_MODE and (not FACEBOOK_CLIENT_ID or FACEBOOK_CLIENT_ID == "seu_facebook_client_id"):
        logger.warning("Callback Facebook em modo de desenvolvimento sem credenciais")
        return RedirectResponse(url="/api/v1/oauth/demo-login?provider=facebook")
    
    if error:
        logger.error(f"Erro no callback Facebook: {error}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": f"Erro de autenticação: {error}"}
        )
    
    if not code:
        logger.error("Código de autorização Facebook ausente")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Código de autorização ausente"}
        )
    
    try:
        # Troca do código de autorização por token
        token_url = "https://graph.facebook.com/v14.0/oauth/access_token"
        token_params = {
            "client_id": FACEBOOK_CLIENT_ID,
            "client_secret": FACEBOOK_CLIENT_SECRET,
            "redirect_uri": FACEBOOK_REDIRECT_URI,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.get(token_url, params=token_params)
            token_response.raise_for_status()
            token_info = token_response.json()
        
        access_token = token_info.get("access_token")
        if not access_token:
            logger.error("Token de acesso ausente na resposta do Facebook")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token de acesso ausente")
        
        # Obter informações do usuário
        user_info_url = "https://graph.facebook.com/v14.0/me"
        user_params = {
            "fields": "id,email,picture",
            "access_token": access_token
        }
        
        async with httpx.AsyncClient() as client:
            user_response = await client.get(user_info_url, params=user_params)
            user_response.raise_for_status()
            user_info = user_response.json()
        
        email = user_info.get("email")
        if not email:
            logger.error("Email não encontrado na resposta do Facebook")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email não fornecido")
        
        picture = user_info.get("picture", {}).get("data", {}).get("url", "")
        
        oauth_user_info = OAuthUserInfo(
            email=email,
            profile_picture=picture,
            provider=AuthProvider.FACEBOOK
        )
        
        logger.info(f"Processando usuário Facebook: {email}")
        return await process_oauth_user(oauth_user_info, db)
    
    except Exception as e:
        logger.error(f"Erro ao processar callback Facebook: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Erro no servidor: {str(e)}"}
        ) 