from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import orm
import os
from dotenv import load_dotenv
import logging

# Configurar logger
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco de dados - Valores fixos para ambiente de desenvolvimento
DB_USER = "carteira"
DB_PASSWORD = "carteira123"
# Em ambiente de contêiner Docker, usar "db" como host
# Em ambiente de desenvolvimento local, usar "localhost"
DB_HOST = os.getenv("DB_HOST", "db")
if os.getenv("TESTING", "False").lower() == "true":
    DB_HOST = "localhost"  # Forçar localhost para testes
DB_PORT = "5432"
DB_NAME = "carteira_db"

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

logger.info(f"Conectando ao banco de dados em: {DB_HOST}:{DB_PORT}")

engine = create_async_engine(DATABASE_URL, echo=True if os.getenv('DEBUG', 'False').lower() == 'true' else False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = orm.declarative_base()