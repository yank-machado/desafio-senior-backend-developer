import os
import logging
import logging.handlers
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from infrastucture.api.routers import auth, documents, transport, chatbot, health, oauth
from infrastucture.database.session import get_db
from infrastucture.database.init_enum import initialize_enums

def setup_logging():
    os.makedirs("logs", exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    
    file_handler = logging.handlers.RotatingFileHandler(
        filename='logs/api.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]'
    )
    file_handler.setFormatter(file_format)
    
    error_file_handler = logging.handlers.RotatingFileHandler(
        filename='logs/error.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(file_format)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_file_handler)
    
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    logger.info("=== Iniciando servidor da API Carteira Digital ===")

setup_logging()
logger = logging.getLogger(__name__)

load_dotenv()

api_v1_prefix = os.getenv("API_V1_STR", "/api/v1")
if not api_v1_prefix.startswith("/"):
    api_v1_prefix = f"/{api_v1_prefix}"
    logger.warning(f"API_V1_STR não começava com '/'. Valor corrigido para: {api_v1_prefix}")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{api_v1_prefix}/auth/token")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Aplicação iniciada com sucesso")
    
    db_host = os.getenv("DB_HOST", "não definido")
    db_port = os.getenv("DB_PORT", "não definido")
    db_name = os.getenv("DB_NAME", "não definido")
    
    db_connection = f"{db_host}:{db_port}/{db_name}"
    logger.info(f"Banco de dados configurado: {db_connection}")
    logger.info(f"Modo de depuração: {os.getenv('DEBUG', 'False')}")
    
    try:
        logger.info("Inicializando enums no banco de dados...")
        async for db_session in get_db():
            await initialize_enums(db_session)
            break
        logger.info("Enums inicializados com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar enums: {str(e)}")
    
    yield
    
    logger.info("Aplicação finalizada")

app = FastAPI(
    title="Carteira Digital API",
    description="API para gerenciamento de carteira digital com documentos e transporte",
    version="0.1.0",
    swagger_ui_parameters={
        "persistAuthorization": True,
        "oauth2RedirectUrl": "{{base_url}}/docs/oauth2-redirect",
        "displayRequestDuration": True,
        "docExpansion": "none",
        "defaultModelsExpandDepth": 0
    },
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": False,
        "useBasicAuthenticationWithAccessCodeGrant": True,
        "clientId": ""
    },
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": f"{api_v1_prefix}/auth/token",
                    "scopes": {}
                }
            }
        }
    }
    
    openapi_schema["tags"] = [
        {"name": "auth", "description": "Operações de autenticação"},
        {"name": "oauth", "description": "Autenticação via provedores sociais (Google, Facebook)"},
        {"name": "documents", "description": "Gerenciamento de documentos"},
        {"name": "transport", "description": "Operações relacionadas a cartão de transporte"},
        {"name": "chatbot", "description": "Interação com o chatbot"},
        {"name": "health", "description": "Verificação de saúde da API"}
    ]
    
    openapi_schema["security"] = [{"OAuth2PasswordBearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

logger.info(f"Configurando routers com prefixo: {api_v1_prefix}")
app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(oauth.router, prefix=api_v1_prefix)
app.include_router(documents.router, prefix=api_v1_prefix)
app.include_router(transport.router, prefix=api_v1_prefix)
app.include_router(chatbot.router, prefix=api_v1_prefix)
app.include_router(health.router, prefix=api_v1_prefix)

app.mount("/static", StaticFiles(directory="infrastucture/api/static"), name="static")

@app.get("/")
async def root():
    logger.debug("Requisição à rota raiz '/'")
    return {
        "message": "Bem-vindo à API de Carteira Digital",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/login-social")
async def login_social_example():
    return RedirectResponse(url="/static/login_exemplo.html")

@app.get("/routes")
async def list_routes():
    logger.debug("Requisição à rota '/routes'")
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": route.methods if hasattr(route, "methods") else []
        })
    return routes