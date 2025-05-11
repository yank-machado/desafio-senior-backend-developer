import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from infrastucture.database.base import Base, DATABASE_URL
from infrastucture.database.models import UserModel, DocumentModel, TransportCardModel

logger = logging.getLogger(__name__)

async def init_db():
    try:
        logger.info("Inicializando o banco de dados")
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        # Criar todas as tabelas
        async with engine.begin() as conn:
            logger.info("Criando tabelas no banco de dados")
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Tabelas criadas com sucesso")
        
        # Criar uma sessão para operações
        async_session = sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Verificar se há usuários e criar um admin se necessário
        async with async_session() as session:
            from sqlalchemy import select
            from core.entities.user import User
            from infrastucture.security.password import BCryptPasswordHasher
            from infrastucture.repositories.user_repository import SQLAlchemyUserRepository
            
            # Verificar se já existe algum usuário
            result = await session.execute(select(UserModel))
            admin_exists = result.scalar_one_or_none() is not None
            
            if not admin_exists:
                logger.info("Criando usuário administrador")
                # Criar um hasher de senha
                password_hasher = BCryptPasswordHasher()
                admin_password = "admin123"  # Senha provisória
                hashed_password = password_hasher.hash_password(admin_password)
                
                # Criar entidade de usuário admin
                admin_user = User(
                    email="admin@carteira.com",
                    hashed_password=hashed_password,
                    is_active=True,
                    is_admin=True
                )
                
                # Criar repositório e persistir usuário
                user_repo = SQLAlchemyUserRepository(session)
                created_user = await user_repo.create(admin_user)
                await session.commit()
                
                logger.info(f"Usuário administrador criado com sucesso: ID={created_user.id}")
            else:
                logger.info("Banco de dados já possui usuários, pulando criação de admin")
                
        logger.info("Inicialização do banco de dados concluída")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao inicializar o banco de dados: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    # Configuração de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Executar inicialização
    asyncio.run(init_db()) 